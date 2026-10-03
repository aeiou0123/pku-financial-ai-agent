"""Chronological workflow contracts; synthetic returns are never performance evidence."""
from pathlib import Path
import json

import numpy as np
import pandas as pd
import pytest

from competition import baseline as b
from competition import experiment as e


def fixture_tools():
    """Use the same accounting implementation via a small local contract adapter."""
    dates = ["2015-12-29", "2015-12-30", "2016-01-04", "2016-01-05",
             "2017-12-28", "2017-12-29", "2018-01-02", "2018-01-03",
             "2019-12-30", "2019-12-31", "2020-01-02", "2020-01-03", "2020-01-06"]
    rng = np.random.default_rng(734)
    frames = []
    for date in dates:
        d = pd.Timestamp(date).date()
        frame = pd.DataFrame(rng.normal(size=(400, 100)), columns=b.FACTORS)
        frame["date"], frame["asof_date"], frame["stock_id"] = d, (pd.Timestamp(d) - pd.offsets.BDay()).date(), b.STOCKS
        x, _ = b.daily_features(frame)
        frame["return"] = .002 * x[:, 0] + rng.normal(0, .006, 400)
        frames.append(frame)

    class Contract:
        def __init__(self):
            self.data = pd.concat(frames, ignore_index=True)
            self.reads = []
            self.backtests = []

        def read_data(self, path, start=None, end=None, columns=None):
            self.reads.append((start, end, tuple(columns)))
            selected = self.data
            if start:
                selected = selected[selected.date >= pd.Timestamp(start).date()]
            if end:
                selected = selected[selected.date <= pd.Timestamp(end).date()]
            return selected[columns].copy()

        def backtest(self, path, train, start, end):
            self.backtests.append((start, end))
            # Official accounting is separately integrated in competition.smoke;
            # here a deterministic scorable contract drives the control flow.
            frame = pd.read_csv(path)
            chosen = [int(s[1:]) - 1 for s in frame.stock_id]
            assert all(g.stock_id.nunique() == 20 for _, g in frame.groupby("date"))
            return {"status": "OK", "sharpe": .1 + sum(chosen) / len(chosen) / 400,
                    "final_nav": 1.01, "details": [{"fee": .0002}] * frame.date.nunique()}
    return Contract()


@pytest.fixture
def developed(tmp_path):
    tools = fixture_tools()
    out = tmp_path / "experiment"
    locked = e.develop(out, "unused_train", tools)
    return out, tools, locked


def test_complete_grid_reuses_six_models_and_never_reads_holdout_labels(developed, monkeypatch):
    out, tools, locked = developed
    assert len(list((out / "models").glob("*/model.json"))) == 6
    assert len(list((out / "development").glob("*/accounting.json"))) == 18
    assert len(locked["artifact_receipts_sha256"]) == 26
    assert len(tools.backtests) == 20
    assert locked["holdout_used_for_selection"] is False
    assert not any("return" in columns and (end is None or end > "2019-12-31")
                   for start, end, columns in tools.reads)
    assert all(end <= "2019-12-31" for _, end in tools.backtests)
    assert not (out / "holdout_started.json").exists()
    monkeypatch.setattr(b, "fit_days", lambda *args: pytest.fail("Completed models must not retrain"))
    assert e.develop(out, "unused_train", tools, resume=True) == locked
    with pytest.raises(FileExistsError):
        e.develop(out, "unused_train", tools)


def test_selection_prefers_worst_fold_then_mean_then_simpler_parameters():
    candidates = [{"alpha": a, "hold_bonus": h, "fold_sharpes": [.1, 10.]}
                  for a in e.ALPHAS for h in e.BONUSES]
    candidates[4]["fold_sharpes"] = [.2, .2]
    assert e.select_candidate(candidates) == candidates[4]
    for c in candidates:
        c["fold_sharpes"] = [.2, .3]
    assert e.select_candidate(candidates) == candidates[0]
    candidates[0]["fold_sharpes"] = [None, .3]
    with pytest.raises(ValueError, match="scorable"):
        e.select_candidate(candidates)
    with pytest.raises(ValueError, match="nine"):
        e.select_candidate(candidates[1:])


def test_single_holdout_does_not_reselect_and_cannot_repeat(developed):
    out, tools, locked = developed
    frozen_bytes = (out / "selection_lock.json").read_bytes()
    summary = e.run_holdout(out, "unused_train", tools)
    assert summary["selected"] == locked["selected"]
    assert summary["used_for_selection"] is False
    assert summary["test_sharpe"] is None
    assert (out / "selection_lock.json").read_bytes() == frozen_bytes
    assert e.checked_holdout(out, e.checked_lock(out)) == summary
    with pytest.raises(FileExistsError):
        e.run_holdout(out, "unused_train", tools)
    with pytest.raises(ValueError, match="already touched"):
        e.develop(out, "unused_train", tools, resume=True)


def test_failed_holdout_is_consumed_before_any_2020_read(developed, monkeypatch):
    out, tools, _ = developed
    def fail(*args, **kwargs):
        assert (out / "holdout_started.json").exists()
        raise RuntimeError("Training interrupted")
    monkeypatch.setattr(e, "get_model", fail)
    with pytest.raises(RuntimeError):
        e.run_holdout(out, "unused_train", tools)
    assert not (out / "holdout_summary.json").exists()
    with pytest.raises(FileExistsError):
        e.run_holdout(out, "unused_train", tools)


@pytest.mark.parametrize("file", ["models/A_a00/model.json", "development/B_a01_b02/validation.csv",
                                 "development/A_a02_b01/accounting.json", "controls/A/accounting.json"])
def test_modified_development_evidence_blocks_holdout_before_claim(developed, file):
    out, tools, _ = developed
    with (out / file).open("a") as handle:
        handle.write("changed")
    with pytest.raises(ValueError, match="changed"):
        e.run_holdout(out, "unused_train", tools)
    assert not (out / "holdout_started.json").exists()


def test_changed_plan_or_selection_is_rejected(developed):
    out, _, _ = developed
    locked = e.read_json(out / "selection_lock.json")
    locked["selected"]["hold_bonus"] = 99
    (out / "selection_lock.json").write_text(json.dumps(locked))
    with pytest.raises(ValueError, match="changed"):
        e.checked_lock(out)
    plan = e.read_json(out / "plan.json")
    plan["selection_rule"] = "peek at 2020"
    (out / "plan.json").write_text(json.dumps(plan))
    with pytest.raises(ValueError, match="changed"):
        e.open_plan(out)


def test_incomplete_development_boundary_refused_without_overwrite(tmp_path):
    out = tmp_path / "partial"
    out.mkdir()
    e.write_new(out / "plan.json", e.make_plan())
    partial = out / "models/A_a00"
    partial.mkdir(parents=True)
    sentinel = partial / "sentinel.txt"
    sentinel.write_text("keep failed evidence")
    with pytest.raises(FileNotFoundError):
        e.develop(out, "unused_train", fixture_tools(), resume=True)
    assert sentinel.read_text() == "keep failed evidence"


def test_finalization_requires_completed_holdout_and_real_tools_metadata(developed):
    out, tools, _ = developed
    with pytest.raises(ValueError, match="AI tools"):
        e.finalize(out, "unused", "unused", "unused", tools, "")
    with pytest.raises(FileNotFoundError):
        e.finalize(out, "unused", "unused", "unused", tools, "actual tool")
    assert not (out / "final").exists()


def test_modified_holdout_artifact_blocks_finalization(developed):
    out, tools, locked = developed
    e.run_holdout(out, "unused", tools)
    (out / "holdout/2020_a00_b00/validation.csv").write_text("tampered")
    with pytest.raises(ValueError, match="changed"):
        e.checked_holdout(out, locked)


def test_changed_development_scores_cannot_drive_selection(developed):
    out, tools, _ = developed
    lock = e.read_json(out / "selection_lock.json")
    lock["candidates"][0]["fold_sharpes"] = [999., 999.]
    lock["selected"] = lock["candidates"][0]
    (out / "selection_lock.json").write_text(json.dumps(lock))
    with pytest.raises(ValueError, match="changed"):
        e.run_holdout(out, "unused", tools)
    assert not (out / "holdout_started.json").exists()


def test_changed_holdout_summary_cannot_be_reported_as_measured(developed):
    out, tools, lock = developed
    e.run_holdout(out, "unused", tools)
    summary = e.read_json(out / "holdout_summary.json")
    summary["result"]["sharpe"] = 999.
    (out / "holdout_summary.json").write_text(json.dumps(summary))
    with pytest.raises(ValueError, match="mismatch"):
        e.checked_holdout(out, lock)


@pytest.mark.parametrize("mismatch", [False, True])
def test_final_commands_use_frozen_parameters_and_compare_predictions(developed, monkeypatch, mismatch):
    import subprocess
    out, tools, lock = developed
    e.run_holdout(out, "unused", tools)
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        path = Path(command[command.index("--out") + 1])
        path.mkdir(parents=True)
        if command[3] == "fit":
            assert command[command.index("--alpha") + 1] == str(lock["selected"]["alpha"])
            assert command[command.index("--train-end") + 1] == "2020-12-31"
            (path / "model.json").write_text("{}")
        else:
            assert command[command.index("--hold-bonus") + 1] == str(lock["selected"]["hold_bonus"])
            assert "--train" not in command
            (path / "submission.csv").write_text("different" if mismatch and path.name == "reproduction" else "same")
    def fake_package(run, tools_path, test, output, ai_tools):
        assert not mismatch, "Mismatch must stop before packaging"
        assert ai_tools == "actual Qwen/Kimi versions recorded"
        output.write_bytes(b"synthetic package contract")
        return {"official_check": {"status": "VALID"}}
    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(e, "package", fake_package)
    monkeypatch.setattr(b, "verify_data", lambda path, split, tool: None)
    if mismatch:
        with pytest.raises(ValueError, match="differs"):
            e.finalize(out, "train", "test", "tools", tools, "actual Qwen/Kimi versions recorded")
        assert not (out / "final/receipt.json").exists()
        assert not (out / "final/code.zip").exists()
    else:
        receipt = e.finalize(out, "train", "test", "tools", tools, "actual Qwen/Kimi versions recorded")
        assert receipt["reproduction_matches"] is True
        assert receipt["test_sharpe"] is None
        assert receipt["report_pptx_created"] is False
    assert len(calls) == 3


@pytest.mark.parametrize("command", ["develop", "holdout"])
def test_cli_never_accepts_test_data_before_finalization(command, monkeypatch, tmp_path):
    import sys
    monkeypatch.setattr(sys, "argv", ["experiment", command, "--train", "unused", "--tools", "unused",
        "--test", "test.parquet", "--out", str(tmp_path)])
    monkeypatch.setattr(b, "official_tools", lambda *a: pytest.fail("Invalid CLI must fail before tool/data access"))
    with pytest.raises(SystemExit) as error:
        e.main()
    assert error.value.code == 2
