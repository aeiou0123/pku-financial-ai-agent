"""Verify immutable originals while inventorying legitimate additions separately."""
import hashlib
from pathlib import Path


def verify_checkpoint(root: Path, original_files: list[dict], directories=("raw", "metadata")) -> dict:
    expected = {r["path"]: r for r in original_files}
    if len(expected) != len(original_files):
        raise ValueError("Duplicate checkpoint path")
    changed, missing = [], []
    for name, item in expected.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("Checkpoint path outside source root")
        if not path.is_file():
            missing.append(name)
        elif path.stat().st_size != item["bytes"] or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            changed.append(name)
    added = []
    for directory in directories:
        for path in sorted((root / directory).rglob("*")):
            if path.is_file() and path.relative_to(root).as_posix() not in expected:
                added.append({"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size,
                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return {"original_files": len(expected), "changed": changed, "missing": missing,
            "new_files": added, "originals_unchanged": not (changed or missing)}
