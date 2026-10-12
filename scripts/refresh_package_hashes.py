# -*- coding: utf-8 -*-
"""Regenerate 05_技术证据/提交包成员哈希.json over the submission package."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "deliverables/semifinal_20261012/饮水思源_Claim2Value"
MANIFEST = PACKAGE / "05_技术证据/提交包成员哈希.json"


def main():
    files = {}
    for path in sorted(PACKAGE.rglob("*")):
        if not path.is_file() or path == MANIFEST or "__pycache__" in path.parts:
            continue
        relative = str(path.relative_to(PACKAGE)).replace("\\", "/")
        files[relative] = {"bytes": path.stat().st_size,
                           "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    MANIFEST.write_text(json.dumps(
        {"scope": "All package files except this manifest itself; total ZIP hash is external",
         "files": files}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"files": len(files), "manifest": str(MANIFEST.relative_to(ROOT))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
