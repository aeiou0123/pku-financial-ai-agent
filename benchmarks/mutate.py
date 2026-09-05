"""
Claim2Value Benchmark — Mutation Generator
=============================================

对 claim_bank_filled.json 中的每条 claim 注入 6 类扰动，
生成 claim 验证 benchmark 测试用例。

原理（Mutation Testing of State Oracles）：
    一个好的 verifier 不仅要能验证正确的 claim，
    更要能识别被动过手脚的 claim。
    我们故意制造"看起来合理但实际错误"的输入，
    检验系统的判别力（discrimination ability）。

运行方式:
    python benchmarks/mutate.py

输出:
    benchmarks/claim_verification.json
"""

import json
import re
import random
from pathlib import Path
from datetime import date

random.seed(42)  # 可复现，方便团队对齐

# ── 路径 ──
REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = REPO_ROOT / "data" / "processed" / "claim_bank_filled.json"
OUTPUT_PATH = REPO_ROOT / "benchmarks" / "claim_verification.json"


# ============================================================
# 扰动 1: 数值篡改 (Value Tampering)
# ============================================================
# 场景：把 claim 中的关键数值改大或改小，
#        检验系统能否检出"数值与来源矛盾"。
# ============================================================

def mutate_value_tampering(claim: dict) -> dict | None:
    text = claim["claim_text"]

    # 关键设计：从 claim 的 value 字段挑要篡改的数值，
    # 而不是从 claim_text 里随便挑。这样只会篡改关键指标
    # （金额/数量/百分比），不会误改年份、季度(Q2)、型号(LHS-32)。
    candidates = re.findall(r'\d+\.?\d*', claim.get("value", ""))
    # 排除年份（19xx/20xx），年份由 temporal_shift 扰动处理
    candidates = [n for n in candidates if not re.fullmatch(r'(?:19|20)\d{2}', n)]
    # 只保留确实出现在 claim_text 里的（边界匹配，避免子串误判）
    candidates = [
        n for n in candidates
        if re.search(r'(?<!\d)' + re.escape(n) + r'(?!\d)', text)
    ]

    if not candidates:
        # fallback：value 字段无数值时，从 claim_text 找。
        # 排除年份 + 排除单字符（单字符易歧义，如 "2025" 里的 "2"）
        all_numbers = re.findall(r'\d+\.?\d*', text)
        seen = set()
        candidates = [
            n for n in all_numbers
            if not re.fullmatch(r'(?:19|20)\d{2}', n)
            and len(n) >= 2
            and not (n in seen or seen.add(n))
        ]

    if not candidates:
        return None

    target = random.choice(candidates)
    original_val = float(target)

    if random.random() < 0.5:
        factor = random.uniform(0.3, 0.7)
    else:
        factor = random.uniform(1.3, 2.0)

    tampered_val = round(original_val * factor, 2)
    if '.' not in target:
        tampered_val = int(tampered_val)

    # 边界匹配替换：(?<!\d) 和 (?!\d) 确保 target 是完整数字，
    # 不会把 "2025" 里的 "2" 或 "LHS-32" 里的 "32" 误改掉
    mutated_text = re.sub(
        r'(?<!\d)' + re.escape(target) + r'(?!\d)',
        str(tampered_val), text, count=1
    )

    return {
        "mutation_type": "value_tampering",
        "mutated_claim": mutated_text,
        "mutated_source": claim["source_text"],
        "expected_verdict": "refuted",
        "expected_confidence_max": 0.3,
        "diff_description": f"数值从 {target} 篡改为 {tampered_val}",
        "rationale": "数值与来源矛盾，系统应检出",
    }


# ============================================================
# 扰动 2: 限定词删除 (Qualifier Removal)
# ============================================================
# 场景：删掉 claim 中的限定条件（"同等出力""同尺寸"），
#        检验系统能否识别"定义不完整"。
# ============================================================

QUALIFIER_PATTERNS = [
    r'在同等出力情况下',
    r'同等出力情况下',
    r'同尺寸',
    r'在同等条件下',
    r'连续扭矩',
    r'额定扭矩',
    r'峰值扭矩',
    r'累计出货',
    # ── 扩充：更多可删除的限定词 ──
    r'同比增长',        # 删掉后变成"增长"（方向不明）
    r'同比下降',        # 同上
    r'归母净利润',      # 删掉后变成"净利润"（口径不明）
    r'扣非后净利润',    # 同上
    r'扣非净利润',      # 同上
    r'国内',           # 删掉后市占率范围不明
    r'国产',           # 删掉后TOP2范围不明
    r'精密',           # 删掉后产品类型不明
    r'关节模组',       # 删掉后减重对象不明
    r'谐波减速器',     # 删掉后产品线不明（慎用，可能改变主语）
    r'无框力矩电机',   # 删掉后产品线不明
    r'RV减速器',       # 删掉后产品线不明
    r'设计产能',       # 删掉后产能口径不明
    r'专用',           # 删掉后定制化程度不明
    r'长期',           # 删掉后合作深度不明
    r'核心',           # 删掉后供应商地位不明
]


def mutate_qualifier_removal(claim: dict) -> list[dict]:
    """对每条 claim 生成多个限定词删除用例（每匹配到一个限定词生成一个）。"""
    if not claim.get("definition_issues"):
        return []

    text = claim["claim_text"]
    results = []

    for pattern in QUALIFIER_PATTERNS:
        match = re.search(pattern, text)
        if not match:
            continue

        removed = match.group()
        mutated_text = text.replace(removed, '', 1)
        mutated_text = re.sub(r'，+', '，', mutated_text)
        mutated_text = re.sub(r'，([，。])', r'\1', mutated_text)
        mutated_text = mutated_text.strip('，').strip()

        # 跳过删完后文本太短或没实质变化的
        if len(mutated_text) < 8:
            continue

        results.append({
            "mutation_type": "qualifier_removal",
            "mutated_claim": mutated_text,
            "mutated_source": claim["source_text"],
            "expected_verdict": "partially_supported",
            "expected_confidence_max": 0.5,
            "diff_description": f"删除限定条件「{removed}」",
            "rationale": "限定条件被删除，定义不完整，系统应标记",
        })

    return results


# ============================================================
# 扰动 3: 口径偷换 (Unit Swap)
# ============================================================
# 场景：把"额定扭矩"偷换为"峰值扭矩"（或反之），
#        检验系统能否识别测试口径不一致。
# ============================================================

UNIT_SWAPS = [
    ('额定扭矩', '峰值扭矩'),
    ('峰值扭矩', '额定扭矩'),
    ('额定', '峰值'),
    # ── 扩充：更多口径对 ──
    ('归母净利润', '扣非净利润'),
    ('扣非净利润', '归母净利润'),
    ('扣非后净利润', '归母净利润'),
    ('营业收入', '净利润'),
    ('设计产能', '实际达产产能'),
    ('市占率', '全球市占率'),
    ('国内市占率', '全球市占率'),
    ('累计出货', '年度出货'),
    ('销量', '出货量'),
    ('毛利率', '净利率'),
    ('CAGR', '年均增长率'),
]


def mutate_unit_swap(claim: dict) -> list[dict]:
    """对每条 claim 生成多个口径偷换用例（每匹配到一个口径对生成一个）。"""
    text = claim["claim_text"]
    results = []

    for old, new in UNIT_SWAPS:
        if old not in text:
            continue

        mutated_text = text.replace(old, new, 1)
        results.append({
            "mutation_type": "unit_swap",
            "mutated_claim": mutated_text,
            "mutated_source": claim["source_text"],
            "expected_verdict": "definition_mismatch",
            "expected_confidence_max": 0.4,
            "diff_description": f"口径从「{old}」偷换为「{new}」",
            "rationale": "测试口径被偷换，系统应识别",
        })

    return results


# ============================================================
# 扰动 4: 来源降级 (Source Downgrade)
# ============================================================
# 场景：把权威来源（年报/招股书/研报）替换为低权威来源，
#        检验系统能否识别"证据来源不可靠"。
# ============================================================

SOURCE_DOWNGRADES = [
    ('年报', '市场传闻'),
    ('招股书', '自媒体爆料'),
    ('券商研报', '股吧帖子'),
    ('国信证券研报', '网传消息'),
    ('国金证券研报', '网传消息'),
    ('研报', '网传消息'),
    ('半年报', '未经证实的消息'),
]


def mutate_source_downgrade(claim: dict) -> dict | None:
    source = claim["source_text"]

    for old, new in SOURCE_DOWNGRADES:
        if old in source:
            mutated_source = source.replace(old, new, 1)
            return {
                "mutation_type": "source_downgrade",
                "mutated_claim": claim["claim_text"],
                "mutated_source": mutated_source,
                "expected_verdict": "low_confidence",
                "expected_confidence_max": 0.3,
                "diff_description": f"来源从「{old}」降级为「{new}」",
                "rationale": "证据来源不可靠，系统应降低置信度",
            }

    return None


# ============================================================
# 扰动 5: 时间错位 (Temporal Shift)
# ============================================================
# 场景：把年份改错一年，检验系统能否识别时序矛盾。
# ============================================================

def mutate_temporal_shift(claim: dict) -> dict | None:
    text = claim["claim_text"]
    years = re.findall(r'(20\d{2})', text)
    if not years:
        return None

    target_year = random.choice(years)
    shift = random.choice([1, -1])
    wrong_year = str(int(target_year) + shift)

    mutated_text = text.replace(target_year, wrong_year, 1)

    return {
        "mutation_type": "temporal_shift",
        "mutated_claim": mutated_text,
        "mutated_source": claim["source_text"],
        "expected_verdict": "refuted",
        "expected_confidence_max": 0.3,
        "diff_description": f"年份从 {target_year} 篡改为 {wrong_year}",
        "rationale": "时间戳与来源矛盾，系统应检出",
    }


# ============================================================
# 扰动 6: 证据缺失 (Evidence Absence)
# ============================================================
# 场景：删掉所有证据，检验系统是否会拒绝给出结论。
#        这是最狠的一条：诚实的 Agent 应该说"我不知道"，
#        而不是硬编一个答案。
# ============================================================

def mutate_evidence_absence(claim: dict) -> dict:
    return {
        "mutation_type": "evidence_absence",
        "mutated_claim": claim["claim_text"],
        "mutated_source": "",
        "expected_verdict": "abstain",
        "expected_confidence_max": 0.1,
        "diff_description": "删除全部证据来源",
        "rationale": "无证据支撑，诚实的系统应拒答而非硬给结论",
    }


# ============================================================
# 主函数
# ============================================================

MUTATORS = [
    mutate_value_tampering,
    mutate_qualifier_removal,
    mutate_unit_swap,
    mutate_source_downgrade,
    mutate_temporal_shift,
    mutate_evidence_absence,
]

MUTATION_SHORT_NAMES = {
    "value_tampering": "VALU",
    "qualifier_removal": "QUAL",
    "unit_swap": "UNIT",
    "source_downgrade": "SRCD",
    "temporal_shift": "TEMP",
    "evidence_absence": "EVID",
}


def generate_benchmark() -> dict:
    with open(INPUT_PATH, 'r', encoding='utf-8') as f:
        claims = json.load(f)

    cases = []
    type_counts = {}

    for claim in claims:
        for mutator in MUTATORS:
            result = mutator(claim)
            if result is None:
                continue

            # 兼容返回 dict（单个）和 list（多个变体）
            variants = result if isinstance(result, list) else [result]

            for variant in variants:
                mtype = variant["mutation_type"]
                short = MUTATION_SHORT_NAMES.get(mtype, mtype[:4].upper())
                case_id = f"{claim['claim_id']}_{short}"

                # 同一 claim 同类型多变体时加序号
                existing = [c for c in cases if c["case_id"].startswith(case_id)]
                if existing:
                    case_id = f"{case_id}_{len(existing) + 1}"

                case = {
                    "case_id": case_id,
                    "original_claim_id": claim["claim_id"],
                    "subject": claim["subject"],
                    "claim_type": claim["claim_type"],
                    "original_claim": claim["claim_text"],
                    "original_source": claim["source_text"],
                    **variant,
                }
                cases.append(case)
                type_counts[mtype] = type_counts.get(mtype, 0) + 1

    benchmark = {
        "benchmark": "claim_verification",
        "version": "0.1.0",
        "generated": str(date.today()),
        "source_file": str(INPUT_PATH.relative_to(REPO_ROOT)),
        "total_claims": len(claims),
        "total_cases": len(cases),
        "mutation_type_counts": type_counts,
        "cases": cases,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(benchmark, f, ensure_ascii=False, indent=2)

    return benchmark


def print_summary(benchmark: dict):
    print(f"\n{'=' * 55}")
    print(f"  Claim2Value Benchmark — Mutation Report")
    print(f"{'=' * 55}")
    print(f"  原始 claims:      {benchmark['total_claims']}")
    print(f"  生成测试用例:     {benchmark['total_cases']}")
    print(f"\n  各类型扰动数量:")
    for mtype, count in benchmark['mutation_type_counts'].items():
        label = mtype.replace('_', ' ').title()
        print(f"    {label:28s} {count:3d}")
    print(f"\n  输出: {OUTPUT_PATH.name}")
    print(f"{'=' * 55}\n")


if __name__ == "__main__":
    result = generate_benchmark()
    print_summary(result)
