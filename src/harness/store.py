"""Private run snapshots and output-only packages with manifests."""
from __future__ import annotations

from .module_stamp import source_stamp
_c2v_loaded_source_hash = source_stamp(__file__)

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .documents import digest, safe_name, MAX_TOTAL_BYTES, MAX_BYTES


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Run:
    def __init__(self, root: Path, workflow: str, uploads: list[tuple[str, bytes]]):
        if len(uploads) > 10 or sum(len(data) for _, data in uploads) > MAX_TOTAL_BYTES:
            raise ValueError("每次最多 10 个文件，总量 60 MB。")
        if any(not data or len(data) > MAX_BYTES for _, data in uploads):
            raise ValueError("文件为空或超过 20 MB。")
        names = [safe_name(name) for name, _ in uploads]
        if len({name.casefold().rstrip(". ") for name in names}) != len(names):
            raise ValueError("文件名发生冲突，请重命名后上传。")
        self.path = root / (datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid4().hex[:10])
        (self.path / "sources").mkdir(parents=True)
        (self.path / "outputs").mkdir()
        self.metadata = {"id": self.path.name, "workflow": workflow, "created_at": now(),
                         "status": "created", "inputs": []}
        for (name, data), stored in zip(uploads, names):
            (self.path / "sources" / stored).write_bytes(data)
            self.metadata["inputs"].append({"name": name, "source_file": stored,
                                           "bytes": len(data), "sha256": digest(data)})
        self.event("created")

    def event(self, stage: str, **values):
        # Callers pass only structured local results, never credentials/provider bodies.
        self.metadata["status"] = stage
        (self.path / "run.json").write_text(json.dumps(self.metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        with (self.path / "events.jsonl").open("a", encoding="utf-8") as file:
            file.write(json.dumps({"at": now(), "stage": stage, **values}, ensure_ascii=False) + "\n")

    def write(self, name: str, value) -> Path:
        if Path(name).name != name or "\\" in name:
            raise ValueError("Output must be a filename")
        path = self.path / "outputs" / name
        if isinstance(value, bytes):
            path.write_bytes(value)
        elif isinstance(value, str):
            path.write_text(value, encoding="utf-8")
        else:
            path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        return path

    def bundle(self) -> bytes:
        """Do not distribute uploaded licensed originals or API extraction cache."""
        files = list((self.path / "outputs").glob("*")) + [self.path / "run.json", self.path / "events.jsonl"]
        manifest = {p.relative_to(self.path).as_posix(): {"sha256": digest(p.read_bytes()), "bytes": p.stat().st_size}
                    for p in files if p.is_file()}
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in files:
                if path.is_file():
                    archive.write(path, path.relative_to(self.path).as_posix())
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        return out.getvalue()
