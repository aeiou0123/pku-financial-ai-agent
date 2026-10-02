"""Daily cross-sectional rank ridge baseline with strictly dated training."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import importlib.util
import json
import platform
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

FACTORS = [f"factor_{i}" for i in range(1, 101)]
STOCKS = tuple(f"C{i:04d}" for i in range(1, 401))
TOOLS_SHA = "50ce8aedf54029b2ddb1f3afb703c8a25c8364d424ccf9ea9f641175bc55a07e"
DATA_SHA = {
    "train": "482d4c0387e9da2facd77f722fa465b2d69ec7f119d96933c57761790f4d9519",
    "test": "015ce29eade2ddd199e23b68bb4c829b004750e2d02e13f1b4a2550024887171",
}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iso_date(value):
    parsed = dt.date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("Dates must use YYYY-MM-DD")
    return value


def official_tools(path):
    if sha256(path) != TOOLS_SHA:
        raise ValueError("tools.py SHA-256 differs from the supplied official v1.2.1 file")
    spec = importlib.util.spec_from_file_location("fel_official_tools", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_data(path, split, tools):
    _, actual = tools.validate_data(path)
    if actual.decode() != split or sha256(path) != DATA_SHA[split]:
        raise ValueError("Official data split or SHA-256 mismatch")


def daily_features(frame):
    """Only the current day's available 400-stock cross-section is transformed."""
    frame = frame.sort_values("stock_id")
    if len(frame) != 400 or tuple(frame.stock_id) != STOCKS:
        raise ValueError("Each day must have all 400 unique stocks")
    if frame.date.nunique() != 1 or frame.asof_date.nunique() != 1:
        raise ValueError("Expected one date and one asof_date per cross-section")
    if pd.Timestamp(frame.asof_date.iloc[0]) >= pd.Timestamp(frame.date.iloc[0]):
        raise ValueError("Factors must be available before their same-row return")
    values = frame[FACTORS]
    if not np.isfinite(values.to_numpy()).all():
        raise ValueError("Factors contain nonfinite values")
    # Midranks handle ties. Fixed transform has no fitted global/test statistics.
    x = ((values.rank(axis=0, method="average").to_numpy() - .5) / 400 - .5) * np.sqrt(12)
    return x, frame


def fit_days(days, alpha):
    if not np.isfinite(alpha) or alpha <= 0:
        raise ValueError("alpha must be positive and finite")
    gram = np.zeros((100, 100))
    rhs = np.zeros(100)
    n = 0
    first = last = None
    for frame in days:
        x, ordered = daily_features(frame)
        date = str(ordered.date.iloc[0])[:10]
        if last is not None and date <= last:
            raise ValueError("Training days must be strictly increasing")
        y = ordered["return"].to_numpy(dtype=float)
        if not np.isfinite(y).all() or (y <= -1).any():
            raise ValueError("Invalid training return")
        # Predict relative returns; the market component cannot affect top-20 ranking.
        y = y - y.mean()
        gram += x.T @ x
        rhs += x.T @ y
        n += 400
        first = first or date
        last = date
    if not n:
        raise ValueError("Empty training interval")
    coef = np.linalg.solve(gram / n + alpha * np.eye(100), rhs / n)
    return {"format": "rank_ridge_v1", "alpha": float(alpha), "coef": coef.tolist(),
            "training_start": first, "trained_through": last, "training_rows": n,
            "seed": 0, "label": "same_row_return_demeaned_within_day",
            "features": FACTORS, "preprocessing": "current_day_cross_section_midranks_only"}


def select_twenty(scores, previous=(), hold_bonus=0.0):
    scores = np.asarray(scores, dtype=float)
    if scores.shape != (400,) or not np.isfinite(scores).all():
        raise ValueError("Expected 400 finite scores")
    if not np.isfinite(hold_bonus) or hold_bonus < 0:
        raise ValueError("hold_bonus must be nonnegative and finite")
    if len(set(previous)) != len(previous) or any(s not in STOCKS for s in previous):
        raise ValueError("Invalid previous holdings")
    adjusted = scores.copy()
    for stock in previous:
        adjusted[int(stock[1:]) - 1] += hold_bonus
    # Deterministic tie breaks; no realized validation/test returns in selection.
    indices = np.lexsort((np.arange(400), -adjusted))[:20]
    return tuple(STOCKS[i] for i in sorted(indices))


def predict_days(model, days, hold_bonus=0.0):
    if model.get("format") != "rank_ridge_v1" or model.get("features") != FACTORS:
        raise ValueError("Unknown model format or factor order")
    coef = np.asarray(model["coef"], dtype=float)
    if coef.shape != (100,) or not np.isfinite(coef).all():
        raise ValueError("Invalid coefficients")
    previous = ()
    last = model["trained_through"]
    for frame in days:
        x, ordered = daily_features(frame)
        date = str(ordered.date.iloc[0])[:10]
        if date <= last:
            raise ValueError("Prediction date must be strictly after training/history cutoff")
        chosen = select_twenty(x @ coef, previous, hold_bonus)
        yield date, chosen
        previous, last = chosen, date


def read_days(path, tools, start=None, end=None, labels=False):
    """Read bounded monthly batches; never fit on the test period."""
    calendar = tools.read_data(path, columns=["date"])
    dates = sorted(pd.Timestamp(d) for d in calendar.date.unique())
    dates = [d for d in dates if (start is None or d >= pd.Timestamp(start)) and
             (end is None or d <= pd.Timestamp(end))]
    if not dates:
        raise ValueError("No dates in selected interval")
    columns = ["date", "asof_date", "stock_id"] + FACTORS + (["return"] if labels else [])
    months = sorted({d.to_period("M") for d in dates})
    for month in months:
        lo = max(month.start_time, dates[0]).date().isoformat()
        hi = min(month.end_time, dates[-1]).date().isoformat()
        frame = tools.read_data(path, start=lo, end=hi, columns=columns)
        for _, group in frame.groupby("date", sort=True):
            yield group


def write_holdings(path, selections):
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "stock_id"])
        count = 0
        for date, chosen in selections:
            for stock in chosen:
                writer.writerow([date, stock])
                count += 1
    if not count:
        raise ValueError("No predictions written")
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["validate", "fit", "predict"])
    parser.add_argument("--tools", type=Path, required=True)
    parser.add_argument("--train", type=Path)
    parser.add_argument("--test", type=Path)
    parser.add_argument("--train-start", default="2000-01-01")
    parser.add_argument("--train-end", default="2015-12-31")
    parser.add_argument("--valid-start", default="2016-01-01")
    parser.add_argument("--valid-end", default="2017-12-31")
    parser.add_argument("--alpha", type=float, default=.001)
    parser.add_argument("--hold-bonus", type=float, default=0.)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="New output directory; existing directories are refused")
    args = parser.parse_args()
    for value in (args.train_start, args.train_end, args.valid_start, args.valid_end):
        iso_date(value)
    if not np.isfinite(args.hold_bonus) or args.hold_bonus < 0:
        parser.error("--hold-bonus must be nonnegative and finite")
    started = perf_counter()
    tools = official_tools(args.tools)
    if args.command in {"fit", "validate"}:
        if not args.train:
            parser.error("--train required")
        if args.train_start > args.train_end or args.train_end > "2020-12-31":
            parser.error("Training interval must be ordered and end by 2020-12-31")
        if args.command == "validate" and not args.train_end < args.valid_start <= args.valid_end <= "2020-12-31":
            parser.error("Validation must follow training and remain within public training data")
        verify_data(args.train, "train", tools)
        model = fit_days(read_days(args.train, tools, args.train_start, args.train_end, labels=True), args.alpha)
        model.update({"training_file_sha256": DATA_SHA["train"], "tools_sha256": TOOLS_SHA})
    else:
        if not args.test or not args.model:
            parser.error("--test and --model required")
        verify_data(args.test, "test", tools)
        model = json.loads(args.model.read_text(encoding="utf-8"))
        if model.get("training_file_sha256") != DATA_SHA["train"] or model.get("tools_sha256") != TOOLS_SHA:
            raise ValueError("Model provenance mismatch")
        if not model["trained_through"] <= "2020-12-31":
            raise ValueError("Model trained after public training cutoff")
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "model.json").write_text(json.dumps(model, indent=2, allow_nan=False), encoding="utf-8")
    summary = {"command": args.command, "python": platform.python_version(),
               "numpy": np.__version__, "pandas": pd.__version__,
               "tools_sha256": TOOLS_SHA, "model_sha256": sha256(args.out / "model.json"),
               "train_end": model["trained_through"], "alpha": model["alpha"],
               "hold_bonus": args.hold_bonus, "test_return_access": False,
               "selection_score": "predicted_relative_return_plus_incumbent_bonus",
               "status": "COMPLETE"}
    if args.command != "fit":
        is_validation = args.command == "validate"
        data = args.train if is_validation else args.test
        selections = predict_days(model, read_days(data, tools,
            args.valid_start if is_validation else None, args.valid_end if is_validation else None), args.hold_bonus)
        output = args.out / ("validation.csv" if is_validation else "submission.csv")
        summary["holding_rows"] = write_holdings(output, selections)
        summary["holdings_sha256"] = sha256(output)
        if is_validation:
            accounting = tools.backtest(output, args.train, args.valid_start, args.valid_end)
            (args.out / "accounting.json").write_text(json.dumps(accounting, indent=2, allow_nan=False), encoding="utf-8")
            summary["validation"] = {k: accounting[k] for k in ("status", "sharpe", "final_nav")}
            summary["validation_interval"] = [args.valid_start, args.valid_end]
            calendar = tools.read_data(args.train, start=args.valid_start, end=args.valid_end, columns=["date"])
            fixed_path = args.out / "fixed20_validation.csv"
            write_holdings(fixed_path, ((str(d)[:10], STOCKS[:20]) for d in sorted(calendar.date.unique())))
            fixed_account = tools.backtest(fixed_path, args.train, args.valid_start, args.valid_end)
            summary["fixed20_validation"] = {k: fixed_account[k] for k in ("status", "sharpe", "final_nav")}
        else:
            summary["submission_check"] = tools.check(output, args.test)
            summary["test_sharpe"] = None
    summary["elapsed_seconds"] = round(perf_counter() - started, 3)
    (args.out / "run_summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
