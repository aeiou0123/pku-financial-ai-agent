"""Package executable preparation tools without claiming a real prediction run."""
import argparse
import json
from pathlib import Path
import zipfile

from competition.baseline import official_tools, sha256

ROOT = Path(__file__).resolve().parents[1]


def build(tools, output):
    official_tools(tools)
    paths = ["competition/__init__.py", "competition/baseline.py", "competition/experiment.py",
             "competition/experiment_smoke.py", "competition/package_code.py", "competition/smoke.py",
             "competition/requirements.txt", "competition/README.md", "scripts/launch_technical.py",
             "start_technical.sh", "start_technical.bat", "docs/semifinal/technical_workflow_guide.md",
             "docs/semifinal/delivery_tools.md", "tests/test_competition_baseline.py",
             "tests/test_competition_experiment.py"]
    evidence = ROOT / "docs/semifinal/evidence/technical_workflow_20261003"
    if evidence.is_dir():
        paths.extend(str(p.relative_to(ROOT)) for p in sorted(evidence.iterdir()) if p.is_file())
    files = {name: (ROOT / name).read_bytes() for name in paths}
    files["tools.py"] = Path(tools).read_bytes()
    files["00_先读我.md"] = ("# 技术题执行准备包\n\n先读docs/semifinal/technical_workflow_guide.md，按develop、holdout、finalize运行。\n"
        "本包没有真实赛事Parquet、训练模型、持仓结果或成绩；不是正式07_技术题/code.zip。\n"
        "从已有私人Drive下载原始train.parquet/test.parquet，与tools.py放在同一外部数据目录。\n"
        "附tools.py与原官方SHA-256一致；仅供团队及比赛评审使用，未推送到公共GitHub。\n"
        "Python3.12/3.13，首次启动安装依赖需联网。Linux启动已实测；Windows提供入口，尚未真机验收。\n").encode()
    import hashlib
    files["execution_manifest.json"] = json.dumps({"scope": "PREPARATION_NOT_REAL_SUBMISSION",
        "files_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}}, indent=2).encode()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            entry = zipfile.ZipInfo(name)
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = (0o100755 if name.endswith(".sh") else 0o100644) << 16
            archive.writestr(entry, data)
    return {"path": str(output), "files": len(files), "sha256": sha256(output)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--tools", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(build(a.tools, a.out), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
