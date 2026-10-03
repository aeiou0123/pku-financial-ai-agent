"""Frozen chronological development, single holdout, and checked final delivery."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import platform
import sys
from pathlib import Path
from time import perf_counter

from competition import baseline as b
from competition.package_code import package

ROOT = Path(__file__).resolve().parents[1]
ALPHAS = (0.00001, 0.001, 0.1)
BONUSES = (0.0, 0.0004, 0.0008)
FOLDS = (
    {"id": "A", "train_end": "2015-12-31", "start": "2016-01-01", "end": "2017-12-31"},
    {"id": "B", "train_end": "2017-12-31", "start": "2018-01-01", "end": "2019-12-31"},
)
HOLDOUT = {"id": "2020", "train_end": "2019-12-31", "start": "2020-01-01", "end": "2020-12-31"}
RULE = "maximize minimum fold net Sharpe; then mean; then smaller bonus; then smaller alpha"


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_new(path, data):
    """Exclusive creation: never silently replace evidence or a frozen plan."""
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def code_hashes():
    return {p: b.sha256(ROOT / p) for p in (
        "competition/experiment.py", "competition/baseline.py", "competition/package_code.py",
        "competition/requirements.txt")}


def make_plan():
    import numpy as np
    import pandas as pd
    import pyarrow as pa
    return {"format": "chronological_experiment_v1", "alphas": list(ALPHAS),
            "hold_bonuses": list(BONUSES), "folds": list(FOLDS), "holdout": HOLDOUT,
            "selection_rule": RULE, "data_sha256": b.DATA_SHA, "tools_sha256": b.TOOLS_SHA,
            "code_sha256": code_hashes(), "test_return_access": False,
            "environment": {"python": platform.python_version(), "numpy": np.__version__,
                            "pandas": pd.__version__, "pyarrow": pa.__version__,
                            "platform": platform.platform()}}


def open_plan(out):
    plan = read_json(out / "plan.json")
    if plan != make_plan():
        raise ValueError("Frozen plan/code/environment changed; do not reuse this experiment directory")
    return plan


def receipt(directory, context, files, **fields):
    data = {"context": context, "files_sha256": {f: b.sha256(directory / f) for f in files}, **fields}
    write_new(directory / "receipt.json", data)
    return data


def checked_receipt(directory, context):
    data = read_json(directory / "receipt.json")
    if data.get("context") != context:
        raise ValueError("Artifact context differs from frozen plan")
    for name, expected in data.get("files_sha256", {}).items():
        # Only relative filenames generated here are admissible.
        if Path(name).name != name or b.sha256(directory / name) != expected:
            raise ValueError(f"Evidence changed after completion: {directory.name}/{name}")
    if not data.get("files_sha256"):
        raise ValueError("Artifact receipt has no files")
    return data


def context_for(out, fold, alpha, bonus=None):
    return {"plan_sha256": b.sha256(out / "plan.json"), "fold": fold,
            "alpha": alpha, "hold_bonus": bonus}


def get_model(out, train, tools, fold, alpha, index, resume=False):
    directory = out / "models" / f"{fold['id']}_a{index:02d}"
    context = context_for(out, fold, alpha)
    if directory.exists():
        if not resume:
            raise FileExistsError(directory)
        checked_receipt(directory, context)
        return read_json(directory / "model.json")
    directory.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    model = b.fit_days(b.read_days(train, tools, "2000-01-01", fold["train_end"], labels=True), alpha)
    model.update({"training_file_sha256": b.DATA_SHA["train"], "tools_sha256": b.TOOLS_SHA})
    write_new(directory / "model.json", model)
    receipt(directory, context, ["model.json"], elapsed_seconds=round(perf_counter() - started, 3))
    return model


def turnover_summary(path, accounting):
    import pandas as pd
    frame = pd.read_csv(path, dtype=str)
    previous = None
    replaced = []
    for _, group in frame.groupby("date", sort=True):
        current = set(group.stock_id)
        if previous is not None:
            replaced.append(len(current - previous) / 20)
        previous = current
    return {"mean_constituent_replacement_fraction_excluding_first_day":
            sum(replaced) / len(replaced) if replaced else None,
            "absolute_nav_units_total_fees": sum(float(d["fee"]) for d in accounting["details"]),
            "fee_note": "absolute fee sum uses evolving NAV; it is not a turnover rate"}


def evaluate(out, train, tools, fold, model, alpha, bonus, ai, bi, resume=False, parent="development"):
    directory = out / parent / f"{fold['id']}_a{ai:02d}_b{bi:02d}"
    context = context_for(out, fold, alpha, bonus)
    if directory.exists():
        if not resume:
            raise FileExistsError(directory)
        return checked_receipt(directory, context)
    directory.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    rows = b.write_holdings(directory / "validation.csv", b.predict_days(model,
        b.read_days(train, tools, fold["start"], fold["end"], labels=False), bonus))
    accounting = tools.backtest(directory / "validation.csv", train, fold["start"], fold["end"])
    write_new(directory / "accounting.json", accounting)
    result = {"status": accounting["status"], "sharpe": accounting["sharpe"],
              "final_nav": accounting["final_nav"], "holding_rows": rows,
              "turnover": turnover_summary(directory / "validation.csv", accounting)}
    write_new(directory / "result.json", result)
    return receipt(directory, context, ["validation.csv", "accounting.json", "result.json"],
                   result=result, elapsed_seconds=round(perf_counter() - started, 3))


def fixed_control(out, train, tools, fold, resume=False):
    directory = out / "controls" / fold["id"]
    context = {"plan_sha256": b.sha256(out / "plan.json"), "fold": fold, "control": "fixed_first20"}
    if directory.exists():
        if not resume:
            raise FileExistsError(directory)
        return checked_receipt(directory, context)
    directory.mkdir(parents=True, exist_ok=False)
    calendar = tools.read_data(train, start=fold["start"], end=fold["end"], columns=["date"])
    b.write_holdings(directory / "validation.csv",
                     ((str(d)[:10], b.STOCKS[:20]) for d in sorted(calendar.date.unique())))
    account = tools.backtest(directory / "validation.csv", train, fold["start"], fold["end"])
    write_new(directory / "accounting.json", account)
    return receipt(directory, context, ["validation.csv", "accounting.json"],
                   result={k: account[k] for k in ("status", "sharpe", "final_nav")})


def select_candidate(candidates):
    if len(candidates) != 9 or {(c["alpha"], c["hold_bonus"]) for c in candidates} != {
            (a, h) for a in ALPHAS for h in BONUSES}:
        raise ValueError("All nine predefined candidates must be present exactly once")
    for item in candidates:
        scores = item["fold_sharpes"]
        if len(scores) != 2 or any(not isinstance(x, (int, float)) or not math.isfinite(x) for x in scores):
            raise ValueError("Both development folds must have finite scorable net Sharpe")
    return max(candidates, key=lambda c: (min(c["fold_sharpes"]),
        sum(c["fold_sharpes"]) / 2, -c["hold_bonus"], -c["alpha"]))


def develop(out, train, tools, resume=False):
    out = Path(out)
    if out.exists():
        if not resume:
            raise FileExistsError("Existing directory refused; use --resume for completed boundaries only")
        open_plan(out)
    else:
        if resume:
            raise ValueError("--resume requires an existing experiment")
        out.mkdir(parents=True, exist_ok=False)
        write_new(out / "plan.json", make_plan())
    if (out / "holdout_started.json").exists():
        raise ValueError("Holdout was already touched; development cannot resume as a pristine experiment")
    candidates, artifacts = [], {}
    for ai, alpha in enumerate(ALPHAS):
        models = [get_model(out, train, tools, fold, alpha, ai, resume) for fold in FOLDS]
        for bi, bonus in enumerate(BONUSES):
            results = [evaluate(out, train, tools, fold, model, alpha, bonus, ai, bi, resume)
                       for fold, model in zip(FOLDS, models)]
            if any(r["result"]["status"] != "OK" for r in results):
                raise ValueError("Unscorable development run; no automatic scheme lock")
            candidates.append({"alpha": alpha, "hold_bonus": bonus,
                               "fold_sharpes": [r["result"]["sharpe"] for r in results]})
            print(json.dumps({"completed_candidate": len(candidates), "total": 9,
                              "alpha": alpha, "hold_bonus": bonus}), flush=True)
    for fold in FOLDS:
        fixed_control(out, train, tools, fold, resume)
    # Bind every completed model, prediction/accounting and control receipt.
    for path in sorted(out.glob("*/*/receipt.json")):
        artifacts[str(path.relative_to(out))] = b.sha256(path)
    selected = select_candidate(candidates)
    frozen = {"format": "frozen_selection_v1", "plan_sha256": b.sha256(out / "plan.json"),
              "selection_rule": RULE, "candidates": candidates, "selected": selected,
              "artifact_receipts_sha256": artifacts, "holdout_used_for_selection": False,
              "fold_account_note": "independent accounts; fold Sharpe is not pooled continuous-account Sharpe"}
    if (out / "selection_lock.json").exists():
        if read_json(out / "selection_lock.json") != frozen:
            raise ValueError("Recomputed development differs from selection lock")
    else:
        write_new(out / "selection_lock.json", frozen)
    return frozen


def checked_lock(out):
    open_plan(out)
    locked = read_json(out / "selection_lock.json")
    if locked.get("plan_sha256") != b.sha256(out / "plan.json") or locked.get("selection_rule") != RULE:
        raise ValueError("Selection lock provenance mismatch")
    if locked.get("holdout_used_for_selection") is not False or locked.get("selected") != select_candidate(locked["candidates"]):
        raise ValueError("Frozen selection changed")
    expected_paths, reconstructed = set(), []
    for ai, alpha in enumerate(ALPHAS):
        for fold in FOLDS:
            directory = out / "models" / f"{fold['id']}_a{ai:02d}"
            expected_paths.add(str((directory / "receipt.json").relative_to(out)))
            checked_receipt(directory, context_for(out, fold, alpha))
        for bi, bonus in enumerate(BONUSES):
            scores = []
            for fold in FOLDS:
                directory = out / "development" / f"{fold['id']}_a{ai:02d}_b{bi:02d}"
                expected_paths.add(str((directory / "receipt.json").relative_to(out)))
                evidence = checked_receipt(directory, context_for(out, fold, alpha, bonus))
                result = read_json(directory / "result.json")
                accounting = read_json(directory / "accounting.json")
                if evidence["result"] != result or result["sharpe"] != accounting["sharpe"] or result["status"] != "OK":
                    raise ValueError("Development result/accounting mismatch")
                scores.append(result["sharpe"])
            reconstructed.append({"alpha": alpha, "hold_bonus": bonus, "fold_sharpes": scores})
    for fold in FOLDS:
        directory = out / "controls" / fold["id"]
        expected_paths.add(str((directory / "receipt.json").relative_to(out)))
        checked_receipt(directory, {"plan_sha256": b.sha256(out / "plan.json"), "fold": fold, "control": "fixed_first20"})
    if set(locked.get("artifact_receipts_sha256", {})) != expected_paths or locked["candidates"] != reconstructed:
        raise ValueError("Development candidates/receipt set changed")
    for name, expected in locked["artifact_receipts_sha256"].items():
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or b.sha256(out / path) != expected:
            raise ValueError("Development receipt changed")
        data = read_json(out / path)
        checked_receipt((out / path).parent, data["context"])
    return locked


def run_holdout(out, train, tools):
    out = Path(out)
    locked = checked_lock(out)
    # Claim before any 2020 read. A failure remains consumed, never silently retried.
    write_new(out / "holdout_started.json", {"started_utc": now(),
        "selection_lock_sha256": b.sha256(out / "selection_lock.json"),
        "policy": "single attempt; failure still consumes pristine holdout"})
    selected = locked["selected"]
    model = get_model(out, train, tools, HOLDOUT, selected["alpha"], 0)
    result = evaluate(out, train, tools, HOLDOUT, model, selected["alpha"], selected["hold_bonus"], 0, 0, parent="holdout")
    control = fixed_control(out, train, tools, HOLDOUT)
    if result["result"]["status"] != "OK":
        raise ValueError("Holdout not scorable; preserve the consumed attempt and disclose failure")
    summary = {"status": "COMPLETE", "selection_lock_sha256": b.sha256(out / "selection_lock.json"),
               "holdout_started_sha256": b.sha256(out / "holdout_started.json"),
               "selected": selected, "result": result["result"], "fixed20": control["result"],
               "receipts_sha256": {str(p.relative_to(out)): b.sha256(p) for p in (
                   out / "models/2020_a00/receipt.json", out / "holdout/2020_a00_b00/receipt.json",
                   out / "controls/2020/receipt.json")},
               "used_for_selection": False, "test_sharpe": None}
    write_new(out / "holdout_summary.json", summary)
    return summary


def checked_holdout(out, locked):
    summary = read_json(out / "holdout_summary.json")
    if (summary.get("status") != "COMPLETE" or summary.get("selected") != locked["selected"] or
        summary.get("selection_lock_sha256") != b.sha256(out / "selection_lock.json") or
        summary.get("holdout_started_sha256") != b.sha256(out / "holdout_started.json") or
        summary.get("used_for_selection") is not False):
        raise ValueError("Holdout completion/lock mismatch")
    expected_paths = {"models/2020_a00/receipt.json", "holdout/2020_a00_b00/receipt.json", "controls/2020/receipt.json"}
    if set(summary.get("receipts_sha256", {})) != expected_paths:
        raise ValueError("Holdout evidence missing")
    for name, expected in summary["receipts_sha256"].items():
        if b.sha256(out / name) != expected:
            raise ValueError("Holdout receipt changed")
        data = read_json(out / name)
        checked_receipt((out / name).parent, data["context"])
    selected = locked["selected"]
    checked_receipt(out / "models/2020_a00", context_for(out, HOLDOUT, selected["alpha"]))
    result = checked_receipt(out / "holdout/2020_a00_b00",
                             context_for(out, HOLDOUT, selected["alpha"], selected["hold_bonus"]))
    control = checked_receipt(out / "controls/2020",
        {"plan_sha256": b.sha256(out / "plan.json"), "fold": HOLDOUT, "control": "fixed_first20"})
    if summary["result"] != result["result"] or summary["fixed20"] != control["result"]:
        raise ValueError("Holdout summary/result mismatch")
    return summary


def finalize(out, train, test, tools_path, tools, ai_tools):
    import subprocess
    import shutil
    out = Path(out)
    if not ai_tools.strip():
        raise ValueError("Record the AI tools actually used")
    locked = checked_lock(out)
    checked_holdout(out, locked)
    b.verify_data(test, "test", tools)
    directory = out / "final"
    directory.mkdir(exist_ok=False)
    selected = locked["selected"]
    common = [sys.executable, "-m", "competition.baseline"]
    subprocess.run(common + ["fit", "--tools", str(Path(tools_path).resolve()), "--train", str(Path(train).resolve()),
        "--train-end", "2020-12-31", "--alpha", str(selected["alpha"]), "--out", str((directory / "model").resolve())], cwd=ROOT, check=True)
    for name in ("prediction", "reproduction"):
        subprocess.run(common + ["predict", "--tools", str(Path(tools_path).resolve()), "--test", str(Path(test).resolve()),
            "--model", str((directory / "model/model.json").resolve()), "--hold-bonus", str(selected["hold_bonus"]),
            "--out", str((directory / name).resolve())], cwd=ROOT, check=True)
    hashes = [b.sha256(directory / name / "submission.csv") for name in ("prediction", "reproduction")]
    if hashes[0] != hashes[1]:
        raise ValueError("Repeated prediction differs; no delivery marked complete")
    packaged = package(directory / "prediction", tools_path, test, directory / "code.zip", ai_tools)
    shutil.copyfile(directory / "prediction/submission.csv", directory / "submission.csv")
    return receipt(directory, {"selection_lock_sha256": b.sha256(out / "selection_lock.json"),
        "holdout_summary_sha256": b.sha256(out / "holdout_summary.json")}, ["submission.csv", "code.zip"],
        status="COMPLETE", official_check=packaged["official_check"], reproduction_matches=True,
        test_sharpe=None, report_pptx_created=False, ai_tools=ai_tools.strip())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["develop", "holdout", "finalize"])
    p.add_argument("--tools", type=Path, required=True)
    p.add_argument("--train", type=Path, required=True)
    p.add_argument("--test", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--ai-tools", default="")
    a = p.parse_args()
    if a.resume and a.command != "develop":
        p.error("Only development supports resuming completed boundaries")
    if a.command == "finalize" and (a.test is None or not a.ai_tools.strip()):
        p.error("finalize requires --test and --ai-tools")
    if a.command != "finalize" and a.test is not None:
        p.error("Development/holdout do not accept or access test data")
    tools = b.official_tools(a.tools)
    b.verify_data(a.train, "train", tools)
    if a.command == "develop":
        result = develop(a.out, a.train, tools, a.resume)
    elif a.command == "holdout":
        result = run_holdout(a.out, a.train, tools)
    else:
        result = finalize(a.out, a.train, a.test, a.tools, tools, a.ai_tools)
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
