"""Bounded document parsing with explicit page/line coverage and byte provenance."""
from __future__ import annotations

from .module_stamp import source_stamp
_c2v_loaded_source_hash = source_stamp(__file__)

import hashlib
import csv
import io
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import pandas as pd

MAX_BYTES = 20 * 1024 * 1024
MAX_TOTAL_BYTES = 60 * 1024 * 1024
MAX_PAGES = 1000
MAX_CHARS = 1000000


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(name: str) -> str:
    # Uploaded names are labels, never paths or Windows devices.
    base = re.split(r"[/\\]", name)[-1]
    base = re.sub(r"[^\w.\-\u4e00-\u9fff]", "_", base)[:100]
    if not base or base in {".", ".."}:
        base = "upload"
    return "source_" + base


def upload_issues(uploads: list[tuple[str, bytes]]) -> list[str]:
    """Show all intake problems before creating a run or making model requests."""
    issues = []
    if len(uploads) > 10:
        issues.append(f'已选 {len(uploads)} 个文件；每次最多10个，请分批处理。')
    total = sum(len(raw) for _, raw in uploads)
    if total > MAX_TOTAL_BYTES:
        issues.append(f'总大小 {total / 1024**2:.1f} MB；上限60 MB，请缩小材料范围。')
    used = set()
    for name, raw in uploads:
        if not raw:
            issues.append(f'{name} 是空文件，请重新导出有内容的文件。')
        elif len(raw) > MAX_BYTES:
            issues.append(f'{name} 超过20 MB，请拆分后上传；保留原件页码对应关系。')
        key = safe_name(name).casefold().rstrip('. ')
        if key in used:
            issues.append(f'{name} 与另一文件保存后的名称冲突，请重命名后上传。')
        used.add(key)
        if Path(name).suffix.lower() not in {'.pdf','.docx','.txt','.md','.csv','.xlsx'}:
            issues.append(f'{name} 格式暂不支持；请选择PDF、Word、文本、CSV或Excel文件。')
    return issues


def decode(data: bytes) -> str:
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    raise ValueError("仅支持 UTF-8 或 GB18030 文本，请先转换编码。")


def table(data: bytes, name: str, sheet: str | int = 0) -> pd.DataFrame:
    if len(data) > MAX_BYTES:
        raise ValueError("单个文件上限 20 MB。")
    suffix = Path(name).suffix.lower()
    if suffix == ".csv":
        text = decode(data)
        headers = next(csv.reader(io.StringIO(text)), [])
        if len(headers) != len(set(headers)):
            raise ValueError("CSV 存在重复列名。")
        frame = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)
    elif suffix == ".xlsx":
        _check_zip(data)
        frame = pd.read_excel(io.BytesIO(data), sheet_name=sheet, dtype=str, keep_default_na=False)
    else:
        raise ValueError("表格请使用 CSV 或 XLSX。")
    if frame.empty or not frame.columns.is_unique:
        raise ValueError("表格为空或存在重复列名。")
    return frame


def _check_zip(data: bytes) -> None:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if sum(i.file_size for i in archive.infolist()) > 100 * 1024 * 1024:
            raise ValueError("压缩文档展开超过 100 MB。")


def page_selection(value: str) -> list[int] | None:
    """One-based original PDF pages; blank means the usual full bounded parse."""
    if not value.strip():
        return None
    pages = set()
    for item in value.replace('，', ',').split(','):
        if not re.fullmatch(r'\s*[1-9]\d*\s*(?:-\s*[1-9]\d*\s*)?', item):
            raise ValueError('PDF页码格式错误；请使用1,6-7,108-116这样的原件页码。')
        bounds = [int(part.strip()) for part in item.split('-')]
        start, end = bounds[0], bounds[-1]
        if end < start or end > MAX_PAGES:
            raise ValueError('PDF页码范围错误；页码必须递增且不超过1000。')
        pages.update(range(start, end + 1))
    return sorted(pages)


def parse(data: bytes, name: str, *, max_chars: int = MAX_CHARS, max_pages: int = MAX_PAGES,
          pdf_pages: str = '') -> dict:
    if not data or len(data) > MAX_BYTES:
        raise ValueError("文件为空或超过 20 MB。")
    if not 1 <= max_chars <= MAX_CHARS or not 1 <= max_pages <= MAX_PAGES:
        raise ValueError('解析范围超出本机允许的字符或页数上限。')
    suffix = Path(name).suffix.lower()
    selection = page_selection(pdf_pages)
    if selection and suffix != '.pdf':
        raise ValueError('PDF页码选择仅适用于PDF文件。')
    parts, warnings = [], []
    total_units = 0
    if suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise ValueError("PDF 已加密，请上传可读取的版本。")
        total_units = len(reader.pages)
        if selection and (selection[-1] > total_units or len(selection) > max_pages):
            raise ValueError('PDF页码超出原件总页数或本次允许页数；请核对原件。')
        selected = selection or list(range(1, min(total_units, max_pages) + 1))
        if selection and len(selected) < total_units:
            warnings.append(f'本次只读取指定的{len(selected)}个原件页；其余页不在审查范围内。')
        for i in selected:
            page = reader.pages[i - 1]
            text = page.extract_text() or ""
            if not text.strip():
                warnings.append(f"第 {i} 页无可提取文字；本版不含 OCR。")
            parts.append({"locator": f"page:{i}", "text": text})
    elif suffix in {".txt", ".md"}:
        lines = decode(data).splitlines()
        total_units = len(lines)
        parts = [{"locator": f"line:{i}", "text": text} for i, text in enumerate(lines, 1)]
    elif suffix == ".docx":
        _check_zip(data)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            xml = archive.read("word/document.xml")
        root = ElementTree.fromstring(xml)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = root.findall(".//w:p", ns)
        total_units = len(paragraphs)
        parts = [{"locator": f"paragraph:{i}", "text": "".join(p.itertext())}
                 for i, p in enumerate(paragraphs, 1)]
        warnings.append("DOCX 定位为段落序号，不是 Word 页码；未读取页眉页脚或文本框附件。")
    elif suffix in {".csv", ".xlsx"}:
        if suffix == ".csv":
            sheets = {"CSV": table(data, name)}
        else:
            _check_zip(data)
            with pd.ExcelFile(io.BytesIO(data)) as workbook:
                sheets = {sheet: table(data, name, sheet) for sheet in workbook.sheet_names}
        for sheet, frame in sheets.items():
            total_units += len(frame)
            for i, values in enumerate(frame.to_dict("records"), 2):
                parts.append({"locator": f"sheet:{sheet}/row:{i}",
                              "text": json.dumps(values, ensure_ascii=False)})
    else:
        raise ValueError("支持 PDF、DOCX、TXT、MD、CSV、XLSX。")
    kept, chars = [], 0
    for part in parts:
        if chars + len(part["text"]) > max_chars:
            warnings.append(f"本机提取文字达到 {max_chars:,} 字符上限；后续内容尚未解析。已解析文字仍按小批次送入模型，不等于一次请求整个报告。")
            if chars < max_chars:
                kept.append({**part, "text": part["text"][:max_chars - chars]})
                chars = max_chars
            break
        kept.append(part)
        chars += len(part["text"])
    if suffix == ".pdf" and not selection and total_units > max_pages:
        warnings.append(f"本次只读取前 {max_pages} 页；其余页尚未解析。")
    if not any(p["text"].strip() for p in kept):
        raise ValueError("没有可读取的文字，本版不含 OCR。")
    return {"name": name, "source_file": safe_name(name), "sha256": digest(data),
            "bytes": len(data), "parts": kept, "warnings": warnings,
            "total_units": total_units, "parsed_units": len(kept), "characters": chars,
            "coverage": "partial" if warnings else "parsed_text",
            "parse_limits": {"max_chars": max_chars, "max_pages": max_pages,
                             "pdf_pages": selection}}


def chunks(documents: list[dict], limit: int = 6000) -> list[list[dict]]:
    """Every included character receives its own anchored chunk; no silent slicing."""
    if not 500 <= limit <= 16000:
        raise ValueError('单批原文须为500—16000字符。')
    output, current, size = [], [], 0
    piece_size = min(5000, limit)
    for doc in documents:
        for part in doc["parts"]:
            # Long pages are explicitly split; quote checks bind to the exact piece.
            for offset in range(0, len(part["text"]), piece_size):
                piece = {"source_file": doc["source_file"], "source_sha256": doc["sha256"],
                         "source_locator": part["locator"], "offset": offset,
                         "text": part["text"][offset:offset + piece_size]}
                if size + len(piece["text"]) > limit and current:
                    output.append(current)
                    current, size = [], 0
                current.append(piece)
                size += len(piece["text"])
    if current:
        output.append(current)
    return output
