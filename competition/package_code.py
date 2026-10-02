"""Package actual checked predictions and the exact generating code/model."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import zipfile
from competition.baseline import sha256, official_tools, verify_data

ROOT = Path(__file__).resolve().parents[1]
REPRODUCE = '''import argparse,json,subprocess,sys,hashlib
from pathlib import Path
root=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();config=json.loads((root/'run_summary.json').read_text())
subprocess.run([sys.executable,'-m','competition.baseline','predict','--tools',str(root/'tools.py'),'--test',str(a.data.resolve()/'test.parquet'),'--model',str(root/'model.json'),'--hold-bonus',str(config['hold_bonus']),'--out',str(a.out.resolve())],cwd=root,check=True)
actual=hashlib.sha256((a.out/'submission.csv').read_bytes()).hexdigest()
if actual!=config['holdings_sha256']:raise SystemExit('Reproduction mismatch')
print('REPRODUCED: CSV SHA-256 matches the original run')
'''


def package(run, tools_path, test_path, output, ai_tools):
    run, output = Path(run), Path(output)
    if not ai_tools.strip():
        raise ValueError("Record the AI tools actually used")
    summary = json.loads((run / "run_summary.json").read_text())
    if summary.get("command") != "predict" or summary.get("status") != "COMPLETE" or summary.get("submission_check", {}).get("status") != "VALID":
        raise ValueError("Only a completed, officially checked real prediction run can be packaged")
    for file, key in [("submission.csv", "holdings_sha256"), ("model.json", "model_sha256")]:
        if sha256(run / file) != summary.get(key):
            raise ValueError(f"{file} changed after the recorded run")
    if sha256(ROOT / "competition/baseline.py") != summary.get("code_sha256"):
        raise ValueError("Generating code differs from the run; reproduce with this version before packaging")
    official = official_tools(tools_path)
    verify_data(test_path, "test", official)
    checked = official.check(run / "submission.csv", test_path)
    if checked.get("status") != "VALID":
        raise ValueError("Fresh official check failed")
    files = {name: (ROOT / name).read_bytes() for name in ["competition/__init__.py", "competition/baseline.py", "competition/requirements.txt", "competition/README.md"]}
    files.update({name: (run / name).read_bytes() for name in ["model.json", "run_summary.json"]})
    files["tools.py"] = Path(tools_path).read_bytes()
    files["reproduce.py"] = REPRODUCE.encode()
    readme = """# 技术题复现包
安装Python3.12/3.13，执行 python -m pip install -r competition/requirements.txt。
在本目录执行 python reproduce.py --data <含官方test.parquet的目录> --out <不存在的新目录>。
包含实际模型权重、生成代码、运行摘要、官方工具；复现完成会比对原持仓CSV指纹。
训练命令和时间划分见competition/README.md，模型JSON保留训练区间、正则参数与确定性种子。
复现包不含原始训练/测试数据，不包含技术题报告PPT；正式submission.csv需另放07_技术题。
本包创建前已重新执行官方check；格式有效不等于成绩高或研究设计正确。
""" + "\n实际使用的AI工具：" + ai_tools.strip() + "\n"
    files["运行说明.md"] = readme.encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            archive.writestr(name, data)
    return {"path": str(output), "sha256": sha256(output), "official_check": checked}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--tools", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--ai-tools", required=True)
    args = parser.parse_args()
    print(json.dumps(package(args.run, args.tools, args.test, args.out, args.ai_tools), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
