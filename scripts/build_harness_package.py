"""Build an allowlisted research-desk deployment, excluding private data."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    paths = [ROOT / name for name in ("harness_app.py", "start_harness.bat", "start_harness.sh", "requirements-harness.txt",
                                      ".streamlit/config.toml",
                                      "src/review_ui.py", "src/financial_intake.py", "src/state_verifier.py",
                                      "src/quantity_text.py", "scripts/launch_harness.py")]
    paths += sorted((ROOT / "src/harness").glob("*.py"))
    # Only the usage-facing docs ship; development notes stay in the repository.
    usage_docs = {"README.md", "getting_started.md", "industry_workflow.md",
                  "model-connections.md", "announcement_catalog.md"}
    harness_docs = ROOT / "docs/harness"
    for path in sorted(harness_docs.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(harness_docs)
        if path.name in usage_docs or "examples" in relative.parts:
            paths.append(path)
    manifest = {str(p.relative_to(ROOT)).replace("\\", "/"): {"bytes": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths}
    destination = ROOT / "deliverables/harness_20261010"
    destination.mkdir(parents=True, exist_ok=True)
    archive_path = destination / "Claim2Value_研究工作台.zip"
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, str(path.relative_to(ROOT)).replace("\\", "/"))
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        saved = json.loads(archive.read("manifest.json"))
        assert all(hashlib.sha256(archive.read(name)).hexdigest() == meta["sha256"] for name, meta in saved.items())
    receipt = {"path": str(archive_path), "members": len(manifest) + 1, "bytes": archive_path.stat().st_size,
               "sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(), "member_hashes": "passed",
               "original_uploads_included": False, "real_api_verified_by_automated_checks": False,
               "provider_configuration_record": "docs/harness/model-connections.md",
               "getting_started_record": "docs/harness/getting_started.md",
               "industry_workflow_record": "docs/harness/industry_workflow.md",
               "real_case_review_record": "docs/harness/real-cases/README.md",
               "real_case_model_boundary": "Kimi industry and financial extraction tested; 20/24 financial targets matched before operator correction and 4-row supplementation; automated checks are not human trials"}
    (destination / "package_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
