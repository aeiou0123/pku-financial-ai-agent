"""Synthetic workflow integration using actual official portfolio accounting."""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import io
import json
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import numpy as np
import pandas as pd

from competition import baseline as b
from competition import experiment as e

SCOPE = "SYNTHETIC_WORKFLOW_WITH_REAL_ACCOUNTING_NOT_COMPETITION_PERFORMANCE"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tools", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    official = b.official_tools(a.tools)
    a.out.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    rng = np.random.default_rng(734)
    dates = ["2015-12-29", "2015-12-30", "2016-01-04", "2016-01-05", "2017-12-28", "2017-12-29",
             "2018-01-02", "2018-01-03", "2019-12-30", "2019-12-31", "2020-01-02", "2020-01-03", "2020-01-06"]
    frames = []
    for value in dates:
        date = pd.Timestamp(value).date()
        frame = pd.DataFrame(rng.normal(size=(400, 100)), columns=b.FACTORS)
        frame["date"], frame["asof_date"], frame["stock_id"] = date, (pd.Timestamp(date) - pd.offsets.BDay()).date(), b.STOCKS
        x, _ = b.daily_features(frame)
        frame["return"] = .002 * x[:, 0] + rng.normal(0, .006, 400)
        frames.append(frame)
    data = pd.concat(frames, ignore_index=True)

    class SyntheticTools:
        reads = []
        accounts = 0

        def read_data(self, path, start=None, end=None, columns=None):
            assert path == "synthetic_train"
            self.reads.append((start, end, tuple(columns)))
            frame = data
            if start:
                frame = frame[frame.date >= pd.Timestamp(start).date()]
            if end:
                frame = frame[frame.date <= pd.Timestamp(end).date()]
            return frame[columns].copy()

        def backtest(self, path, train, start, end):
            df = self.read_data(train, start, end, ["date", "stock_id", "return"])
            df["date"] = df["date"].astype(str)
            calendar = sorted(df.date.unique())
            choices = official.parse_csv(path, calendar)
            returns = df.pivot(index="date", columns="stock_id", values="return").reindex(index=calendar, columns=b.STOCKS)
            self.accounts += 1
            return official.account(returns.to_numpy(), choices)

    tools = SyntheticTools()
    experiment = a.out / "synthetic_experiment"
    normal_plan = e.make_plan
    def synthetic_plan():
        return {**normal_plan(), "scope": SCOPE, "official_parquet_validation_bypassed_for_fixture": True}
    # Never label fixture-trained models with the real training file's fingerprint.
    synthetic_identity = hashlib.sha256(pd.util.hash_pandas_object(data, index=True).values.tobytes()).hexdigest()
    with patch.object(b, "DATA_SHA", {"train": "synthetic:" + synthetic_identity, "test": "NOT_ACCESSED"}), patch.object(e, "make_plan", synthetic_plan):
        with contextlib.redirect_stdout(io.StringIO()):
            lock = e.develop(experiment, "synthetic_train", tools)
        development_reads = tools.reads.copy()
        assert all(end is not None and end <= "2019-12-31"
                   for _, end, columns in development_reads if "return" in columns)
        lock_sha = b.sha256(experiment / "selection_lock.json")
        e.run_holdout(experiment, "synthetic_train", tools)
        assert b.sha256(experiment / "selection_lock.json") == lock_sha
        e.checked_holdout(experiment, e.checked_lock(experiment))
        try:
            e.run_holdout(experiment, "synthetic_train", tools)
        except FileExistsError:
            pass
        else:
            raise AssertionError("Second holdout attempt was not refused")
        try:
            e.develop(experiment, "synthetic_train", tools, resume=True)
        except ValueError:
            pass
        else:
            raise AssertionError("Development reopened after holdout")
    review = {"scope": SCOPE, "result": "PASS", "seed": 734, "fixture_rows": len(data),
              "development_models": 6, "development_candidates": len(lock["candidates"]),
              "development_validation_runs": 18, "development_fixed_controls": 2,
              "official_account_calls": tools.accounts, "holdout_attempts_completed": 1,
              "test_data_access": False, "real_training_run": False, "real_test_submission": False,
              "performance_metrics_reported": False,
              "elapsed_seconds": round(perf_counter() - started, 3),
              "code_sha256": e.code_hashes(), "smoke_code_sha256": b.sha256(Path(__file__)),
              "tools_sha256": b.TOOLS_SHA, "synthetic_fixture_identity": synthetic_identity,
              "checks": ["six cached model fits for eighteen development strategies",
                         "development labels end before 2020", "frozen selection bound to accounting receipts",
                         "real official CSV parsing and portfolio fees on synthetic returns",
                         "holdout lock remains unchanged", "second holdout attempt refused",
                         "development after holdout refused"],
              "limitations": ["synthetic returns; no real Parquet validation or research performance",
                              "finalization subprocess contracts are regression-tested, not a real submission"]}
    e.write_new(a.out / "workflow_smoke_review.json", review)
    print(json.dumps(review, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
