import csv
import hashlib
import json
from pathlib import Path
import pytest
from scripts.resume_csmar_announcements import execute, preview, received_ids


def fixture(root, security_type="P50100", declaration="2025-04-23"):
    for directory in ["raw/C_announcements", "metadata", "reports", "derived/source_review", "scripts"]:
        (root / directory).mkdir(parents=True)
    source = root / "raw/C_announcements/ANN_Security_original.business.json"
    source.write_text(json.dumps({"rows": [{"AnnouncementID": 123, "DeclareDate": declaration,
                                           "SecurityTypeID": security_type}]}), encoding="utf-8")
    checkpoint = [{"path": source.relative_to(root).as_posix(), "bytes": source.stat().st_size,
                   "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}]
    (root / "reports/CODEX_RECEIVED_SOURCE_CHECKPOINT.json").write_text(json.dumps({"files": checkpoint}), encoding="utf-8")
    (root / "scripts/csmar_client.py").write_text("raise RuntimeError('preview must never load client')", encoding="utf-8")
    with (root / "derived/source_review/announcement_resume_jobs.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["job_id", "platform_table", "startTime", "endTime", "id_count", "ids_json"])
        w.writeheader(); w.writerow(dict(job_id="J1", platform_table="ANN_AnnouncementInfo", startTime="2025-01-01",
                                        endTime="2025-12-31", id_count=1, ids_json='["123"]'))


def test_preview_is_offline_and_partial_return_resume_uses_actual_ids(tmp_path):
    fixture(tmp_path)
    assert preview(tmp_path)["pending_ids"] == 1
    response = {"job": {"table": "ANN_AnnouncementInfo"}, "response": {"code": 0, "data": {"previewDatas": [{"AnnouncementID": 123}]}}}
    (tmp_path / "raw/C_announcements/ANN_INFO_2025_001.response.redacted.json").write_text(json.dumps(response), encoding="utf-8")
    assert received_ids(tmp_path) == {"123"}
    result = preview(tmp_path)
    assert result["pending_ids"] == 0 and result["integrity"]["originals_unchanged"]
    assert len(result["integrity"]["new_files"]) == 1
    response["response"]["code"] = -2404
    (tmp_path / "raw/C_announcements/ANN_INFO_2025_001.response.redacted.json").write_text(json.dumps(response), encoding="utf-8")
    assert received_ids(tmp_path) == set() and preview(tmp_path)["pending_ids"] == 1


@pytest.mark.parametrize("name,allowed", [("metadata/verification.json", True),
                                         ("metadata/current_dictionary.json", False)])
def test_working_metadata_update_is_reported_without_exempting_sources(tmp_path, name, allowed):
    fixture(tmp_path)
    path = tmp_path / name
    path.write_text('{"round":1}', encoding="utf-8")
    checkpoint_path = tmp_path / "reports/CODEX_RECEIVED_SOURCE_CHECKPOINT.json"
    checkpoint = json.loads(checkpoint_path.read_text())
    checkpoint["files"].append({"path": name, "bytes": path.stat().st_size,
                                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
    frozen_checkpoint = checkpoint_path.read_bytes()
    path.write_text('{"round":2}', encoding="utf-8")
    if allowed:
        result = preview(tmp_path)
        assert not result["integrity"]["originals_unchanged"]
        assert result["raw_integrity"]["originals_unchanged"]
        assert result["working_metadata_changed"] == [name]
        assert result["pending_ids"] == 1
        # A legitimate metadata update never authorizes changing an old raw file.
        (tmp_path / checkpoint["files"][0]["path"]).write_text('{}', encoding="utf-8")
    with pytest.raises(ValueError, match="Original source missing or changed"):
        preview(tmp_path)
    assert checkpoint_path.read_bytes() == frozen_checkpoint


@pytest.mark.parametrize("security,date", [("P50302", "2025-04-23"), ("P50100", "2026-04-23")])
def test_fund_or_wrong_date_window_is_rejected(tmp_path, security, date):
    fixture(tmp_path, security, date)
    with pytest.raises(ValueError, match="Non-target security"):
        preview(tmp_path)


@pytest.mark.parametrize("quota_code", [-2404, -2512])
def test_quota_error_is_saved_and_stops_before_next_request(tmp_path, quota_code):
    fixture(tmp_path)
    # A local fake client is loaded through the same entry used for acquisition.
    # An error response may contain rows, which must never count as received IDs.
    (tmp_path / "scripts/csmar_client.py").write_text(f'''
import json
from pathlib import Path
class CsmarClient:
    def login(self): pass
    def list_fields(self, table):
        return {{"code": 0, "data": [{{"field": "AnnouncementID"}}]}}
    def _redact(self, data): return data
    def query_raw(self, *args):
        path = Path(__file__).parent / "query_calls.json"
        calls = json.loads(path.read_text()) if path.exists() else []
        calls.append(list(args))
        path.write_text(json.dumps(calls))
        return {{"code": {quota_code}, "data": {{"previewDatas": [{{"AnnouncementID": 123}}]}}}}
''', encoding="utf-8")
    plan = preview(tmp_path)
    plan["jobs"].append({**plan["jobs"][0], "job_id": "J2"})
    result = execute(tmp_path, plan)
    assert len(json.loads((tmp_path / "scripts/query_calls.json").read_text())) == 1
    assert result["receipts"][0]["code"] == quota_code
    assert len(result["receipts"]) == 1 and result["remaining"] == 1
    assert received_ids(tmp_path) == set()
    saved = Path(result["output"]) / "J1.response.redacted.json"
    assert json.loads(saved.read_text())["response"]["code"] == quota_code
