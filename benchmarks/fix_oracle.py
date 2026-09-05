"""
fix_oracle.py — Oracle 自我修正：为证据不足的用例注入原始参数
================================================================

背景（首轮 benchmark 的元发现）：
    首轮评估中，模型的"过度拒答"并非模型保守，而是考卷缺陷——
    部分技术参数类用例的 source_text 只写了来源名（如"国金证券研报：对比表"），
    没有把对比表里的原始数值给模型。模型没有可核对的内容，
    选择 abstain 是诚实且正确的，错的是 oracle 预设了模型不可见的信息。

修正方法：
    从 parameter_table_filled.csv 提取型号的原始参数，
    作为"研报原文摘录"注入到对应用例的 evidence 中。
    这样 expected_verdict 才站得住——模型有了对照物，
    才能真正检出数值篡改 / 口径偷换 / 限定词删除。

原则：
    - 只动 benchmark 生成的用例，不动 claim_bank_filled.json（队长的原始数据）
    - evidence_absence 用例不注入（它本来就是测"无证据时是否拒答"）
    - 输出 v2 用例集，保留 v1 以便对比

运行：
    python benchmarks/fix_oracle.py
输出：
    benchmarks/claim_verification_v2.json
"""

import io
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
V1_PATH = REPO_ROOT / "benchmarks" / "claim_verification.json"
V2_PATH = REPO_ROOT / "benchmarks" / "claim_verification_v2.json"

# ──────────────────────────────────────────────────────────────
# 证据补丁：从 parameter_table_filled.csv 整理的原始参数
# 注入后，模型才有对照物来检出扰动
# ──────────────────────────────────────────────────────────────
EVIDENCE_PATCHES = {
    "GH_007": (
        "【研报原文摘录】LHS-32 谐波减速器：额定扭矩 51 Nm，峰值扭矩 130 Nm，"
        "重量 2.5 kg，扭矩密度 20.4 Nm/kg，效率 80%，齿隙 ≤1 arcmin，"
        "使用寿命 15000 h，最大输入转速 6500 rpm。"
    ),
    "SH_002": (
        "【研报原文摘录】SHPR-20E RV 减速器：额定扭矩 110 Nm，峰值扭矩 231 Nm，"
        "重量 4.7 kg，扭矩密度 23.4 Nm/kg，效率 80%。"
        "（对比：纳博特斯克 RV-20E 额定扭矩 412 Nm，重量 2.5 kg，扭矩密度 164.8 Nm/kg）"
    ),
    "IND_001": (
        "【招股书引用 GGII 数据原文】2023 年中国工业机器人销量达 31.60 万台，"
        "2019 年为 15.31 万台，2019-2023 年复合增长率（CAGR）为 19.86%。"
    ),
}


def needs_patch(case: dict) -> bool:
    """该用例是否需要注入证据补丁"""
    # evidence_absence 本来就是测"无证据拒答"，不能注入
    if case["mutation_type"] == "evidence_absence":
        return False
    return case["original_claim_id"] in EVIDENCE_PATCHES


def inject_evidence(case: dict) -> dict:
    """给用例注入原始参数证据"""
    patch = EVIDENCE_PATCHES[case["original_claim_id"]]
    new_case = dict(case)
    original_source = case["mutated_source"]
    # 在原有 source 后追加原文摘录
    if original_source:
        new_case["mutated_source"] = f"{original_source}\n{patch}"
    else:
        new_case["mutated_source"] = patch
    # 标记此用例经过 oracle 修正
    new_case["oracle_fixed"] = True
    new_case["oracle_fix_note"] = "注入原始参数，使扰动可被检出"
    return new_case


def main():
    v1 = json.loads(io.open(V1_PATH, encoding="utf-8").read())
    cases = v1["cases"]

    patched = 0
    v2_cases = []
    for case in cases:
        if needs_patch(case):
            v2_cases.append(inject_evidence(case))
            patched += 1
        else:
            new_case = dict(case)
            new_case["oracle_fixed"] = False
            v2_cases.append(new_case)

    v2 = {
        "benchmark": "claim_verification",
        "version": "0.2.0",
        "generated": v1.get("generated"),
        "oracle_fixed": True,
        "oracle_fix_description": (
            "首轮发现部分技术参数用例的 source 只写来源名、未含可核对数值，"
            "导致模型无法检出扰动（abstain 是正确答案而非失误）。"
            "本版从 parameter_table_filled.csv 注入原始参数作为证据。"
        ),
        "source_file": v1.get("source_file"),
        "total_claims": v1["total_claims"],
        "total_cases": len(v2_cases),
        "patched_cases": patched,
        "mutation_type_counts": v1["mutation_type_counts"],
        "cases": v2_cases,
    }

    io.open(V2_PATH, "w", encoding="utf-8").write(
        json.dumps(v2, ensure_ascii=False, indent=2)
    )

    print("=" * 60)
    print("  Oracle 修正完成")
    print("=" * 60)
    print(f"  总用例:       {len(v2_cases)}")
    print(f"  注入证据补丁: {patched} 条")
    print()
    # 按 claim 统计注入数量
    from collections import Counter
    c = Counter(
        case["original_claim_id"]
        for case in v2_cases if case.get("oracle_fixed")
    )
    for cid, n in sorted(c.items()):
        print(f"    {cid}: {n} 条用例注入证据")
    print()
    print(f"  输出: {V2_PATH.name}")
    print("=" * 60)


if __name__ == "__main__":
    main()
