import csv
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from src.financial_intake import FIELDS, init_workspace, inventory, save_run, sha256, validate

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def evidence(tmp_path):
    source = tmp_path / "raw.csv"
    source.write_text("original,value\n营业收入,100\n", encoding="utf-8")
    row = dict(zip(FIELDS, ["002472", "公司", "2024-12-31", "2025-04-30",
                           "consolidated", "annual", "营业收入", "revenue", "100", "万元",
                           "CNY", "original", "fixture", "raw.csv", "row 2", sha256(source)]))
    return tmp_path, row


def check(evidence, rows):
    root, _ = evidence
    path = root / "mapped.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return validate(path, root, date(2026, 10, 9))


def test_units_and_leading_zero_preserved(evidence):
    normalized, report = check(evidence, [evidence[1]])
    assert normalized[0]["stock_code"] == "002472"
    assert Decimal(normalized[0]["value_cny"]) == 1000000
    assert report["status"] == "partial"  # No balance totals or cost.
    assert report["forecast_updated"] is False


@pytest.mark.parametrize("value", ["", "—", "NA", "-"])
def test_missing_never_zero(evidence, value):
    normalized, report = check(evidence, [{**evidence[1], "value_original": value}])
    assert normalized[0]["value_cny"] == ""
    assert report["warnings"]


def test_observed_zero_preserved(evidence):
    normalized, report = check(evidence, [{**evidence[1], "value_original": "0"}])
    assert normalized[0]["value_cny"] == "0"
    assert not report["warnings"]


@pytest.mark.parametrize("change", [
    {"value_original": "NaN"}, {"value_original": "Infinity"}, {"value_original": "1,23"},
    {"stock_code": "2472"}, {"published_at": "2026-10-10"}, {"published_at": ""},
    {"published_at": "2024-01-01"}, {"unit": "unknown"}, {"currency": "USD"},
    {"source_file": "../escape.csv"}, {"source_sha256": "wrong"},
    {"report_period": "2026-06-30", "published_at": "2026-08-30", "period_type": "annual"},
])
def test_bad_financial_or_source_metadata_blocked(evidence, change):
    normalized, report = check(evidence, [{**evidence[1], **change}])
    assert not normalized
    assert report["status"] == "invalid"


def test_duplicate_not_silently_selected(evidence):
    _, report = check(evidence, [evidence[1], evidence[1]])
    assert any(e["issue"] == "duplicate_metric_requires_review" for e in report["errors"])


def test_revision_kept_separate(evidence):
    normalized, report = check(evidence, [evidence[1], {**evidence[1], "revision_flag": "restated"}])
    assert len(normalized) == 2
    assert not report["errors"]


def test_total_equity_not_parent_equity_for_balance(evidence):
    row = evidence[1]
    rows = [{**row, "period_type": "point_in_time", "canonical_metric": m, "value_original": v}
            for m, v in [("total_assets", "100"), ("total_liabilities", "30"), ("parent_equity", "60")]]
    _, partial = check(evidence, rows)
    assert partial["checks"][0]["status"] == "not_checked_missing_totals"
    _, complete = check(evidence, rows + [{**rows[0], "canonical_metric": "total_equity", "value_original": "70"}])
    assert complete["checks"][0]["status"] == "passed"
    _, failed = check(evidence, rows + [{**rows[0], "canonical_metric": "total_equity", "value_original": "60"}])
    assert failed["status"] == "invalid"


def test_half_year_cumulative_not_annualized(evidence):
    normalized, report = check(evidence, [{**evidence[1], "report_period": "2026-06-30",
                                         "published_at": "2026-08-30", "period_type": "cumulative"}])
    assert normalized[0]["value_cny"] == "1000000"
    assert not report["errors"]


def test_scope_not_mixed_for_margin(evidence):
    row = evidence[1]
    _, report = check(evidence, [row, {**row, "canonical_metric": "cost_of_revenue", "statement_scope": "parent"}])
    assert not any(c["status"] == "calculated" for c in report["checks"])


def test_symlink_escape_rejected(evidence, tmp_path_factory):
    root, row = evidence
    outside = tmp_path_factory.mktemp("outside") / "raw.csv"
    outside.write_text("outside")
    (root / "link.csv").symlink_to(outside)
    _, report = check(evidence, [{**row, "source_file": "link.csv", "source_sha256": sha256(outside)}])
    assert report["errors"][0]["issue"] == "source_file_outside_root"


def test_inventory_init_and_runs_preserve_originals(evidence):
    root, row = evidence
    init_workspace(root)
    raw = root / "raw/A_financial/export.csv"
    raw.write_text("原始字段,值\n证券代码,002472\n", encoding="utf-8-sig")
    before = sha256(raw)
    init_workspace(root)
    items = inventory(root)
    assert items["files"][0]["sha256"] == before
    normalized, report = check(evidence, [row])
    a = save_run(root, root / "mapped.csv", normalized, report)
    b = save_run(root, root / "mapped.csv", normalized, report)
    assert a != b
    assert (a / "input_snapshot.csv").read_bytes() == (root / "mapped.csv").read_bytes()
    assert sha256(raw) == before


def test_public_filing_sample_and_historical_unit_regression():
    normalized, report = validate(ROOT / "data/processed/public_financial_green_2024_2025.csv",
                                  ROOT, date(2026, 10, 9))
    assert report["status"] == "checked"
    assert len(normalized) == 34
    balances = [c for c in report["checks"] if c["check"] == "balance_sheet"]
    assert len(balances) == 2 and all(c["residual_cny"] == "0.00" for c in balances)
    actual = {r["canonical_metric"]: Decimal(r["value_cny"]) for r in normalized
              if r["report_period"] == "2024-12-31"}
    # Source controls independently transcribed from 2024 annual report page 7.
    assert actual["revenue"] == Decimal("387411303.84")
    assert actual["net_profit_parent"] == Decimal("56168149.88")
    inputs = list(csv.DictReader((ROOT / "data/processed/green_harmonic_model_inputs.csv").open(encoding="utf-8")))
    by_metric = {r["metric"]: r for r in inputs}
    assert Decimal(by_metric["historical_revenue_bn"]["value"]) * 10**9 == actual["revenue"]
    assert Decimal(by_metric["historical_net_profit_bn"]["value"]) * 10**9 == actual["net_profit_parent"]
    assert actual["net_profit"] != actual["net_profit_parent"]


def test_corrupt_xlsx_recorded_without_losing_fingerprints(tmp_path):
    init_workspace(tmp_path)
    raw = tmp_path / "raw/A_financial/broken.xlsx"
    raw.write_bytes(b"not an xlsx")
    items = inventory(tmp_path)
    assert items["files"][0]["sha256"] == sha256(raw)
    assert "BadZipFile" in items["files"][0]["error"]
