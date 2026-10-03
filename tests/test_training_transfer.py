import hashlib
import json
import pytest
from scripts.transfer_training_data import split, join


@pytest.mark.parametrize("count", [1, 16, 17, 48, 51])
def test_exact_bytes_round_trip_and_no_overwrite(tmp_path, count):
    data = bytes(range(count));sha = hashlib.sha256(data).hexdigest()
    source = tmp_path / "source.parquet";source.write_bytes(data)
    parts = tmp_path / "parts";output = tmp_path / "train.parquet"
    manifest = split(source, parts, expected_sha=sha, part_bytes=16)
    assert manifest["original_bytes"] == count
    assert all(p["bytes"] <= 16 for p in manifest["parts"])
    assert join(parts, output, expected_sha=sha)["sha256"] == sha
    assert output.read_bytes() == source.read_bytes() == data
    with pytest.raises(FileExistsError):
        split(source, parts, expected_sha=sha, part_bytes=16)
    with pytest.raises(FileExistsError):
        join(parts, output, expected_sha=sha)


def test_changed_part_is_rejected_before_creating_output(tmp_path):
    source = tmp_path / "source";source.write_bytes(b"abcdefghijklmnopqrstuv")
    sha = hashlib.sha256(source.read_bytes()).hexdigest();parts = tmp_path / "parts"
    split(source, parts, expected_sha=sha, part_bytes=10)
    (parts / "train.parquet.part002").write_bytes(b"changed")
    with pytest.raises(ValueError, match="mismatch"):
        join(parts, tmp_path / "output", expected_sha=sha)
    assert not (tmp_path / "output").exists()


def test_wrong_original_does_not_create_parts_directory(tmp_path):
    source = tmp_path / "source";source.write_bytes(b"wrong")
    with pytest.raises(ValueError, match="Source SHA"):
        split(source, tmp_path / "parts")
    assert not (tmp_path / "parts").exists()


def test_reordered_manifest_is_rejected(tmp_path):
    source = tmp_path / "source";source.write_bytes(bytes(range(30)))
    sha = hashlib.sha256(source.read_bytes()).hexdigest();parts=tmp_path/'parts'
    manifest=split(source,parts,expected_sha=sha,part_bytes=10)
    manifest['parts'].reverse();(parts/'parts_manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='reordered'):
        join(parts,tmp_path/'output',expected_sha=sha)
