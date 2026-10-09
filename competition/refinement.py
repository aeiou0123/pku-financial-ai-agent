"""Bounded second-round development; previously inspected 2020 is not pristine."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import platform
from pathlib import Path
from time import perf_counter

import numpy as np

from competition import baseline as b

FOLDS = (
    {"id": "A", "train_end": "2015-12-31", "start": "2016-01-01", "end": "2017-12-31"},
    {"id": "B", "train_end": "2017-12-31", "start": "2018-01-01", "end": "2019-12-31"},
)
WINDOWS = (2, 5)
FEATURES = ("linear", "quadratic")
POLICIES = ("fixed_4bp", "fixed_8bp", "daily_2std")
ALPHA = 0.1


def write_new(path, data):
    with Path(path).open("x", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def features(frame, kind):
    x, ordered = b.daily_features(frame)
    if kind == "linear":
        return x, ordered
    if kind != "quadratic":
        raise ValueError("Unknown feature map")
    # Fixed same-day quadratic map; each column is demeaned within this day.
    # Scaling is the analytic SD of squared Uniform(-sqrt(3), sqrt(3)).
    quadratic = x * x
    quadratic = (quadratic - quadratic.mean(axis=0)) / np.sqrt(0.8)
    return np.concatenate((x, quadratic), axis=1), ordered


def fit(days, kind):
    dim = 100 if kind == "linear" else 200
    gram, rhs = np.zeros((dim, dim)), np.zeros(dim)
    n = 0
    first = last = None
    for frame in days:
        x, ordered = features(frame, kind)
        date = str(ordered.date.iloc[0])[:10]
        if last is not None and date <= last:
            raise ValueError("Training days must increase")
        y = ordered["return"].to_numpy(dtype=float)
        if not np.isfinite(y).all() or (y <= -1).any():
            raise ValueError("Invalid public training returns")
        gram += x.T @ x
        rhs += x.T @ (y - y.mean())
        n += len(y)
        first, last = first or date, date
    if n == 0:
        raise ValueError("Empty training interval")
    return {"format": "recent_rank_ridge_v1", "kind": kind, "alpha": ALPHA,
            "coef": np.linalg.solve(gram / n + ALPHA * np.eye(dim), rhs / n).tolist(),
            "training_start": first, "trained_through": last, "training_rows": n,
            "features": b.FACTORS, "training_file_sha256": b.DATA_SHA["train"],
            "tools_sha256": b.TOOLS_SHA}


def scores(model, days):
    if model.get("format") != "recent_rank_ridge_v1" or model.get("features") != b.FACTORS:
        raise ValueError("Unknown model format")
    coef = np.asarray(model["coef"], dtype=float)
    dim = 100 if model["kind"] == "linear" else 200
    if coef.shape != (dim,) or not np.isfinite(coef).all():
        raise ValueError("Invalid model coefficients")
    last = model["trained_through"]
    for frame in days:
        x, ordered = features(frame, model["kind"])
        date = str(ordered.date.iloc[0])[:10]
        if date <= last:
            raise ValueError("Prediction must follow the training/history cutoff")
        yield date, x @ coef
        last = date


def holdings(scored_days, policy):
    if policy not in POLICIES:
        raise ValueError("Unknown holdings policy")
    previous = ()
    for date, score in scored_days:
        # Current-day scores alone determine scale; no fitted test statistics.
        bonus = {"fixed_4bp": 0.0004, "fixed_8bp": 0.0008}.get(policy)
        if bonus is None:
            bonus = 2 * float(np.std(score))
        chosen = b.select_twenty(score, previous, bonus)
        yield date, chosen
        previous = chosen


def candidate_key(c):
    s = c["fold_sharpes"]
    if len(s) != 2 or not np.isfinite(s).all():
        raise ValueError("Both folds must be scorable")
    return min(s), sum(s) / 2


def develop(train, tools_path, out):
    started = perf_counter()
    tools = b.official_tools(tools_path)
    b.verify_data(train, "train", tools)
    out.mkdir(parents=True, exist_ok=False)
    plan = {"format": "bounded_refinement_v1", "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "windows_years": list(WINDOWS), "feature_maps": list(FEATURES),
            "policies": list(POLICIES), "alpha": ALPHA, "folds": list(FOLDS),
            "candidate_count": 12, "selection_rule": "max minimum fold net Sharpe, then mean; deterministic candidate order breaks ties",
            "promotion_rule": "only if minimum fold net Sharpe strictly exceeds immutable incumbent",
            "incumbent": {"alpha": 0.00001, "hold_bonus": 0.0008,
                          "fold_sharpes": [-0.10166514307510185, 0.7885331846721062]},
            "2020_previously_inspected": True, "2020_access_this_run": False,
            "test_access_this_run": False, "independent_holdout_available": False,
            "selection_metrics_are_development_results": True,
            "data_sha256": b.DATA_SHA, "tools_sha256": b.TOOLS_SHA,
            "code_sha256": {"competition/refinement.py": b.sha256(__file__),
                            "competition/baseline.py": b.sha256(Path(__file__).with_name("baseline.py"))},
            "environment": {"python": platform.python_version(), "numpy": np.__version__}}
    write_new(out / "plan.json", plan)
    candidates = []
    for years in WINDOWS:
        for kind in FEATURES:
            models, scored = [], []
            for fold in FOLDS:
                directory = out / f"{fold['id']}_{years}y_{kind}"
                directory.mkdir()
                train_start = f"{int(fold['train_end'][:4]) - years + 1}-01-01"
                model = fit(b.read_days(train, tools, train_start, fold["train_end"], labels=True), kind)
                write_new(directory / "model.json", model)
                models.append(model)
                # Only development scores are cached; test data is never accepted here.
                scored.append(list(scores(model, b.read_days(train, tools, fold["start"], fold["end"]))))
            for policy in POLICIES:
                result = {"years": years, "kind": kind, "policy": policy, "fold_sharpes": []}
                for fold, values in zip(FOLDS, scored):
                    directory = out / f"{fold['id']}_{years}y_{kind}" / policy
                    directory.mkdir()
                    rows = b.write_holdings(directory / "validation.csv", holdings(values, policy))
                    account = tools.backtest(directory / "validation.csv", train, fold["start"], fold["end"])
                    if account["status"] != "OK":
                        raise ValueError("Official accounting did not succeed")
                    write_new(directory / "accounting.json", account)
                    write_new(directory / "receipt.json", {"plan_sha256": b.sha256(out / "plan.json"),
                        "holding_rows": rows, "sharpe": account["sharpe"],
                        "files_sha256": {n: b.sha256(directory / n) for n in ("validation.csv", "accounting.json")}})
                    result["fold_sharpes"].append(account["sharpe"])
                candidate_key(result)
                candidates.append(result)
                print(json.dumps({"completed": len(candidates), **result}), flush=True)
    selected = max(candidates, key=candidate_key)
    summary = {"status": "COMPLETE", "plan_sha256": b.sha256(out / "plan.json"),
               "candidates": candidates, "selected": selected,
               "promote": min(selected["fold_sharpes"]) > min(plan["incumbent"]["fold_sharpes"]),
               "elapsed_seconds": perf_counter() - started, "test_sharpe": None,
               "note": "Development comparison only. 2020 was inspected in the first round; no new pristine holdout exists.",
               "artifact_receipts_sha256": {str(p.relative_to(out)): b.sha256(p) for p in sorted(out.glob("*/*/receipt.json"))},
               "model_files_sha256": {str(p.relative_to(out)): b.sha256(p) for p in sorted(out.glob("*/model.json"))}}
    write_new(out / "selection_lock.json", summary)
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--train", required=True, type=Path)
    p.add_argument("--tools", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    a = p.parse_args()
    print(json.dumps(develop(a.train, a.tools, a.out), indent=2))


if __name__ == "__main__":
    main()
