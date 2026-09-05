"""
state_verifier.py — Claim2Value 定义一致性验证器
=================================================

这是 Claim2Value 的「技术创新」核心模块。

问题：
    Benchmark 评估发现，主流 LLM 在金融 claim 验证中有两个系统性盲区：
    1. 口径偷换（unit_swap）：分不清额定扭矩/峰值扭矩、归母净利润/扣非净利润、
       毛利率/净利率 → 判别准确率仅 12-35%
    2. 限定词删除（qualifier_removal）：删掉"同等出力""同尺寸"等限定条件后
       不识别定义缺失 → 判别准确率仅 32-42%

方案：
    在 LLM 判断之前，先用确定性规则层做定义一致性检查。
    这不是让 LLM "更努力"，而是给它一个外部检查器——
    模型可能分不清"额定"和"峰值"，但规则引擎永远不会搞混。

    本模块维护一个金融/工程定义注册表（DefinitionRegistry），
    检测 claim 中的口径是否与证据一致、限定条件是否完整。

用法：
    from src.state_verifier import StateVerifier, VerificationResult

    verifier = StateVerifier()
    result = verifier.verify(claim_text, source_text)
    # result.has_definition_mismatch → True if 口径偷换
    # result.missing_qualifiers → ["同等出力情况下"]
    # result.verdict → "definition_mismatch" / "partially_supported" / None
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set, Tuple


# ============================================================
# 定义注册表：口径对 & 限定词库
# ============================================================

@dataclass
class DefinitionPair:
    """一对不可混用的口径定义"""
    term_a: str           # 如 "额定扭矩"
    term_b: str           # 如 "峰值扭矩"
    category: str         # 如 "扭矩口径"
    severity: str = "high"  # high = 量级差异, medium = 定义差异
    description: str = ""


# 口径对注册表：这些定义不可混用
# 来源：parameter_table_filled.csv + 金融常识
DEFINITION_PAIRS: List[DefinitionPair] = [
    # ── 扭矩口径 ──
    DefinitionPair("额定扭矩", "峰值扭矩", "扭矩口径", "high",
                    "额定扭矩是持续工作能力，峰值扭矩是瞬时最大值，量级可差 2-3 倍"),
    DefinitionPair("额定", "峰值", "扭矩口径", "high",
                    "额定/峰值混淆会导致性能评估量级错误"),
    # ── 利润口径 ──
    DefinitionPair("归母净利润", "扣非净利润", "利润口径", "medium",
                    "归母净利润含非经常性损益，扣非净利润不含，差异可达 30-50%"),
    DefinitionPair("归母净利润", "扣非后净利润", "利润口径", "medium",
                    "同上"),
    DefinitionPair("扣非净利润", "扣非后净利润", "利润口径", "low",
                    "同一概念不同表述"),
    # ── 利润率口径 ──
    DefinitionPair("毛利率", "净利率", "利润率口径", "high",
                    "毛利率不含期间费用，净利率含，差异通常 10-20 个百分点"),
    # ── 收入口径 ──
    DefinitionPair("营业收入", "净利润", "收入口径", "high",
                    "营业收入是 top-line，净利润是 bottom-line，量级差异大"),
    # ── 产能口径 ──
    DefinitionPair("设计产能", "实际达产产能", "产能口径", "medium",
                    "设计产能是理论值，实际达产产能受良率/工时影响"),
    DefinitionPair("设计产能", "产能利用率", "产能口径", "medium",
                    "设计产能是绝对值，产能利用率是百分比"),
    # ── 市占率口径 ──
    DefinitionPair("国内市占率", "全球市占率", "市占率口径", "medium",
                    "国内市占率分母是国内市场，全球市占率分母是全球市场"),
    DefinitionPair("市占率", "全球市占率", "市占率口径", "medium",
                    "市占率默认指国内，与全球市占率不可混用"),
    # ── 出货口径 ──
    DefinitionPair("累计出货", "年度出货", "出货口径", "medium",
                    "累计出货是历史总量，年度出货是单年量"),
    DefinitionPair("销量", "出货量", "出货口径", "low",
                    "销量面向终端，出货量面向渠道，差异取决于渠道库存"),
]


# 限定词库：这些词对 claim 的定义完整性至关重要
# 来源：claim_bank_filled.json 的 definition_issues 字段 + 工程常识
QUALIFIER_LIBRARY: Dict[str, str] = {
    # ── 测试条件限定词 ──
    "同等出力情况下": "测试条件：出力相同才有可比性",
    "同等出力": "测试条件：出力相同才有可比性",
    "同尺寸": "测试条件：尺寸相同才有可比性",
    "同等条件下": "测试条件：条件相同才有可比性",
    # ── 扭矩类型限定词 ──
    "额定扭矩": "扭矩类型：额定 vs 峰值不可省略",
    "峰值扭矩": "扭矩类型：额定 vs 峰值不可省略",
    "连续扭矩": "扭矩类型：连续 vs 峰值不可省略",
    # ── 统计口径限定词 ──
    "累计出货": "统计口径：累计 vs 年度不可省略",
    "同比增长": "方向限定：增长方向不可省略",
    "同比下降": "方向限定：下降方向不可省略",
    "归母净利润": "利润口径：归母 vs 扣非不可省略",
    "扣非后净利润": "利润口径：归母 vs 扣非不可省略",
    "扣非净利润": "利润口径：归母 vs 扣非不可省略",
    # ── 范围限定词 ──
    "国内": "范围限定：国内 vs 全球不可省略",
    "国产": "范围限定：国产 vs 进口不可省略",
    # ── 产品类型限定词 ──
    "精密": "产品等级：精密 vs 普通不可省略",
    "关节模组": "产品范围：模组 vs 单件不可省略",
    "谐波减速器": "产品线：谐波 vs RV 不可省略",
    "无框力矩电机": "产品线：无框 vs 有框不可省略",
    "RV减速器": "产品线：RV vs 谐波不可省略",
    # ── 产能口径 ──
    "设计产能": "产能口径：设计 vs 实际不可省略",
    # ── 合作深度 ──
    "专用": "定制程度：专用 vs 通用不可省略",
    "长期": "合作深度：长期 vs 短期不可省略",
    "核心": "供应商地位：核心 vs 一般不可省略",
}


# ============================================================
# 验证结果
# ============================================================

@dataclass
class VerificationResult:
    """state_verifier 的验证结果"""
    # 口径偷换检测
    has_definition_mismatch: bool = False
    mismatched_pairs: List[Dict] = field(default_factory=list)
    # 限定词缺失检测
    missing_qualifiers: List[str] = field(default_factory=list)
    # 数值矛盾检测
    value_contradictions: List[Dict] = field(default_factory=list)
    # 来源降级检测
    has_source_downgrade: bool = False
    source_note: str = ""
    # 综合判定
    verdict_override: Optional[str] = None  # 如果检测到问题，覆盖 LLM 的 verdict
    confidence_adjustment: float = 0.0      # 对 LLM confidence 的调整量
    flags: List[str] = field(default_factory=list)  # 人类可读的标记列表

    @property
    def has_issues(self) -> bool:
        return (
            self.has_definition_mismatch
            or len(self.missing_qualifiers) > 0
            or len(self.value_contradictions) > 0
            or self.has_source_downgrade
        )

    def to_dict(self) -> Dict:
        return {
            "has_definition_mismatch": self.has_definition_mismatch,
            "mismatched_pairs": self.mismatched_pairs,
            "missing_qualifiers": self.missing_qualifiers,
            "value_contradictions": self.value_contradictions,
            "has_source_downgrade": self.has_source_downgrade,
            "source_note": self.source_note,
            "verdict_override": self.verdict_override,
            "confidence_adjustment": self.confidence_adjustment,
            "flags": self.flags,
            "has_issues": self.has_issues,
        }


# ============================================================
# StateVerifier：定义一致性验证器
# ============================================================

class StateVerifier:
    """
    确定性规则层：在 LLM 判断之前，先检查定义一致性。

    检测项目：
    1. 口径偷换：claim 用了"峰值扭矩"但证据写的是"额定扭矩"（或反过来）
    2. 限定词缺失：claim 删掉了"同等出力""同尺寸"等关键限定条件
    3. 数值矛盾：claim 中的数值与证据中的数值不一致
    4. 来源降级：证据来源从年报/研报变成了传闻/自媒体
    """

    def __init__(self):
        self.definition_pairs = DEFINITION_PAIRS
        self.qualifier_library = QUALIFIER_LIBRARY
        # 构建口径查找索引：每个词 → 它的"对立面"集合
        self._term_conflicts: Dict[str, Set[str]] = {}
        for pair in self.definition_pairs:
            self._term_conflicts.setdefault(pair.term_a, set()).add(pair.term_b)
            self._term_conflicts.setdefault(pair.term_b, set()).add(pair.term_a)

    # ── 口径偷换检测 ──

    def _extract_value_near_term(self, text: str, term: str, window_before: int = 15, window_after: int = 30) -> Optional[str]:
        """
        提取术语附近的数值。
        优先取术语后面的数值（中文技术文档中数值通常跟在术语后面）。
        排除型号编号（如 LHS-32 中的 32）。
        窗口边界保护：数值被窗口截断（如 "47.31" 切成 "47"）时丢弃，
        宁可提取失败也不返回半个数值——半数值会导致数值归属误判。
        """
        idx = text.find(term)
        if idx < 0:
            return None

        # 先看术语后面（数值通常跟在术语后面）
        after_start = idx + len(term)
        after_end = min(len(text), after_start + window_after)
        after_segment = text[after_start:after_end]
        # 排除连字符后的编号（如 -32, -20E）
        after_segment = re.sub(r'-\w+', '', after_segment)
        # 边界保护：segment 以数字结尾且原文窗口边界处仍是数字/小数点
        # → 最后一个数值被截断，不可靠，截掉
        if after_segment and re.search(r'\d$', after_segment):
            if after_end < len(text) and (text[after_end].isdigit() or text[after_end] == '.'):
                after_segment = re.sub(r'\d+\.?\d*$', '', after_segment)
        after_nums = re.findall(r'(?<!\d)(\d+\.?\d*)(?!\d)', after_segment)
        after_nums = [n for n in after_nums if not re.fullmatch(r'(?:19|20)\d{2}', n) and len(n) >= 2]
        if after_nums:
            return after_nums[0]

        # 再看术语前面（少数情况数值在术语前）
        before_start = max(0, idx - window_before)
        before_segment = text[before_start:idx]
        before_segment = re.sub(r'-\w+', '', before_segment)
        # 边界保护：segment 以数字开头且原文窗口边界前是数字/小数点
        # → 第一个数值被截断，截掉
        if before_segment and re.match(r'^\d', before_segment):
            if before_start > 0 and (text[before_start - 1].isdigit() or text[before_start - 1] == '.'):
                before_segment = re.sub(r'^\d+\.?\d*', '', before_segment)
        before_nums = re.findall(r'(?<!\d)(\d+\.?\d*)(?!\d)', before_segment)
        before_nums = [n for n in before_nums if not re.fullmatch(r'(?:19|20)\d{2}', n) and len(n) >= 2]
        return before_nums[0] if before_nums else None

    def _check_definition_mismatch(self, claim: str, source: str) -> Tuple[bool, List[Dict]]:
        """
        检测 claim 和 source 之间的口径偷换。

        逻辑：
        1. 简单词存在性：claim 有 A，source 有 B，source 无 A → 偷换
        2. 数值归属：claim 有 A，source 同时有 A 和 B，但 claim 中 A 附近的数值
           匹配的是 source 中 B 附近的数值 → 偷换（数值挂错了口径）
        """
        mismatches = []

        for pair in self.definition_pairs:
            # 策略 1：简单词存在性
            # claim 中有 A，source 中有 B（但 source 中没有 A）
            if pair.term_a in claim and pair.term_b in source and pair.term_a not in source:
                mismatches.append({
                    "claim_term": pair.term_a,
                    "source_term": pair.term_b,
                    "category": pair.category,
                    "severity": pair.severity,
                    "description": pair.description,
                    "detection": "word_presence",
                })
                continue
            # claim 中有 B，source 中有 A（但 source 中没有 B）
            if pair.term_b in claim and pair.term_a in source and pair.term_b not in source:
                mismatches.append({
                    "claim_term": pair.term_b,
                    "source_term": pair.term_a,
                    "category": pair.category,
                    "severity": pair.severity,
                    "description": pair.description,
                    "detection": "word_presence",
                })
                continue

            # 策略 2：数值归属检测
            # claim 和 source 都有某个口径词（如"峰值扭矩"），
            # 但 claim 中该词附近的数值匹配 source 中对立词（如"额定扭矩"）附近的数值
            for claim_term, source_counterpart in [(pair.term_a, pair.term_b), (pair.term_b, pair.term_a)]:
                if claim_term not in claim:
                    continue
                if source_counterpart not in source:
                    continue
                # source 同时有两个词时才需要数值归属检测
                if claim_term not in source:
                    continue  # 策略 1 已覆盖

                claim_val = self._extract_value_near_term(claim, claim_term)
                source_counter_val = self._extract_value_near_term(source, source_counterpart)
                source_same_val = self._extract_value_near_term(source, claim_term)

                # 三值齐全才判定（宁缺毋滥）：
                # - source_same_val 提取不到时（如「A、B、C 分别增长 x%、y%、z%」列举式证据，
                #   数值集中在句尾，离术语超出窗口），数值归属无法可靠判定，直接跳过。
                #   此时贸然用对立词的数值匹配会产生系统性误报（GH_006 系列）。
                if claim_val and source_counter_val and source_same_val:
                    if claim_val == source_counter_val and claim_val != source_same_val:
                        mismatches.append({
                            "claim_term": claim_term,
                            "source_term": source_counterpart,
                            "category": pair.category,
                            "severity": pair.severity,
                            "description": (
                                f"数值归属错误：claim 中「{claim_term}」附近的 {claim_val} "
                                f"匹配的是 source 中「{source_counterpart}」的值"
                            ),
                            "detection": "value_attribution",
                            "claim_value": claim_val,
                            "source_counterpart_value": source_counter_val,
                        })

        return len(mismatches) > 0, mismatches

    # ── 限定词缺失检测 ──

    # 口径词对中的限定词（如"额定扭矩"）：claim 只要用了对立词对中的
    # 任何一个（"额定扭矩"或"峰值扭矩"），口径就是明确的，
    # 不再要求 claim 同时包含另一个（GH_007_VALU 误报修复）。
    _QUALIFIER_PAIR_EXEMPTION = {
        "额定扭矩": "峰值扭矩",
        "峰值扭矩": "额定扭矩",
        "连续扭矩": "峰值扭矩",
        "累计出货": "年度出货",
        "归母净利润": "扣非净利润",
        "扣非净利润": "归母净利润",
        "扣非后净利润": "归母净利润",
        "设计产能": "实际达产产能",
    }

    def _check_qualifier_removal(self, claim: str, source: str) -> List[str]:
        """
        检测 claim 是否删掉了 source 中存在的限定词。

        逻辑：如果 source 中有某个限定词（如"同等出力情况下"），
        但 claim 中没有，则判定为限定词缺失。
        去重：如果"同等出力情况下"已匹配，不再重复匹配子串"同等出力"。
        口径对豁免：对立口径词（额定/峰值扭矩等），claim 含其一即不报另一个。
        """
        missing = []
        matched_spans = []  # 已匹配的字符区间 [(start, end), ...]

        for qualifier, reason in self.qualifier_library.items():
            if qualifier in source and qualifier not in claim:
                # 口径对豁免：claim 已包含对立口径词时，口径是明确的，不报
                counterpart = self._QUALIFIER_PAIR_EXEMPTION.get(qualifier)
                if counterpart and counterpart in claim:
                    continue

                # 检查是否是已匹配限定词的子串
                idx = source.find(qualifier)
                is_substring = any(
                    s <= idx and idx + len(qualifier) <= e
                    for s, e in matched_spans
                )
                if not is_substring:
                    missing.append(qualifier)
                    matched_spans.append((idx, idx + len(qualifier)))

        return missing

    # ── 数值矛盾检测 ──

    def _check_value_contradiction(self, claim: str, source: str) -> List[Dict]:
        """
        检测 claim 中的数值与 source 中的数值是否矛盾。

        逻辑：提取 claim 和 source 中的数值，对每个 claim 中的数值，
        检查 source 中是否存在相同数值。如果 claim 中所有数值
        都不在 source 中找到，且 source 中有数值，则可能有矛盾。

        注意：这是粗粒度检查，精确匹配交给 LLM。
        """
        if not source or not source.strip():
            return []

        # 提取数值（排除年份）
        claim_nums = set(re.findall(r'(?<!\d)(\d+\.?\d*)(?!\d)', claim))
        source_nums = set(re.findall(r'(?<!\d)(\d+\.?\d*)(?!\d)', source))

        # 排除年份
        claim_nums = {n for n in claim_nums if not re.fullmatch(r'(?:19|20)\d{2}', n)}
        source_nums = {n for n in source_nums if not re.fullmatch(r'(?:19|20)\d{2}', n)}

        # 排除单字符数值（易歧义）
        claim_nums = {n for n in claim_nums if len(n) >= 2}
        source_nums = {n for n in source_nums if len(n) >= 2}

        if not claim_nums or not source_nums:
            return []

        # claim 中的数值不在 source 中 → 可能篡改
        # 约数感知匹配：
        # - 精确数值（"额定扭矩172"）→ 严格 float 相等。不用容差——
        #   容差会让不同指标的数值交叉匹配（SH_002_VALU 中 172 与竞对
        #   扭矩密度 164.8），杀掉真正的矛盾信号。
        # - 约数数值（"超过100%"）→ ±10% 容差。约数与精确值的差异
        #   是表述粒度（"超过100%" vs 101.30%），不是篡改（SH_005_QUAL）。
        source_floats = set()
        for s in source_nums:
            try:
                source_floats.add(float(s))
            except ValueError:
                continue

        contradictions = []
        for num in claim_nums:
            if num in source_nums:
                continue
            try:
                val = float(num)
            except ValueError:
                continue

            if self._is_approx_value(claim, num):
                # 约数：±10% 容差内存在 source 值即视为匹配
                matched = any(
                    abs(float(s) - val) / max(val, 0.01) < 0.1
                    for s in source_nums
                )
            else:
                matched = val in source_floats

            if not matched:
                contradictions.append({
                    "claim_value": num,
                    "source_values": sorted(source_nums),
                    "note": f"claim 中的 {num} 在 source 中未找到匹配值",
                })

        return contradictions

    # 约数表述的模糊量词
    APPROX_MARKERS = ("超过", "大约", "左右", "以上", "以下", "约", "近", "超", "余")

    def _is_approx_value(self, text: str, num: str) -> bool:
        """判断数值在文本中是否为约数表述（前接模糊量词如"超过""约"）"""
        idx = text.find(num)
        if idx <= 0:
            return False
        prefix = text[max(0, idx - 3):idx]
        return any(m in prefix for m in self.APPROX_MARKERS)

    # ── 来源降级检测 ──

    HIGH_CREDIBILITY_KEYWORDS = ["年报", "招股书", "半年报", "季报", "公告", "研报", "证券", "券商"]
    LOW_CREDIBILITY_KEYWORDS = ["网传", "市场传闻", "股吧", "自媒体", "爆料", "未经证实"]

    def _check_source_downgrade(self, source: str) -> Tuple[bool, str]:
        """检测来源是否为低可信度"""
        if not source:
            return False, ""

        for kw in self.LOW_CREDIBILITY_KEYWORDS:
            if kw in source:
                return True, f"证据来源含低可信度关键词「{kw}」，应降低置信度"

        return False, ""

    # ── 时间错位检测 ──

    def _check_temporal_shift(self, claim: str, source: str) -> Tuple[bool, List[Dict]]:
        """
        检测 claim 中的年份是否与 source 不一致。

        逻辑：提取 claim 和 source 中的年份，
        如果 claim 的年份不在 source 的年份集合中，则可能时间错位。
        """
        if not source or not source.strip():
            return False, []

        claim_years = set(re.findall(r'(?<!\d)(20\d{2})(?!\d)', claim))
        source_years = set(re.findall(r'(?<!\d)(20\d{2})(?!\d)', source))

        if not claim_years or not source_years:
            return False, []

        # claim 中有年份不在 source 中 → 时间错位
        mismatched_years = claim_years - source_years
        if mismatched_years:
            return True, [
                {
                    "claim_year": y,
                    "source_years": sorted(source_years),
                    "note": f"claim 中的 {y} 年在 source 中未找到",
                }
                for y in sorted(mismatched_years)
            ]

        return False, []

    # ── 主验证函数 ──

    def verify(self, claim: str, source: str) -> VerificationResult:
        """
        对一条 claim + source 组合执行定义一致性验证。

        Args:
            claim: claim 文本
            source: 证据来源文本

        Returns:
            VerificationResult，包含检测结果和 verdict 覆盖建议
        """
        result = VerificationResult()

        if not source or not source.strip():
            # 无证据 → 不做规则检查，让 LLM 处理 abstain
            result.flags.append("无证据，规则层跳过")
            return result

        # ── 检测顺序即优先级（高 → 低）──
        # 口径偷换 > 数值矛盾 > 时间错位 > 来源降级 > 限定词缺失
        #
        # 限定词缺失放最后的原因：source 中的背景描述词（如"国内""关节模组"）
        # 不一定是 claim 的限定条件，误报率高且信号弱——任何更强的
        # 确定性信号（数值矛盾/时间错位/来源降级）都应优先决定 verdict。
        # 修复前限定词排第 2，会把来源降级该给的 low_confidence
        # 错误覆盖成 partially_supported（GH_004_SRCD 等误伤根因）。

        # 1. 口径偷换（最高优先级：口径错则一切比较无意义）
        has_mismatch, mismatches = self._check_definition_mismatch(claim, source)
        if has_mismatch:
            result.has_definition_mismatch = True
            result.mismatched_pairs = mismatches
            result.verdict_override = "definition_mismatch"
            result.confidence_adjustment = -0.3
            for m in mismatches:
                result.flags.append(
                    f"口径偷换：claim 用「{m['claim_term']}」，"
                    f"source 用「{m['source_term']}」（{m['category']}）"
                )

        # 2. 数值矛盾
        contradictions = self._check_value_contradiction(claim, source)
        if contradictions:
            result.value_contradictions = contradictions
            if not result.verdict_override:
                result.verdict_override = "refuted"
                result.confidence_adjustment = -0.4
            for c in contradictions:
                result.flags.append(
                    f"数值矛盾：claim 中的 {c['claim_value']} 在 source 中未找到"
                )

        # 3. 时间错位
        has_temporal, temporal_issues = self._check_temporal_shift(claim, source)
        if has_temporal:
            for t in temporal_issues:
                result.flags.append(
                    f"时间错位：claim 中的 {t['claim_year']} 年在 source 中未找到"
                )
            if not result.verdict_override:
                result.verdict_override = "refuted"
                result.confidence_adjustment = -0.3

        # 4. 来源降级（证据不可信时，基于证据的其他判断已无从谈起）
        is_low, note = self._check_source_downgrade(source)
        if is_low:
            result.has_source_downgrade = True
            result.source_note = note
            if not result.verdict_override:
                result.verdict_override = "low_confidence"
                result.confidence_adjustment = -0.3
            result.flags.append(note)

        # 5. 限定词缺失（最低优先级：弱信号，只在无任何更强信号时才决定 verdict）
        missing = self._check_qualifier_removal(claim, source)
        if missing:
            result.missing_qualifiers = missing
            if not result.verdict_override:
                result.verdict_override = "partially_supported"
                result.confidence_adjustment = -0.2
            for q in missing:
                result.flags.append(f"限定词缺失：「{q}」在 source 中存在但 claim 中缺失")

        return result

    def verify_batch(self, cases: List[Dict]) -> List[Dict]:
        """
        批量验证：对一组 {claim, source} 执行验证。

        Args:
            cases: [{"case_id": ..., "mutated_claim": ..., "mutated_source": ...}, ...]

        Returns:
            [{"case_id": ..., "verification": VerificationResult.to_dict()}, ...]
        """
        results = []
        for case in cases:
            vr = self.verify(
                case.get("mutated_claim", ""),
                case.get("mutated_source", ""),
            )
            results.append({
                "case_id": case.get("case_id", ""),
                "verification": vr.to_dict(),
            })
        return results


# ============================================================
# 快速自测
# ============================================================

if __name__ == "__main__":
    verifier = StateVerifier()

    # 测试 1: 口径偷换
    print("=== 测试 1: 口径偷换 ===")
    r = verifier.verify(
        claim="绿的谐波LHS-32谐波减速器峰值扭矩51 Nm，重量2.5 kg",
        source="【研报原文摘录】LHS-32 谐波减速器：额定扭矩 51 Nm，峰值扭矩 130 Nm，重量 2.5 kg",
    )
    print(f"  has_definition_mismatch: {r.has_definition_mismatch}")
    print(f"  verdict_override: {r.verdict_override}")
    print(f"  flags: {r.flags}")
    print()

    # 测试 2: 限定词缺失
    print("=== 测试 2: 限定词缺失 ===")
    r = verifier.verify(
        claim="绿的谐波新一代谐波减速器关节模组减重30%以上",
        source="国信证券研报：聚焦谐波减速器的轻量小型化技术突破，同等出力情况下减重30%以上",
    )
    print(f"  missing_qualifiers: {r.missing_qualifiers}")
    print(f"  verdict_override: {r.verdict_override}")
    print(f"  flags: {r.flags}")
    print()

    # 测试 3: 数值篡改
    print("=== 测试 3: 数值篡改 ===")
    r = verifier.verify(
        claim="绿的谐波2024年谐波减速器销量8.41万台，同比增长16.56%",
        source="国信证券研报：2024年谐波减速器及金属部件收入3.25亿元，谐波减速器销量24.65万台，同比增长16.56%",
    )
    print(f"  value_contradictions: {len(r.value_contradictions)}")
    print(f"  verdict_override: {r.verdict_override}")
    print(f"  flags: {r.flags}")
    print()

    # 测试 4: 来源降级
    print("=== 测试 4: 来源降级 ===")
    r = verifier.verify(
        claim="绿的谐波新一代谐波减速器关节模组在同等出力情况下减重30%以上",
        source="网传消息：聚焦谐波减速器的轻量小型化技术突破，同等出力情况下减重30%以上",
    )
    print(f"  has_source_downgrade: {r.has_source_downgrade}")
    print(f"  verdict_override: {r.verdict_override}")
    print(f"  flags: {r.flags}")
    print()

    # 测试 5: 无证据
    print("=== 测试 5: 无证据 ===")
    r = verifier.verify(
        claim="绿的谐波新一代谐波减速器关节模组在同等出力情况下减重30%以上",
        source="",
    )
    print(f"  flags: {r.flags}")
    print(f"  has_issues: {r.has_issues}")
