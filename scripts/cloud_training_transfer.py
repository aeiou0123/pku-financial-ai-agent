"""Colab SDK transfer: private Drive source -> exact byte parts -> private Drive."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
from pathlib import Path
import tempfile
import uuid

TRAIN_ID = "11AN832isGfPMYirAT37VJBhmNCnNZqFw"
PARENT_ID = "1kkaTaXQg4q8B8THVRY-sUMp0Dd7vvtdx"
TRAIN_SHA = "482d4c0387e9da2facd77f722fa465b2d69ec7f119d96933c57761790f4d9519"
TRAIN_BYTES = 622965149
CHUNK_BYTES = 8 * 1024 * 1024


def hash_file(path, algorithm):
    value = hashlib.new(algorithm)
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK_BYTES), b""):
            value.update(block)
    return value.hexdigest()


def run_transfer(service, *, split_function=None, work_parent=None,
                 downloader_factory=None, uploader_factory=None,
                 train_id=TRAIN_ID, parent_id=PARENT_ID,
                 expected_sha=TRAIN_SHA, expected_bytes=TRAIN_BYTES,
                 part_bytes=200 * 1024 * 1024):
    if split_function is None:
        from scripts.transfer_training_data import split
        split_function = split
    if downloader_factory is None or uploader_factory is None:
        from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
        downloader_factory = downloader_factory or MediaIoBaseDownload
        uploader_factory = uploader_factory or MediaFileUpload
    metadata = service.files().get(fileId=train_id,
        fields="id,name,size,mimeType,capabilities(canDownload)").execute()
    if int(metadata.get("size", -1)) != expected_bytes or not metadata.get("capabilities", {}).get("canDownload"):
        raise ValueError("Original training file size or download permission differs")
    parent = service.files().get(fileId=parent_id, fields="id,mimeType,capabilities(canAddChildren)").execute()
    if parent.get("mimeType") != "application/vnd.google-apps.folder" or not parent.get("capabilities", {}).get("canAddChildren"):
        raise ValueError("Destination is not a writable Drive folder")
    work = Path(tempfile.mkdtemp(prefix="claim2value_cloud_transfer_", dir=work_parent))
    source = work / "train.parquet"
    print("Downloading into the Colab runtime; no download to your computer", flush=True)
    request = service.files().get_media(fileId=train_id)
    with source.open("xb") as handle:
        downloader = downloader_factory(handle, request, chunksize=CHUNK_BYTES)
        done, previous = False, -1
        while not done:
            status, done = downloader.next_chunk(num_retries=3)
            if status:
                percent = int(status.progress() * 100)
                if percent // 10 != previous:
                    previous = percent // 10
                    print(f"Download {percent}%", flush=True)
    if source.stat().st_size != expected_bytes or hash_file(source, "sha256") != expected_sha:
        raise ValueError("Downloaded bytes differ from the official original; nothing written to Drive")
    parts_dir = work / "parts"
    manifest = split_function(source, parts_dir, expected_sha=expected_sha, part_bytes=part_bytes)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"Claim2Value_train_parts_{stamp}_{uuid.uuid4().hex[:8]}"
    folder = service.files().create(body={"name": name, "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]}, fields="id,name,webViewLink").execute()

    def upload(path, mime_type):
        request = service.files().create(body={"name": path.name, "parents": [folder["id"]]},
            media_body=uploader_factory(str(path), mimetype=mime_type, chunksize=CHUNK_BYTES, resumable=True),
            fields="id,name,size,md5Checksum")
        response = None
        while response is None:
            _, response = request.next_chunk(num_retries=3)
        if int(response.get("size", -1)) != path.stat().st_size or response.get("md5Checksum") != hash_file(path, "md5"):
            raise ValueError("Uploaded file byte count/checksum mismatch; transfer remains incomplete")
        return response

    for number, part in enumerate(manifest["parts"], 1):
        response = upload(parts_dir / part["file"], "application/octet-stream")
        part["drive_file_id"] = response["id"]
        print(f"Verified part {number}/{len(manifest['parts'])}", flush=True)
    # The completed manifest appears only after all parts have been uploaded and checked.
    manifest["source_drive_file_id"] = train_id
    manifest["destination_drive_folder_id"] = folder["id"]
    manifest["transfer_scope"] = "ORIGINAL_BYTES_ONLY_NO_MODELING"
    manifest_path = parts_dir / "parts_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest_file = upload(manifest_path, "application/json")
    result = {"status": "COMPLETE", "folder_id": folder["id"], "folder_name": folder["name"],
              "folder_url": folder.get("webViewLink"), "manifest_file_id": manifest_file["id"],
              "parts": len(manifest["parts"]), "original_sha256": expected_sha,
              "raw_original_modified": False, "model_training_run": False}
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return result
