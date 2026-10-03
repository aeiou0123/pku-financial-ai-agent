"""Create an isolated environment and run one chronological technical-task phase."""
import argparse
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("phase", choices=["develop", "holdout", "finalize", "smoke"])
    p.add_argument("--data", type=Path, required=True, help="Directory containing the original official files")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--ai-tools", default="")
    p.add_argument("--skip-install", action="store_true", help="Use only after this isolated environment is already installed")
    a = p.parse_args()
    if sys.version_info[:2] not in {(3, 12), (3, 13)}:
        p.error("Use Python 3.12 or 3.13")
    if a.resume and a.phase != "develop":
        p.error("--resume is available only for completed development boundaries")
    if a.phase == "finalize" and not a.ai_tools.strip():
        p.error("finalize requires --ai-tools with the tools actually used")
    required = ["tools.py"] + (["train.parquet"] if a.phase != "smoke" else [])
    if a.phase == "finalize":
        required.append("test.parquet")
    for name in required:
        if not (a.data / name).is_file():
            p.error(f"Missing official input: {name}")
    env = ROOT / ".venv-competition"
    interpreter = env / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not interpreter.exists():
        venv.EnvBuilder(with_pip=True).create(env)
    if not a.skip_install:
        subprocess.run([str(interpreter), "-m", "pip", "install", "-r", str(ROOT / "competition/requirements.txt")], check=True)
    args = [str(interpreter), "-m", "competition.experiment_smoke" if a.phase == "smoke" else "competition.experiment"]
    if a.phase != "smoke":
        args.extend([a.phase, "--train", str((a.data / "train.parquet").resolve())])
    args.extend(["--tools", str((a.data / "tools.py").resolve()), "--out", str(a.out.resolve())])
    if a.phase == "finalize":
        args.extend(["--test", str((a.data / "test.parquet").resolve()), "--ai-tools", a.ai_tools])
    if a.resume:
        args.append("--resume")
    subprocess.run(args, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
