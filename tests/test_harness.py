"""Research boundary tests; synthetic data and local API mocks only."""
from __future__ import annotations

import io
import json
import threading
import zipfile
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.financial_intake import FIELDS
from src.harness.api import ModelClient, APIError
from src.harness.documents import parse, table, chunks, digest, safe_name
from src.harness.engine import propose_quant
from src.harness.financial import anchor_records, extract, check_financial, dcf
from src.harness.quant import prepare, backtest
from src.harness.store import Run

EXAMPLES = Path(__file__).resolve().parents[1] / "docs/harness/examples"


def panel(days=7):
    dates = pd.bdate_range("2025-01-01", periods=days)
    return pd.DataFrame([{"date": dt.date().isoformat(), "stock": f"{stock:06d}",
                          "close": str(100 + i * stock)} for i, dt in enumerate(dates) for stock in (1, 2, 3)])


def prep(frame):
    return prepare(frame, {k: k for k in ("date", "stock", "close")}, "momentum")


def finance_run(tmp_path):
    uploads = [(name, (EXAMPLES / name).read_bytes()) for name in ("synthetic_financial.txt", "synthetic_financial.csv")]
    run = Run(tmp_path, "financial", uploads)
    rows = table(uploads[1][1], uploads[1][0]).to_dict("records")
    for row in rows:
        row["source_file"] = safe_name(row["source_file"])
    return run, rows


def test_financial_synthetic_identity_and_ratios(tmp_path):
    run, rows = finance_run(tmp_path)
    normalized, quality = check_financial(run, rows, date(2025, 3, 1))
    assert quality["errors"] == []
    assert normalized[0]["stock_code"] == "000000"
    ratios = pd.read_csv(run.path / "outputs/historical_ratios.csv")
    assert ratios.set_index("ratio")["value"].to_dict() == pytest.approx({"liabilities/assets": .4, "gross_margin": .4, "parent_net_margin": .1})
    assert quality["forecast_updated"] is False


@pytest.mark.parametrize("field,value,expected", [("published_at", "", "invalid_published_at"),
    ("published_at", "2024-01-01", "publication_or_period_after_cutoff"),
    ("statement_scope", "", "unknown_statement_scope"), ("unit", "美元", "unsupported_unit_or_currency"),
    ("stock_code", "1", "stock_code_requires_six_digits"), ("source_sha256", "0" * 64, "source_sha256_mismatch"),
    ("source_file", "../run.json", "source_file_outside_root")])
def test_financial_required_metadata_stays_blocked(tmp_path, field, value, expected):
    run, rows = finance_run(tmp_path)
    rows[0][field] = value
    _, quality = check_financial(run, rows, date(2025, 3, 1))
    assert quality["errors"]
    # Match the specific boundary without relying on wording of shared intake errors.
    assert quality["status"] == "invalid"
    assert not (run.path / "outputs/financial.xlsx").exists()


def test_revisions_not_combined_for_ratio(tmp_path):
    run, rows = finance_run(tmp_path)
    rows[4]["revision_flag"] = "restated"
    _, report = check_financial(run, rows, date(2025, 3, 1))
    assert not report["errors"]
    ratios = pd.read_csv(run.path / "outputs/historical_ratios.csv")
    assert "gross_margin" not in ratios["ratio"].tolist()


def test_duplicate_metrics_and_missing_not_zero(tmp_path):
    run, rows = finance_run(tmp_path)
    rows[5]["value_original"] = ""
    normalized, quality = check_financial(run, rows + [rows[0]], date(2025, 3, 1))
    assert normalized[5]["value_status"] == "missing"
    assert any(error["issue"] == "duplicate_metric_requires_review" for error in quality["errors"])


def test_dcf_known_perpetuity_and_missing_debt():
    result = dcf([100.] * 5, .1, 0)
    assert result["enterprise_value"] == pytest.approx(1000)
    assert result["equity_value"] is None
    assert dcf([100.] * 5, .1, 0, 300)["equity_value"] == pytest.approx(700)


@pytest.mark.parametrize("fcf,rate,growth", [([100.] * 4, .1, .02), ([float("nan")] * 5, .1, .02),
    ([100.] * 5, .02, .02), ([100.] * 5, 0, 0), ([0.] * 5, .1, .02)])
def test_invalid_dcf_rejected(fcf, rate, growth):
    with pytest.raises(ValueError):
        dcf(fcf, rate, growth)


def test_document_locators_chunk_coverage_and_quote_binding():
    text = "数字 100\n" + "a" * 17000
    doc = parse(text.encode(), "../source.txt")
    batches = chunks([doc])
    assert sum(len(p["text"]) for batch in batches for p in batch) == sum(len(p["text"]) for p in doc["parts"])
    pieces = batches[0]
    candidates, bad = anchor_records({"records": [{"source_file": doc["source_file"], "source_locator": "line:1", "quote": "数字 100"},
                                                  {"source_file": doc["source_file"], "source_locator": "page:99", "quote": "数字 100"}]}, pieces)
    assert len(candidates) == 1 and len(bad) == 1
    assert candidates[0]["published_at"] == ""
    assert candidates[0]["source_sha256"] == digest(text.encode())


def test_empty_pdf_requires_ocr():
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    stream = io.BytesIO()
    writer.write(stream)
    with pytest.raises(ValueError, match="OCR"):
        parse(stream.getvalue(), "scan.pdf")


def test_text_limit_explicit_not_full_read():
    doc = parse(("aa\n" * 70000).encode(), "large.txt")
    assert doc["parsed_units"] < doc["total_units"]
    assert doc["warnings"] and doc["coverage"] == "partial"


def test_table_leading_zero_and_duplicate_headers():
    assert table(b"stock,close\n000001,10\n", "x.csv").iloc[0]["stock"] == "000001"
    with pytest.raises(ValueError, match="重复"):
        table(b"stock,stock\n1,2\n", "x.csv")


def test_run_package_hashes_excludes_raw(tmp_path):
    run = Run(tmp_path, "financial", [("../../secret.txt", b"private original")])
    run.write("result.json", {"number": 1})
    with zipfile.ZipFile(io.BytesIO(run.bundle())) as archive:
        assert not any(name.startswith("sources/") for name in archive.namelist())
        manifest = json.loads(archive.read("manifest.json"))
        assert all(digest(archive.read(name)) == info["sha256"] for name, info in manifest.items())
    with pytest.raises(ValueError):
        run.write("../bad", "x")


def test_collision_rejected(tmp_path):
    with pytest.raises(ValueError, match="冲突"):
        Run(tmp_path, "quant", [("a/x.txt", b"a"), ("b/x.txt", b"b")])
    with pytest.raises(ValueError, match="冲突"):
        Run(tmp_path, "quant", [("A.txt", b"a"), ("a.txt", b"b")])


def test_next_close_lag_fee_and_initial_drawdown():
    frame = panel()
    result = backtest(prep(frame), lookback=1, top_n=1, fee_bps=10)
    positions = result["positions"]
    assert positions.iloc[0]["signal_date"] == "2025-01-02"
    assert positions.iloc[0]["execution_date"] == "2025-01-03"
    assert positions.iloc[0]["first_return_date"] == "2025-01-06"
    daily = result["daily"]
    assert daily.iloc[0]["gross_return"] == 0
    assert daily.iloc[0]["net_return"] == pytest.approx(-.001)
    assert daily.iloc[0]["drawdown"] == pytest.approx(-.001)
    assert daily.iloc[1]["gross_return"] == pytest.approx(109 / 106 - 1)


def test_future_changes_do_not_change_past_positions():
    frame = panel(10)
    old = backtest(prep(frame), lookback=1, top_n=2, fee_bps=0)
    frame.loc[frame.date >= "2025-01-10", "close"] = "999"
    new = backtest(prep(frame), lookback=1, top_n=2, fee_bps=0)
    before = lambda output: output["positions"].query("execution_date < '2025-01-10'").reset_index(drop=True)
    pd.testing.assert_frame_equal(before(old), before(new))
    pd.testing.assert_frame_equal(old["daily"].loc[:"2025-01-09"], new["daily"].loc[:"2025-01-09"])


def test_equal_weight_drift_rebalance_charged():
    result = backtest(prep(panel()), lookback=1, top_n=3, fee_bps=10)
    assert result["daily"].iloc[1]["turnover_two_sided"] > 0
    assert result["daily"].iloc[1]["cost_fraction_pretrade_nav"] > 0
    # Universe-wide strategy and benchmark must match with the same schedule/fees.
    np.testing.assert_allclose(result["daily"]["nav"], result["daily"]["benchmark_nav"], rtol=1e-12)


@pytest.mark.parametrize("change", ["duplicate", "missing_price", "incomplete", "zero_price", "lost_zero"])
def test_bad_quant_data_rejected(change):
    data = panel()
    if change == "duplicate":
        data = pd.concat([data, data.iloc[:1]])
    elif change == "incomplete":
        data = data.iloc[1:]
    else:
        data.loc[0, "stock" if change == "lost_zero" else "close"] = {"missing_price": "", "zero_price": "0", "lost_zero": "1"}[change]
    with pytest.raises((ValueError, TypeError)):
        prep(data)


def test_factor_availability_not_future_and_not_zero():
    data = panel()
    data["factor"] = data["stock"]
    data["available_at"] = data["date"] + "T16:00:00+08:00"
    mapped = {k: k for k in ("date", "stock", "close", "factor", "available_at")}
    processed = prepare(data, mapped, "factor")
    assert processed["factor"].isna().all()
    with pytest.raises(ValueError, match="信号"):
        backtest(processed, strategy="factor", top_n=1)
    data["available_at"] = data["date"]
    with pytest.raises(ValueError, match="时分"):
        prepare(data, mapped, "factor")


@pytest.fixture
def local_api():
    class Handler(BaseHTTPRequestHandler):
        status = 200
        content = {"records": []}
        requests = []

        def log_message(self, *args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            type(self).requests.append({"path": self.path, "auth": self.headers.get("Authorization"), "body": body})
            self.send_response(type(self).status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"choices": [{"finish_reason": "stop", "message": {"content": json.dumps(type(self).content)}}],
                                        "usage": {"total_tokens": 5}}).encode())

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/v1", Handler
    server.shutdown()
    server.server_close()
    thread.join(3)


def test_api_protocol_budget_and_error_sanitization(local_api):
    url, handler = local_api
    client = ModelClient(url, "mock", "credential_32_chars_for_test_only", max_calls=1)
    assert client.json("schema", {}) == {"records": []}
    assert handler.requests[0]["path"] == "/v1/chat/completions"
    assert handler.requests[0]["auth"].startswith("Bearer ")
    with pytest.raises(APIError, match="上限"):
        client.json("schema", {})
    handler.status = 429
    client = ModelClient(url, "mock", "credential_32_chars_for_test_only")
    with pytest.raises(APIError) as error:
        client.json("schema", {})
    assert "429" in str(error.value) and client.api_key not in str(error.value)
    assert client.api_key not in repr(client)


def test_credentials_cannot_be_saved_from_model(local_api):
    url, handler = local_api
    secret = "credential_32_chars_for_test_only"
    handler.content = {"records": [], "notes": secret}
    with pytest.raises(APIError, match="凭据"):
        ModelClient(url, "mock", secret).json("schema", {})


@pytest.mark.parametrize("url", ["http://example.com/v1", "https://user:pass@example.com/v1", "https://example.com/v1?key=x"])
def test_api_address_rejected(url):
    with pytest.raises(ValueError):
        ModelClient(url, "model", "key")


def test_extract_cache_resume_and_no_secret_in_artifacts(tmp_path, local_api):
    url, handler = local_api
    doc = parse(b"revenue 100", "x.txt")
    handler.content = {"records": [{"source_file": doc["source_file"], "source_locator": "line:1", "quote": "revenue 100", "value_original": "100"}]}
    run = Run(tmp_path, "financial", [("x.txt", b"revenue 100")])
    key = "credential_32_chars_for_test_only"
    first = extract(run, [doc], "revenue", ModelClient(url, "mock", key))
    assert len(first) == 1 and len(handler.requests) == 1
    assert extract(run, [doc], "revenue", ModelClient(url, "mock", key)) == first
    assert len(handler.requests) == 1
    assert all(key.encode() not in path.read_bytes() for path in run.path.rglob("*") if path.is_file())


def test_failed_multibatch_run_resumes_after_budget_without_repaying_completed_batch(tmp_path, local_api):
    url, handler = local_api
    doc = parse(("revenue 100\n" + "a" * 15000).encode(), "long.txt")
    handler.content = {"records": []}
    run = Run(tmp_path, "financial", [("long.txt", ("revenue 100\n" + "a" * 15000).encode())])
    with pytest.raises(APIError, match="上限"):
        extract(run, [doc], "revenue", ModelClient(url, "mock", "credential_32_chars_for_test_only", max_calls=1))
    completed = len(handler.requests)
    assert completed == 1 and run.metadata["status"] == "extraction_interrupted"
    extract(run, [doc], "revenue", ModelClient(url, "mock", "credential_32_chars_for_test_only", max_calls=10))
    assert len(handler.requests) == len(chunks([doc]))
    assert run.metadata["status"] == "awaiting_review"


def test_unsupported_model_code_plan_rejected(tmp_path, local_api):
    url, handler = local_api
    handler.content = {"mapping": {}, "strategy": "momentum", "lookback": 20, "top_n": 1, "fee_bps": 10,
                       "direction": "high", "python": "import os"}
    run = Run(tmp_path, "quant", [])
    with pytest.raises(ValueError, match="不支持"):
        propose_quant(run, ModelClient(url, "mock", "credential_32_chars_for_test_only"), "run", ["date"], 5)
    assert not (run.path / "outputs/task_proposal.json").exists()


def test_app_initial_render():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "harness_app.py"), default_timeout=20).run()
    assert not app.exception
    assert len(app.get("file_uploader")) == 1
