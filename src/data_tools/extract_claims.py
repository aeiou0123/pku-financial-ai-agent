"""
从已提取的 txt 报告中扫描 claim-like 语句，生成候选 claim 素材。
输出：data/processed/claim_candidates.csv
"""
import re
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TXT_DIR = ROOT / "data" / "raw"
OUT_CSV = ROOT / "data" / "processed" / "claim_candidates.csv"

# Claim 模式：数字/百分比/数量词 + 关键动词/名词
CLAIM_PATTERNS = [
    r"(提升|增长|增加|提高|改善).{0,15}(\d+\.?\d*%|\d+\.?\d*倍|超过\s*\d+)",
    r"(下降|降低|减少|缩减).{0,15}(\d+\.?\d*%|\d+\.?\d*倍)",
    r"(产能|年产能|出货量|出货|销量|销售).{0,15}(\d+\.?\d*\s*[万]?台|[\d,]+\s*套)",
    r"(营收|收入|净利润|毛利率).{0,15}(\d+\.?\d*\s*亿元?|\d+\.?\d*%)",
    r"(进入|获得|导入|切入|供应).{0,20}(特斯拉|Optimus|小米|优必选|宇树|智元|天工|纳博特斯克|哈默纳科|客户)",
    r"(市占率|市场份额).{0,10}(\d+\.?\d*%)",
    r"(扭矩密度|功率密度|传动效率|背隙|减速比|重量).{0,15}(\d+\.?\d*\s*(Nm/kg|W/kg|%|arcmin|角分|角秒|kg|mm|rpm|r/min))",
    r"(达到|实现|突破).{0,15}(\d+\.?\d*\s*(Nm/kg|W/kg|%|arcmin|角分|角秒|kg|万台|亿元))",
]


def find_claims(text: str, source: str):
    claims = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        for pattern in CLAIM_PATTERNS:
            if re.search(pattern, line):
                ctx_start = max(0, i - 1)
                ctx_end = min(len(lines), i + 2)
                context = " ".join(lines[ctx_start:ctx_end]).strip()
                context = re.sub(r"\s+", " ", context)
                claims.append({
                    "source": source,
                    "line_no": i + 1,
                    "context": context[:400],
                    "matched_pattern": pattern[:60],
                })
                break  # 每行只记录一次
    return claims


def main():
    txt_files = []
    for subdir in ["analyst_reports", "company_filings"]:
        txt_files.extend((TXT_DIR / subdir).glob("*.txt"))

    all_claims = []
    for txt_path in txt_files:
        text = txt_path.read_text(encoding="utf-8")
        claims = find_claims(text, txt_path.name)
        all_claims.extend(claims)
        print(f"{txt_path.name}: {len(claims)} claims")

    # 按 source 去重
    seen = set()
    unique = []
    for c in all_claims:
        key = (c["source"], c["context"])
        if key not in seen:
            seen.add(key)
            unique.append(c)

    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["source", "line_no", "context", "matched_pattern"])
        writer.writeheader()
        writer.writerows(unique)

    print(f"\n共提取 {len(unique)} 条候选 claim，保存至 {OUT_CSV}")


if __name__ == "__main__":
    main()
