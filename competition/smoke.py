"""Synthetic integration checks using the actual official accounting tool."""
import argparse
import json
from pathlib import Path

import numpy as np

from competition.baseline import fit_days, predict_days, official_tools, write_holdings, sha256, TOOLS_SHA


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tools", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    tools = official_tools(args.tools)
    # A deterministic synthetic fixture, not competition training or performance evidence.
    import pandas as pd
    from competition.baseline import daily_features, FACTORS, STOCKS
    rng = np.random.default_rng(712)
    days = []
    for d in pd.bdate_range("2015-01-02", periods=30):
        frame = pd.DataFrame(rng.normal(size=(400, 100)), columns=FACTORS)
        frame["date"], frame["asof_date"], frame["stock_id"] = d.date(), (d - pd.offsets.BDay()).date(), STOCKS
        x, _ = daily_features(frame)
        frame["return"] = .002 * x[:, 0] + rng.normal(0, .004, 400)
        days.append(frame)
    model = fit_days(days[:20], .001)
    selected = list(predict_days(model, days[20:], .0004))
    args.out.mkdir(parents=True, exist_ok=False)
    path = args.out / "synthetic_holdings.csv"
    rows = write_holdings(path, selected)
    parsed = tools.parse_csv(path, [date for date, _ in selected])
    returns = np.stack([day.sort_values("stock_id")["return"].to_numpy() for day in days[20:]])
    accounting = tools.account(returns, parsed)
    assert parsed.shape == (10, 20)
    assert accounting["details"][0]["buy_fee"] > 0
    assert accounting["details"][-1]["terminal_fee"] > 0
    assert np.isclose(accounting["final_nav"], np.prod(1 + np.array(accounting["daily_net_returns"])))
    # Same names still incur fees to restore equal weights after unequal returns.
    fixed = np.tile(np.arange(20), (10, 1))
    static = tools.account(returns, fixed)
    assert static["details"][1]["trading_fee"] > 0
    summary = {"scope": "SYNTHETIC_INTEGRATION_ONLY_NOT_COMPETITION_PERFORMANCE",
               "tools_sha256": TOOLS_SHA, "rows": rows, "days": len(selected),
               "csv_sha256": sha256(path), "seed": 712, "result": "PASS",
               "checks": ["same-row synthetic signal", "20 unique holdings each day",
                          "official CSV parse", "initial buy fee", "terminal sale fee",
                          "continuous NAV", "fixed-list equal-weight rebalance fees"],
               "real_training_run": False, "real_test_submission_check": False}
    (args.out / "smoke_review.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
