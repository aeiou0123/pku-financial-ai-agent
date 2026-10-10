"""Resume only missing A-share IDs. Default is offline preview; never recrawl core tables."""
import argparse
import csv
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.source_checkpoint import verify_checkpoint


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def received_ids(root):
    ids = set()
    for path in (root / "raw").rglob("*.json"):
        data = read_json(path)
        if not isinstance(data, dict):
            continue  # Acquisition receipts are arrays, not announcement responses.
        if "ANN_AnnouncementInfo" not in path.name and data.get("job", {}).get("table") != "ANN_AnnouncementInfo":
            continue
        rows = data.get("rows", [])
        if isinstance(data.get("response"), dict):
            if data["response"].get("code") != 0:
                continue
            body = data["response"].get("data") or {}
            rows = body.get("previewDatas", []) if isinstance(body, dict) else []
        ids.update(str(r["AnnouncementID"]) for r in rows if r.get("AnnouncementID") is not None)
    return ids


def preview(root):
    original = read_json(root / "reports/CODEX_RECEIVED_SOURCE_CHECKPOINT.json")["files"]
    integrity = verify_checkpoint(root, original)
    if not integrity["originals_unchanged"]:
        raise ValueError("Original source missing or changed")
    done = received_ids(root)
    target_dates = {}
    for path in (root / "raw").rglob("ANN_Security*.business.json"):
        for row in read_json(path).get("rows", []):
            if row.get("SecurityTypeID") == "P50100":
                target_dates[str(row["AnnouncementID"])] = row["DeclareDate"]
    with (root / "derived/codex_review/announcement_resume_jobs.csv").open(encoding="utf-8-sig", newline="") as handle:
        jobs = list(csv.DictReader(handle))
    requests, seen = [], set()
    for job in jobs:
        ids = json.loads(job["ids_json"])
        if job["platform_table"] != "ANN_AnnouncementInfo" or len(ids) > 200 or len(ids) != int(job["id_count"]):
            raise ValueError("Unexpected resume task")
        if seen.intersection(ids) or any(not i.isdigit() for i in ids):
            raise ValueError("Duplicate or invalid ID")
        if any(i not in target_dates or not job["startTime"] <= target_dates[i] <= job["endTime"] for i in ids):
            raise ValueError("Non-target security or incorrect announcement date window")
        seen.update(ids)
        remaining = [i for i in ids if i not in done]
        if remaining:
            requests.append({"job_id": job["job_id"], "table": job["platform_table"],
                             "startTime": job["startTime"], "endTime": job["endTime"], "ids": remaining})
    return {"mode": "OFFLINE_PREVIEW_NO_LOGIN", "jobs": requests, "pending_ids": sum(len(j["ids"]) for j in requests),
            "integrity": integrity, "quota_restore_time": "UNKNOWN", "old_manual_is_current_dictionary": False}


def execute(root, plan):
    # Load the received acquisition client only after explicit --execute.
    spec = importlib.util.spec_from_file_location("received_csmar_client", root / "scripts/csmar_client.py")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    class CaptureClient(module.CsmarClient):
        def _guard(self, payload, op):
            # Caller saves the redacted response before evaluating stop codes.
            return payload
    client = CaptureClient(); client.login()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    out = root / "raw/B_filings/resume" / stamp
    out.mkdir(parents=True, exist_ok=False)
    receipts = []
    fields = client.list_fields("ANN_AnnouncementInfo")
    (out / "fields.response.redacted.json").write_text(json.dumps(client._redact(fields), ensure_ascii=False, indent=2), encoding="utf-8")
    columns = [r["field"] for r in (fields.get("data") or []) if isinstance(r, dict) and r.get("field")]
    if fields.get("code") != 0 or "AnnouncementID" not in columns:
        raise ValueError("Current fields unavailable; no data request made")
    for job in plan["jobs"]:
        wanted = [i for i in job["ids"] if i not in received_ids(root)]
        if not wanted:
            continue
        payload = client.query_raw(columns, "AnnouncementID in (" + ",".join(wanted) + ")",
                                   job["table"], job["startTime"], job["endTime"])
        body = payload.get("data") or {}
        rows = body.get("previewDatas", []) if isinstance(body, dict) else []
        returned = {str(r["AnnouncementID"]) for r in rows if r.get("AnnouncementID") is not None}
        record = {"job": job, "requested_ids": wanted, "response": client._redact(payload),
                  "capture_kind": "parsed_server_business_response_redacted_not_HTTP_bytes"}
        path = out / (job["job_id"] + ".response.redacted.json")
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        unexpected = sorted(returned - set(wanted))
        receipt = {"job_id": job["job_id"], "code": payload.get("code"), "requested": len(wanted),
                   "returned_ids": sorted(returned), "missing_ids": sorted(set(wanted) - returned),
                   "unexpected_ids": unexpected, "source": path.relative_to(root).as_posix()}
        receipts.append(receipt)
        (out / "receipt.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=2), encoding="utf-8")
        if payload.get("code") != 0 or unexpected:
            break  # Includes -2404 and -2512. No quota/session workaround.
    return {"mode": "EXECUTED_SERIAL", "output": str(out), "receipts": receipts,
            "remaining": preview(root)["pending_ids"], "current_full_definitions_obtained": False}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT / "work/csmar_handoff/20261009")
    p.add_argument("--execute", action="store_true", help="Only use after quota is available; logs in once")
    p.add_argument("--out", type=Path)
    a = p.parse_args(); root = a.root.resolve(); plan = preview(root)
    result = execute(root, plan) if a.execute else plan
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        with a.out.open("x", encoding="utf-8") as f: json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps({"mode": result["mode"], "jobs": len(plan["jobs"]), "pending_ids": result.get("pending_ids", result.get("remaining"))}, ensure_ascii=False))
