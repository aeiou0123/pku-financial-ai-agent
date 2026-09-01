"""
从环动科技 IPO 招股书中提取专利信息。
输出：data/processed/huandong_patents.csv
"""
import re
import json
import csv
from pathlib import Path
from collections import defaultdict

import pdfplumber


ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "data" / "raw" / "company_filings" / "huandong_ipo_prospectus.pdf"
OUT_CSV = ROOT / "data" / "processed" / "huandong_patents.csv"
OUT_JSON = ROOT / "data" / "processed" / "huandong_patents.json"


def normalize_text(text: str) -> str:
    """清理 PDF 提取文本中的常见噪音"""
    # 合并被换行打断的句子
    text = re.sub(r"(\S)\n(?=\S)", r"\1", text)
    # 去掉多余空格
    text = re.sub(r"[ \t]+", " ", text)
    return text


def extract_patents_from_pdf(pdf_path: Path):
    """提取招股书中所有专利号及上下文"""
    # 中国专利号常见模式：CN + 年份 + 7-10 位数字 + 可选字母，或 ZL 开头
    patent_pattern = re.compile(
        r"(CN\d{4}[01]\d{6,9}[UAYS]?|ZL\d{4}[01]\d{6,9}[\.\dUAYS]*)"
    )

    results = []
    seen = set()

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            text = normalize_text(text)
            if not text:
                continue

            for m in patent_pattern.finditer(text):
                patent_no = m.group(1)
                # 去重：同一专利号只保留第一次出现
                key = patent_no.replace(".", "").replace("ZL", "CN")
                if key in seen:
                    continue
                seen.add(key)

                start = max(0, m.start() - 120)
                end = min(len(text), m.end() + 120)
                context = text[start:end].replace("\n", " ").strip()

                results.append({
                    "patent_no": patent_no,
                    "page": page_idx,
                    "context": context,
                })

    return results


def categorize_patents(results):
    """根据上下文关键词做简单分类"""
    categories = []
    for r in results:
        ctx = r["context"]
        cat = "其他"
        if any(k in ctx for k in ["RV", "摆线", "针轮", "行星", "减速器"]):
            cat = "RV/减速器结构"
        elif any(k in ctx for k in ["谐波", "柔轮", "刚轮", "波发生器"]):
            cat = "谐波减速器"
        elif any(k in ctx for k in ["扭矩", "刚度", "强度", "轻量化", "密度"]):
            cat = "性能/材料"
        elif any(k in ctx for k in ["制造", "加工", "热处理", "齿形", "工艺"]):
            cat = "制造工艺"
        elif any(k in ctx for k in ["电机", "伺服", "驱动"]):
            cat = "电机/驱动"
        r["category"] = cat
        categories.append(r)
    return categories


def main():
    print(f"正在提取专利：{PDF_PATH}")
    results = extract_patents_from_pdf(PDF_PATH)
    results = categorize_patents(results)
    print(f"共提取到 {len(results)} 个不同专利号")

    # 保存 CSV
    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["patent_no", "category", "page", "context"],
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(results)
    print(f"CSV 已保存：{OUT_CSV}")

    # 保存 JSON（便于后续 Agent 读取）
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"JSON 已保存：{OUT_JSON}")


if __name__ == "__main__":
    main()
