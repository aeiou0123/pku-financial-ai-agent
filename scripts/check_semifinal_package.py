"""Check submission structure; never substitute for scientific or human review."""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
import zipfile

REQUIRED = ["01_统一信息表.docx", "02_项目说明.pdf", "03_展示稿.pptx", "04_运行视频.mp4",
            "07_技术题/submission.csv", "07_技术题/code.zip", "07_技术题/技术题报告.pptx"]
CALENDAR_SHA = "bda296fe3c1812defa6a164bd8be288fb9d66ae44f99e08635420faae2737dcf"


def presentation_slides(path):
    with zipfile.ZipFile(path) as archive:
        ET.fromstring(archive.read("ppt/presentation.xml"))
        names = set(archive.namelist())
        count = len([n for n in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)])
        if not count or archive.testzip():
            raise ValueError("No slides or corrupt archive")
        return count


def check_holdings(path):
    holdings = {}
    universe = {f"C{i:04d}" for i in range(1, 401)}
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        rows = csv.reader(handle, strict=True)
        if next(rows, None) != ["date", "stock_id"]:
            raise ValueError("CSV header must be date,stock_id")
        for row in rows:
            if len(row) != 2:
                raise ValueError("CSV must have exactly two fields")
            date, stock = row
            if dt.date.fromisoformat(date).isoformat() != date or stock not in universe:
                raise ValueError("Invalid date or stock")
            bucket = holdings.setdefault(date, set())
            if stock in bucket:
                raise ValueError("Duplicate holding")
            bucket.add(stock)
    dates = sorted(holdings)
    if len(dates) != 1212 or any(len(s) != 20 for s in holdings.values()):
        raise ValueError("Expected 1212 days with 20 distinct stocks each")
    if hashlib.sha256(("\n".join(dates) + "\n").encode()).hexdigest() != CALENDAR_SHA:
        raise ValueError("Official test calendar mismatch")
    return {"days": len(dates), "rows": 24240}


def check(root, online_url="", tools=None, test=None):
    root = Path(root)
    errors, warnings, checks = [], [], {}
    for name in REQUIRED:
        path = root / name
        if not path.is_file() or not path.stat().st_size:
            errors.append("缺失或空文件：" + name)
    evidence = root / "05_技术证据"
    if not evidence.is_dir() or not any(p.is_file() and p.stat().st_size for p in evidence.rglob("*")):
        errors.append("05_技术证据缺失或无有效文件")
    if online_url:
        parsed = urlsplit(online_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
            errors.append("在线地址须为评委可访问的HTTP(S)地址，不能是localhost")
        warnings.append("在线可访问性、账号和有效期需实际验收；此脚本不登录页面")
    else:
        deployment = root / "06_本地部署"
        launchers = ["start.sh", "start_demo.sh", "start_demo.bat", "docker-compose.yml"]
        if not deployment.is_dir() or not any((deployment / name).is_file() for name in launchers):
            errors.append("未提供在线地址，06_本地部署须有启动文件")
        if not (deployment / "部署说明.md").is_file():
            errors.append("本地部署缺少部署说明.md")
        warnings.append("本地部署实际启动与人工环节需按说明验收")
    for name in ["03_展示稿.pptx", "07_技术题/技术题报告.pptx"]:
        if (root / name).is_file():
            try:
                count = presentation_slides(root / name)
                checks[name] = {"slides": count}
                if name.startswith("07_") and count > 20:
                    errors.append("技术题报告超过20页")
            except Exception as exc:
                errors.append(f"PPTX无法解析：{name}（{type(exc).__name__}）")
    docx = root / "01_统一信息表.docx"
    if docx.is_file():
        try:
            with zipfile.ZipFile(docx) as archive:
                document = ET.fromstring(archive.read("word/document.xml"))
                text = "".join(document.itertext()).strip()
                if not text or archive.testzip():
                    errors.append("信息表无可读内容或损坏")
            warnings.append("信息表五栏限字、必填字段及真实性需按附件一人工核对")
        except Exception as exc:
            errors.append(f"DOCX无法解析（{type(exc).__name__}）")
    pdf = root / "02_项目说明.pdf"
    if pdf.is_file():
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf)
            checks["pdf"] = {"pages": len(reader.pages), "has_outline": bool(reader.outline)}
            if not reader.pages or not reader.outline:
                errors.append("项目说明PDF无页面或未设置书签")
            warnings.append("PDF书签是否覆盖各部分及内容一致性需人工核对")
        except ImportError:
            warnings.append("未安装pypdf，PDF可读性与书签未验证")
        except Exception as exc:
            errors.append(f"PDF无法解析（{type(exc).__name__}）")
    video = root / "04_运行视频.mp4"
    if video.is_file():
        if shutil.which("ffprobe"):
            try:
                result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-show_chapters", "-of", "json", str(video)], capture_output=True, text=True, check=True, timeout=30)
                metadata = json.loads(result.stdout)
                streams = [s for s in metadata["streams"] if s.get("codec_type") == "video"]
                if not any(s.get("width", 0) >= 1280 and s.get("height", 0) >= 720 for s in streams):
                    errors.append("视频无有效画面或低于1280×720")
                duration = float(metadata.get("format", {}).get("duration", 0))
                checks["video"] = {"duration_seconds": duration, "embedded_chapters": len(metadata.get("chapters", []))}
                if duration <= 0:
                    errors.append("视频时长无效")
                elif duration > 300:
                    warnings.append("视频超过建议5分钟，请确认必要性")
                if not metadata.get("chapters"):
                    warnings.append("未发现容器章节；请人工确认画面中有章节标记")
            except Exception as exc:
                errors.append(f"视频无法解析（{type(exc).__name__}）")
        else:
            warnings.append("未安装ffprobe，视频分辨率、时长、章节尚未验证")
    code = root / "07_技术题/code.zip"
    if code.is_file():
        try:
            with zipfile.ZipFile(code) as archive:
                if not archive.namelist() or archive.testzip():
                    errors.append("code.zip为空或损坏")
            warnings.append("技术题代码与名单生成记录对应、依赖及实际复现需验收")
        except zipfile.BadZipFile:
            errors.append("code.zip不是有效ZIP")
    submission = root / "07_技术题/submission.csv"
    if submission.is_file():
        try:
            checks["holdings_structure"] = check_holdings(submission)
            if tools and test:
                import sys
                sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
                from competition.baseline import official_tools, verify_data
                official = official_tools(tools)
                verify_data(test, "test", official)
                checks["official_submission_check"] = official.check(submission, test)
                if checks["official_submission_check"].get("status") != "VALID":
                    errors.append("官方持仓校验未通过")
            else:
                warnings.append("未提供--tools/--test，尚未执行官方tools.py check")
        except Exception as exc:
            errors.append(f"持仓校验失败：{exc}")
    return {"status": "BLOCKED" if errors else "STRUCTURE_VALID_MANUAL_REVIEW_REQUIRED",
            "errors": errors, "manual_review": warnings, "checks": checks,
            "scope": "Structure/media inspection only; no verification of claims, performance or actual user experience."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--online-url", default="")
    parser.add_argument("--tools", type=Path)
    parser.add_argument("--test", type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    result = check(args.root, args.online_url, args.tools, args.test)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    raise SystemExit(1 if result["errors"] else 0)


if __name__ == "__main__":
    main()
