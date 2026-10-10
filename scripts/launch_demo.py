"""Create a local environment once, then launch the offline demo."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.version_info < (3, 12):
        raise SystemExit("Python 3.12+ is required; Python 3.12 is the verified version.")
    os.environ["PYTHONUTF8"] = "1"
    os.chdir(ROOT)
    environment = ROOT / ".venv-demo"
    interpreter = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not interpreter.exists():
        subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
    expected = {}
    for line in (ROOT / "requirements-demo.txt").read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            package, version = line.strip().split("==")
            expected[package] = version
    probe = "import importlib.metadata as m; import streamlit,openpyxl,numpy,pandas,pyarrow; expected=" + repr(expected) + "; assert all(m.version(k)==v for k,v in expected.items())"
    checked = subprocess.run([str(interpreter), "-c", probe], capture_output=True)
    if checked.returncode:
        subprocess.run([str(interpreter), "-m", "pip", "install", "-r", str(ROOT / "requirements-demo.txt")], check=True)
    command = [str(interpreter), "-m", "streamlit", "run", str(ROOT / "app.py"),
               "--server.address", "127.0.0.1", "--server.port", "8501", "--server.headless", "true",
               "--browser.gatherUsageStats", "false"]
    print("Open http://127.0.0.1:8501 ; press Ctrl+C to stop.", flush=True)
    try:
        return subprocess.call(command)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
