import json
from pathlib import Path

from src.financial_evidence import company_records, historical_report, presentation_rows, load_snapshot
from src.source_checkpoint import verify_checkpoint


def test_reviewed_sample_preserves_availability_and_does_not_calibrate():
    snapshot = load_snapshot()
    green = company_records(snapshot, "688017")
    assert len(green) == 34
    assert len(company_records(snapshot, "688017", "2024-12-31")) == 17
    assert {r["published_at"] for r in green} == {"2026-04-23"}
    assert not company_records(snapshot, "002472")
    assert not company_records(snapshot, "688160")
    report = historical_report(snapshot, "688017", green)
    assert report["forecast_updated"] is False
    assert report["valuation_generated"] is False
    revenue = next(r for r in green if r["canonical_metric"] == "revenue" and r["report_period"] == "2024-12-31")
    assert revenue["value_cny"] == "387411303.84"
    assert presentation_rows([revenue])[0]["金额（百万元）"] == "387.41130384"


def test_addition_is_distinct_from_tampering_and_missing_original(tmp_path):
    import hashlib
    (tmp_path / "raw").mkdir()
    original = tmp_path / "raw/original.json"; original.write_bytes(b"original")
    checkpoint = [{"path": "raw/original.json", "bytes": 8, "sha256": hashlib.sha256(b"original").hexdigest()}]
    (tmp_path / "raw/new.json").write_bytes(b"new")
    check = verify_checkpoint(tmp_path, checkpoint)
    assert check["originals_unchanged"] and [r["path"] for r in check["new_files"]] == ["raw/new.json"]
    original.write_bytes(b"modified")
    assert verify_checkpoint(tmp_path, checkpoint)["changed"] == ["raw/original.json"]
    original.unlink()
    assert verify_checkpoint(tmp_path, checkpoint)["missing"] == ["raw/original.json"]


def test_history_page_without_vendor_data_is_usable():
    from streamlit.testing.v1 import AppTest
    root = Path(__file__).resolve().parents[1]
    app = AppTest.from_file(str(root / "app.py")).run()
    app.radio(key="review_mode").set_value("历史财务核验").run()
    assert not app.exception
    assert len(app.table[0].value) == 34
    app.selectbox(key="history_company").set_value("步科股份").run()
    assert not app.exception
    assert any("尚无完成原页核对" in i.value for i in app.info)
    assert not any("财务三情景" in i.value for i in app.subheader)
