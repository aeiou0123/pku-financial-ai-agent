"""Generate clearly synthetic reproducible user-input examples."""
from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from src.financial_intake import FIELDS
from src.harness.documents import digest
from src.harness.financial import csv_bytes

ROOT = Path(__file__).resolve().parents[1] / "docs/harness/examples"


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    text = "合成样例，不是真实公司财务数据。股票代码 000000 为占位代码。\n披露日期：2025-03-01；报表期间：2024-12-31；合并报表；原始版本；单位：元。\n总资产 1000；总负债 400；所有者权益 600。\n年度营业收入 500；年度营业成本 300；年度归母净利润 50。\n"
    raw = text.encode("utf-8")
    (ROOT / "synthetic_financial.txt").write_bytes(raw)
    values = [("total_assets", "总资产", "1000"), ("total_liabilities", "总负债", "400"), ("total_equity", "所有者权益", "600"),
              ("revenue", "营业收入", "500"), ("cost_of_revenue", "营业成本", "300"), ("net_profit_parent", "归母净利润", "50")]
    rows = []
    for metric, label, value in values:
        rows.append(dict(zip(FIELDS, ["000000", "合成示例公司（非真实公司）", "2024-12-31", "2025-03-01", "consolidated",
                     "point_in_time" if metric.startswith("total_") else "annual", label, metric, value, "元", "CNY", "original",
                     "synthetic_example", "synthetic_financial.txt", "line:3" if metric.startswith("total_") else "line:4", digest(raw)])))
    (ROOT / "synthetic_financial.csv").write_bytes(csv_bytes(rows))
    dates = pd.bdate_range("2025-01-01", periods=80)
    prices = [{"date": dt.date().isoformat(), "stock": f"{stock:06d}", "close": round(20 + stock + i * (.04 + stock * .01) + ((i + stock) % 7) * .03, 6)}
              for i, dt in enumerate(dates) for stock in range(1, 5)]
    (ROOT / "synthetic_prices.csv").write_bytes(pd.DataFrame(prices).to_csv(index=False).encode("utf-8-sig"))


if __name__ == "__main__":
    main()
