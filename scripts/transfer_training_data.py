"""Split and reassemble official training bytes without changing the Parquet file."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

TRAIN_SHA = "482d4c0387e9da2facd77f722fa465b2d69ec7f119d96933c57761790f4d9519"
PART_BYTES = 200 * 1024 * 1024
BUFFER_BYTES = 8 * 1024 * 1024


def digest(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(BUFFER_BYTES), b""):
            result.update(block)
    return result.hexdigest()


def split(source, out, expected_sha=TRAIN_SHA, part_bytes=PART_BYTES):
    source, out = Path(source), Path(out)
    if not isinstance(part_bytes, int) or not 0 < part_bytes <= PART_BYTES:
        raise ValueError("Part size must be positive and at most 200 MiB")
    if digest(source) != expected_sha:
        raise ValueError("Source SHA-256 differs from the expected original training file")
    if not source.stat().st_size:
        raise ValueError("Empty source")
    out.mkdir(parents=True, exist_ok=False)
    parts, total = [], hashlib.sha256()
    with source.open("rb") as handle:
        while block := handle.read(min(BUFFER_BYTES, part_bytes)):
            name = f"train.parquet.part{len(parts) + 1:03d}"
            current, written = hashlib.sha256(), 0
            with (out / name).open("xb") as destination:
                while block:
                    destination.write(block)
                    current.update(block)
                    total.update(block)
                    written += len(block)
                    if written == part_bytes:
                        break
                    block = handle.read(min(BUFFER_BYTES, part_bytes - written))
            parts.append({"file": name, "bytes": written, "sha256": current.hexdigest()})
    if total.hexdigest() != expected_sha:
        raise ValueError("Source changed during splitting; no completed manifest created")
    manifest = {"format": "original_byte_parts_v1", "original_name": "train.parquet",
                "original_bytes": sum(p["bytes"] for p in parts), "original_sha256": expected_sha,
                "part_bytes": part_bytes, "parts": parts}
    with (out / "parts_manifest.json").open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
    return manifest


def join(parts_dir, output, expected_sha=TRAIN_SHA):
    parts_dir, output = Path(parts_dir), Path(output)
    manifest = json.loads((parts_dir / "parts_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format") != "original_byte_parts_v1" or manifest.get("original_sha256") != expected_sha:
        raise ValueError("Training manifest identity mismatch")
    parts = manifest["parts"]
    names = [p["file"] for p in parts]
    if not names or names != [f"train.parquet.part{i + 1:03d}" for i in range(len(parts))]:
        raise ValueError("Missing, reordered or unsafe part names")
    for part in parts:
        path = parts_dir / part["file"]
        if not 0 < part["bytes"] <= PART_BYTES or path.stat().st_size != part["bytes"] or digest(path) != part["sha256"]:
            raise ValueError("Part size or SHA-256 mismatch")
    if sum(p["bytes"] for p in parts) != manifest["original_bytes"]:
        raise ValueError("Manifest total size mismatch")
    output.parent.mkdir(parents=True, exist_ok=True)
    result = hashlib.sha256()
    with output.open("xb") as destination:
        for part in parts:
            with (parts_dir / part["file"]).open("rb") as source:
                for block in iter(lambda: source.read(BUFFER_BYTES), b""):
                    destination.write(block)
                    result.update(block)
    if result.hexdigest() != expected_sha:
        output.unlink()
        raise ValueError("Reassembled file differs from official original; output removed")
    return {"status": "REASSEMBLED", "bytes": output.stat().st_size, "sha256": result.hexdigest()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    commands = p.add_subparsers(dest="command", required=True)
    splitter = commands.add_parser("split")
    splitter.add_argument("--input", type=Path, required=True)
    splitter.add_argument("--out", type=Path, required=True)
    assembler = commands.add_parser("join")
    assembler.add_argument("--parts", type=Path, required=True)
    assembler.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    value = split(a.input, a.out) if a.command == "split" else join(a.parts, a.out)
    print(json.dumps(value, indent=2))


if __name__ == "__main__":
    main()
