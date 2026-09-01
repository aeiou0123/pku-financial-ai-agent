"""
从已提取的 txt 报告中自动扫描产品参数相关片段，生成候选参数表。
输出：data/processed/parameter_candidates.csv
"""
import re
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TXT_DIR = ROOT / "data" / "raw"
OUT_CSV = ROOT / "data" / "processed" / "parameter_candidates.csv"

# 参数关键词与单位
PARAM_PATTERNS = [
    ("扭矩密度", r"扭矩密度|torque density|Nm/kg|N·m/kg|N\\.m/kg"),
    ("额定扭矩", r"额定扭矩|rated torque|额定转矩"),
    ("峰值扭矩", r"峰值扭矩|peak torque|最大转矩|最大扭矩|极限扭矩"),
    ("连续扭矩", r"连续扭矩|continuous torque"),
    ("重量", r"重量|质量|weight|kg|千克"),
    ("减速比", r"减速比|gear ratio|减速比"),
    ("背隙", r"背隙|backlash|重复定位精度|arcsec|角秒"),
    ("效率", r"效率|efficiency"),
    ("功率密度", r"功率密度|power density|W/kg"),
    ("转速", r"转速|speed|rpm|r/min"),
    ("寿命", r"寿命|lifetime|h|小时"),
    ("外径", r"外径|outer diameter|mm"),
]


def find_candidates(text: str, source: str):
    """在文本中查找参数相关片段"""
    candidates = []
    lines = text.splitlines()

    for label, pattern in PARAM_PATTERNS:
        regex = re.compile(pattern, re.IGNORECASE)
        for i, line in enumerate(lines):
            if regex.search(line):
                # 取前后 2 行作为上下文
                ctx_start = max(0, i - 2)
                ctx_end = min(len(lines), i + 3)
                context = " ".join(lines[ctx_start:ctx_end]).strip()
                # 清理多余空格
                context = re.sub(r"\s+", " ", context)
                candidates.append({
                    "source": source,
                    "param_label": label,
                    "line_no": i + 1,
                    "context": context[:500],
                })

    return candidates


def main():
    txt_files = []
    for subdir in ["analyst_reports", "company_filings"]:
        txt_files.extend((TXT_DIR / subdir).glob("*.txt"))

    all_candidates = []
    for txt_path in txt_files:
        text = txt_path.read_text(encoding="utf-8")
        candidates = find_candidates(text, txt_path.name)
        all_candidates.extend(candidates)
        print(f"{txt_path.name}: {len(candidates)} candidates")

    # 去重：同一 source + label + context 只保留一次
    seen = set()
    unique = []
    for c in all_candidates:
        key = (c["source"], c["param_label"], c["context"])
        if key not in seen:
            seen.add(key)
            unique.append(c)

    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["source", "param_label", "line_no", "context"])
        writer.writeheader()
        writer.writerows(unique)

    print(f"\n共提取 {len(unique)} 条候选参数片段，保存至 {OUT_CSV}")


if __name__ == "__main__":
    main()
