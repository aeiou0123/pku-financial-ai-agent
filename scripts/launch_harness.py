"""Create an isolated harness environment, then start the local research desk."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.version_info < (3, 12):
        raise SystemExit("Python 3.12+ required; verified on Python 3.12.")
    os.environ["PYTHONUTF8"] = "1"
    os.chdir(ROOT)
    env = ROOT / ".venv-harness"
    interpreter = env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not interpreter.exists():
        subprocess.run([sys.executable, "-m", "venv", str(env)], check=True)
    expected = dict(line.split("==") for line in (ROOT / "requirements-harness.txt").read_text().splitlines() if line.strip())
    probe = "import importlib.metadata as m; import streamlit,openpyxl,numpy,pandas,pyarrow,pypdf; expected=" + repr(expected) + "; assert all(m.version(k)==v for k,v in expected.items())"
    if subprocess.run([str(interpreter), "-c", probe], capture_output=True).returncode:
        subprocess.run([str(interpreter), "-m", "pip", "install", "-r", str(ROOT / "requirements-harness.txt")], check=True)
    port = str(int(os.environ.get("C2V_PORT", "8510")))
    print(f"Open http://127.0.0.1:{port} ; Ctrl+C to stop.", flush=True)
    try:
        return subprocess.call([str(interpreter), "-m", "streamlit", "run", str(ROOT / "harness_app.py"),
                                "--server.address", "127.0.0.1", "--server.port", port, "--server.headless", "true",
                                "--browser.gatherUsageStats", "false", "--server.maxUploadSize", "20"])
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
