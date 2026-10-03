"""Build a minimal reviewer deployment ZIP, excluding credentials and raw PDFs."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DATA = ["local_demo_fixture.json", "claim_bank_filled.json", "parameter_table_filled.csv",
        "tech_to_economics_ontology.json", "tech_to_economics_ontology_shuanghuan.json",
        "industry_data_summary.csv", "competitor_market_share.csv",
        "green_harmonic_model_inputs.csv", "shuanghuan_model_inputs.csv"]
GUIDE = """# Claim2Value 本地部署

安装Python，推荐本轮实测的3.12。Windows双击start_demo.bat，Linux执行bash start.sh。
首次需要联网安装依赖；后续依赖已齐备且版本匹配时不重复安装，可离线运行。
打开http://127.0.0.1:8501。默认账号：无需登录。无需模型密钥。停止：启动窗口Ctrl+C。

选择两家公司示例并运行，或在自定义核查中提交声明与证据原文。可查看出处、情景和下载报告。
自定义输入只做规则核查，不套用固定估值；示例是固定参数下的敏感性分析，不是已识别因果效应。
无证据或规则无法判断时拒答。无实时检索、PDF上传和在线大模型验证；来源链接与页码仅记录，不自动核实原件。

包内src是自研规则、工程/经济映射、批判与财务模型；Streamlit/openpyxl为外部依赖。
data/processed是已有公开来源整理与示例假设，不含校园账号、CSMAR导出或密钥。

如端口8501占用，请关闭占用程序，或使用.venv-demo的Python手动启动并改--server.port。
首次pip下载失败请检查网络后重试；此包不含离线依赖安装轮子。
Windows真实电脑与非开发成员试用仍待验收。详细说明见docs/semifinal/reviewer_quickstart.md。

批量核查：启动后使用.venv-demo/bin/python（Windows为.venv-demo\\Scripts\\python.exe）运行
scripts/review_evidence_batch.py --input docs/semifinal/templates/evidence_batch.csv --out batch_result。
模板为明确标注的合成案例；新证据按docs/semifinal/batch_evidence_guide.md填写。
结果目录必须不存在；批量核查不认证原件、不修改Claim Bank、不计算估值。
"""


def build(output):
    output = Path(output)
    files = ["app.py", "requirements-demo.txt", "start_demo.bat", "start_demo.sh", "scripts/launch_demo.py",
             "docs/semifinal/reviewer_quickstart.md", "scripts/review_evidence_batch.py",
             "docs/semifinal/batch_evidence_guide.md", "docs/semifinal/templates/evidence_batch.csv"]
    files += [str(p.relative_to(ROOT)) for p in sorted((ROOT / "src").rglob("*.py"))]
    files += ["data/processed/" + name for name in DATA]
    contents = {name: (ROOT / name).read_bytes() for name in files}
    contents["start.sh"] = contents["start_demo.sh"]
    contents["部署说明.md"] = GUIDE.encode("utf-8")
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(contents.items())}
    contents["package_manifest.json"] = json.dumps({"scope": "offline_reviewer_deployment",
        "files_sha256": manifest, "windows_runtime_verified": False}, ensure_ascii=False, indent=2).encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(contents.items()):
            info = zipfile.ZipInfo("06_本地部署/" + name, (2026, 10, 2, 0, 0, 0))
            info.external_attr = (0o100755 if name.endswith(".sh") else 0o100644) << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED)
    return {"path": str(output), "files": len(contents), "bytes": output.stat().st_size,
            "sha256": hashlib.sha256(output.read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().out), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
