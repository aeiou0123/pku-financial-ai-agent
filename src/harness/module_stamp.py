"""Record source bytes at import time so app refreshes only genuinely changed tools."""
import hashlib
from pathlib import Path


def source_stamp(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
