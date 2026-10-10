"""Validate public long-v2 data and stage CSMAR separately, without guessing semantics."""
import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.financial_intake import validate, FIELDS, save_run
from src.financial_evidence import COMPANIES

MAPPING = {"assets": "total_assets", "liabilities": "total_liabilities", "equity_total": "total_equity",
           "equity_parent": "parent_equity", "revenue": "revenue", "cost_of_sales": "cost_of_revenue",
           "selling_expense": "selling_expense", "admin_expense": "admin_expense", "rd_expense": "rd_expense",
           "profit_total": "pretax_profit", "income_tax": "income_tax_expense", "net_profit": "net_profit",
           "net_profit_parent": "net_profit_parent", "operating_cash_flow": "operating_cash_flow",
           "purchase_long_term_assets_cash": "capex_cash_paid"}


def build(public_root, csmar_root, out, as_of):
    out.mkdir(parents=True, exist_ok=False)
    input_path = public_root / "example/public_financial_green_2024_2025.csv"
    records, quality = validate(input_path, public_root, as_of)
    if quality["errors"]:
        raise ValueError(quality["errors"])
    run = save_run(public_root, input_path, records, quality)
    review = json.loads((public_root / "review/source_review.json").read_text(encoding="utf-8"))
    limits = ["2024比较数来自2025年报，披露日为2026-04-23；不能当作2024年实时可得样本。",
              "当前展示仅含绿的谐波34条合并年度财务原页核对样本，不能代表全行业覆盖。",
              "当前CSMAR正式单位、累计/单期、更正含义和披露日期仍待核；待核原值不自动进入事实样本。",
              "固定情景属于假设演示；历史数据不自动校准预测，未验证因果效应或投资效果。"]
    snapshot = {"schema": "historical_public_financial_v1", "as_of": as_of.isoformat(), "records": records,
                "source_review": {k: review[k] for k in ("sample_source", "anchor_source")},
                "validation_summary": quality, "limits": limits, "forecast_updated": False}
    (out / "historical_public_financial.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    with (csmar_root / "derived/codex_review/historical_evidence_ledger.csv").open(encoding="utf-8-sig", newline="") as f:
        ledger = list(csv.DictReader(f))
    pending, status = [], []
    for index, row in enumerate(ledger):
        canonical = MAPPING.get(row["metric"], "")
        pending.append(dict(zip(FIELDS, [row["stock_code"], COMPANIES[row["stock_code"]], row["report_period"], "",
             "", "", row["field_name"], canonical, row["value_original"], "", "CNY",
             "observed_IfCorrect=" + row["IfCorrect_observed"], "CSMAR_client_wrapper", row["source_file"],
             row["source_locator"], row["source_sha256"]])))
        status.append({"staging_row": index + 2, "state": "PENDING_NOT_FOR_VALIDATED_INTAKE",
                       "missing_review": ["published_at", "current_unit_definition", "statement_scope_definition",
                                          "period_type_definition", "revision_semantics"] + ([] if canonical else ["unsupported_canonical_metric"]),
                       "original_typrep": row["Typrep"], "field_code": row["field_code"],
                       "missing_value": row["missing"], "source_kind": "client_extracted_wrapper_not_full_HTTP"})
    with (out / "csmar_pending_long_v2.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(pending)
    (out / "csmar_pending_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"public_rows": len(records), "pending_vendor_rows": len(pending), "intake_run": str(run), "forecast_updated": False}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--public-root", type=Path, required=True); p.add_argument("--csmar-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True); p.add_argument("--as-of", type=date.fromisoformat, required=True)
    a = p.parse_args(); print(json.dumps(build(a.public_root, a.csmar_root, a.out, a.as_of), ensure_ascii=False, indent=2))
