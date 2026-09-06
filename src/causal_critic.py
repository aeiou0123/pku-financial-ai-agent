"""
causal_critic.py — Claim2Value 因果批判层
==========================================

这是「技术创新」规则层的第四个模块，上游是 economic_mapper，
夹在「经济假设生成」与「财务模型」之间：

    经济假设（EconomicAssumption，每条带 provenance_chain / confidence）
        → 本模块以确定性规则提出替代解释与反事实证据需求
        → 调整后的有效置信度（adjusted_confidence）+ 不可归因部分
        → financial_model（消费调整后的假设）

问题：
    economic_mapper 把「扭矩密度领先 34.62%」映射为「销量上调/下调 x%」，
    这是**相关性假设**，不是因果结论。行业整体放量、竞争对手产能受限、
    价格战、口径混杂，都能产生同样的销量/ASP 变化。若不加批判层，
    财务模型会把行业β当成公司α，系统性高估技术因素的贡献。

方案：
    - 替代解释规则注册表（AlternativeRuleRegistry），模式对齐
      state_verifier 的定义注册表：每条规则有 rule_id、机制说明、
      触发条件、兼容度、置信度惩罚，可审计、可注册自定义规则；
    - 每条被触发的规则同时生成对应的反事实证据需求
      （CounterfactualRequirement），并依据调用方提供的
      available_evidence 显式判定「当前是否已满足」；
    - non_attributable 是诚实性输出：宁可保守，明确说「这部分
      不能归因于该技术因素」，给百分比区间 + 理由，不强行归因；
    - 置信度调整显式可解释：adjusted = original − Σ惩罚，
      每条惩罚记录 rule_id、幅度、理由，下限 0.1。

设计原则（对齐兄弟模块）：
    - 全程无网络、无 LLM、无第三方依赖（仅标准库）
    - 输入缺字段不崩溃，进 warnings
    - 所有规则确定性：同输入必同输出

用法：
    from src.causal_critic import CausalCritic, review

    critic = CausalCritic()
    review_result = critic.review(assumption_set)
    # review_result.reviews[i].alternative_explanations
    # review_result.reviews[i].counterfactual_requirements
    # review_result.reviews[i].adjusted_confidence
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple, Union


# ============================================================
# 兼容度与替代解释类型
# ============================================================

# 与该假设的兼容度：替代解释与「技术因素导致该经济变化」之间的关系
COMPATIBILITY = ("coexists", "mutually_exclusive", "partial_overlap")
COMPATIBILITY_LABEL = {
    "coexists": "可同时成立",           # 行业β与技术α可能同时贡献
    "mutually_exclusive": "互斥",       # 若替代解释成立则技术归因被排除
    "partial_overlap": "部分重叠",      # 两者可能各占一部分，无法完全区分
}

# 替代解释类型
ALT_TYPES = ("industry", "competitive", "policy", "metric", "other")
ALT_TYPE_LABEL = {
    "industry": "行业性",
    "competitive": "竞争性",
    "policy": "政策性",
    "metric": "口径性",
    "other": "其他",
}

# 置信度调整下限（比 economic_mapper 的 0.2 更保守，批判层允许压得更低）
_CONFIDENCE_FLOOR = 0.1


# ============================================================
# 输出结构
# ============================================================

@dataclass
class AlternativeExplanation:
    """
    一条替代解释：「该经济变化可能不是由技术因素导致，而是由……导致」。

    basis 必须可追溯：引用具体行业数据（文件名/指标/数值）或
    显式说明是常识性机制；不允许无依据的猜测。
    """
    explanation: str                  # 解释文本
    variables: List[str]              # 涉及的变量（经济变量键或工程指标名）
    compatibility: str                # coexists / mutually_exclusive / partial_overlap
    basis: str                        # 依据：行业数据引用或机制说明
    alt_type: str                     # industry / competitive / policy / metric / other
    rule_id: str                      # 触发的规则 id（可审计）
    confidence_penalty: float = 0.0   # 对原假设有效置信度的下调幅度

    def to_dict(self) -> Dict:
        return {
            "explanation": self.explanation,
            "variables": list(self.variables),
            "compatibility": self.compatibility,
            "compatibility_label": COMPATIBILITY_LABEL.get(self.compatibility, self.compatibility),
            "basis": self.basis,
            "alt_type": self.alt_type,
            "alt_type_label": ALT_TYPE_LABEL.get(self.alt_type, self.alt_type),
            "rule_id": self.rule_id,
            "confidence_penalty": self.confidence_penalty,
        }


@dataclass
class CounterfactualRequirement:
    """
    一条反事实证据需求：要确认因果归因，还缺什么证据。

    satisfied 的判定完全显式：仅当调用方在 available_evidence 中
    以该规则的 evidence_key 提供证据描述时才为 True；否则保守判 False。
    """
    requirement: str                  # 需要的证据
    purpose: str                      # 用途：排除哪个替代解释
    satisfied: bool                   # 当前是否已满足（依据 available_evidence）
    basis: str                        # 判定依据（证据描述或未满足的理由）
    priority: str                     # high / medium / low
    rule_id: str                      # 来源规则 id

    def to_dict(self) -> Dict:
        return {
            "requirement": self.requirement,
            "purpose": self.purpose,
            "satisfied": self.satisfied,
            "basis": self.basis,
            "priority": self.priority,
            "rule_id": self.rule_id,
        }


@dataclass
class NonAttributable:
    """
    不能归因于该技术因素的部分（诚实性输出，宁可保守）。

    portion_pct_range 给出保守区间：即使替代解释不成立，
    该区间的贡献也不能 confidently 记到技术因素头上。
    """
    portion_pct_range: Tuple[float, float]  # 不可归因百分比区间（0-100）
    description: str                        # 哪部分不能归因
    reason: str                             # 理由
    rule_id: str                            # 来源规则 id

    def to_dict(self) -> Dict:
        return {
            "portion_pct_range": list(self.portion_pct_range),
            "description": self.description,
            "reason": self.reason,
            "rule_id": self.rule_id,
        }


@dataclass
class AssumptionReview:
    """单条经济假设的批判性审查结果。"""
    variable: str
    variable_label: str
    rule_id: str
    qualitative_only: bool
    original_confidence: float
    adjusted_confidence: float
    confidence_adjustments: List[Dict] = field(default_factory=list)  # {rule_id, delta, reason}
    alternative_explanations: List[AlternativeExplanation] = field(default_factory=list)
    counterfactual_requirements: List[CounterfactualRequirement] = field(default_factory=list)
    non_attributable: List[NonAttributable] = field(default_factory=list)

    @property
    def open_counterfactuals(self) -> List[CounterfactualRequirement]:
        """尚未满足的反事实证据需求。"""
        return [c for c in self.counterfactual_requirements if not c.satisfied]

    def to_dict(self) -> Dict:
        return {
            "variable": self.variable,
            "variable_label": self.variable_label,
            "rule_id": self.rule_id,
            "qualitative_only": self.qualitative_only,
            "original_confidence": self.original_confidence,
            "adjusted_confidence": self.adjusted_confidence,
            "confidence_adjustments": list(self.confidence_adjustments),
            "alternative_explanations": [a.to_dict() for a in self.alternative_explanations],
            "counterfactual_requirements": [c.to_dict() for c in self.counterfactual_requirements],
            "non_attributable": [n.to_dict() for n in self.non_attributable],
            "n_open_counterfactuals": len(self.open_counterfactuals),
        }


@dataclass
class CriticReview:
    """一次完整审查的输出：逐假设审查 + 过程警告。"""
    target_company: str = ""
    reviews: List[AssumptionReview] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def total_alternatives(self) -> int:
        return sum(len(r.alternative_explanations) for r in self.reviews)

    @property
    def total_open_counterfactuals(self) -> int:
        return sum(len(r.open_counterfactuals) for r in self.reviews)

    def to_dict(self) -> Dict:
        return {
            "target_company": self.target_company,
            "reviews": [r.to_dict() for r in self.reviews],
            "warnings": list(self.warnings),
            "total_alternatives": self.total_alternatives,
            "total_open_counterfactuals": self.total_open_counterfactuals,
        }


# ============================================================
# 替代解释规则注册表
# ============================================================

@dataclass(frozen=True)
class CounterfactualTemplate:
    """规则附带的反事实证据需求模板。"""
    evidence_key: str
    requirement: str
    purpose: str
    priority: str = "medium"


@dataclass(frozen=True)
class AlternativeRule:
    """
    一条替代解释规则（确定性、可审计）。

    condition: 触发条件，接收假设的「文本视图」
    （_AssumptionView，见下），命中返回解释文本（str），
    未命中返回 None。applies_to 为空列表 = 适用于所有经济变量。
    """
    rule_id: str
    name: str
    alt_type: str
    description: str                    # 机制说明（常识性机制）
    applies_to: Tuple[str, ...]         # 适用的经济变量键；空 = 全部
    compatibility: str
    confidence_penalty: float           # 命中时对原假设置信度的下调幅度
    basis: str                          # 依据（行业数据引用或机制出处）
    condition: Callable[["_AssumptionView"], Optional[str]]
    counterfactuals: Tuple[CounterfactualTemplate, ...] = ()


class _AssumptionView:
    """
    假设的只读文本视图：把 EconomicAssumption（或其 dict 形式）的
    关键字段拼成规则条件可检索的文本，规则条件只做子串/关键词
    匹配，保持确定性。
    """

    def __init__(self, assumption: Union["EconomicAssumption", Dict, object]) -> None:
        def _get(name: str, default: object = "") -> object:
            if isinstance(assumption, dict):
                return assumption.get(name, default)
            return getattr(assumption, name, default)

        self.variable = str(_get("variable", "") or "")
        self.variable_label = str(_get("variable_label", "") or "")
        self.rule_id = str(_get("rule_id", "") or "")
        self.engineering_metric = str(_get("engineering_metric", "") or "")
        self.direction = str(_get("direction", "") or "")
        self.qualitative_only = bool(_get("qualitative_only", False))
        self.confidence = _get("confidence", 0.0)
        self.target_comparability = str(_get("target_comparability", "") or "")
        self.notes = str(_get("notes", "") or "")
        self.provenance_text = " ".join(str(p) for p in (_get("provenance_chain", []) or []))
        self.haystack = " ".join([
            self.variable, self.variable_label, self.rule_id,
            self.engineering_metric, self.notes, self.provenance_text,
        ])

    def has_any(self, keywords: Tuple[str, ...]) -> bool:
        return any(k in self.haystack for k in keywords)


# ── 内置规则的条件函数 ──

_VOLUME_KEYS = ("sales_volume", "销量", "份额", "渗透率", "share")
_ASP_KEYS = ("asp", "售价", "ASP", "价格")
_COST_KEYS = ("unit_cost", "成本")
_MARKET_KEYS = ("addressable_market", "市场分层", "可服务市场")


def _cond_industry_beta(view: _AssumptionView) -> Optional[str]:
    """行业总量增长（行业β）：销量/份额类假设永远存在行业共同因子。"""
    if view.variable == "sales_volume" or view.has_any(_VOLUME_KEYS):
        return ("行业总需求增长本身即可推高公司销量/份额，"
                "无需该公司相对技术表现发生变化")
    return None


def _cond_competitive_shift(view: _AssumptionView) -> Optional[str]:
    """竞争格局变化：竞争对手产能受限、退出或份额迁移可解释份额变化。"""
    if view.variable in ("sales_volume", "asp") or view.has_any(("市占率", "份额")):
        return ("竞争对手产能受限/退出/策略收缩可使目标公司被动获得份额，"
                "与目标公司技术领先无关")
    return None


def _cond_policy_localization(view: _AssumptionView) -> Optional[str]:
    """政策性替代：国产化率提升、供应链安全政策可独立于技术因素推动份额。"""
    if view.variable == "sales_volume" or view.has_any(_VOLUME_KEYS):
        return ("国产化替代政策与供应链本土化采购趋势可独立推动份额提升，"
                "与相对技术性能无因果关联")
    return None


def _cond_price_factor(view: _AssumptionView) -> Optional[str]:
    """价格因素：ASP/成本变化可由价格战、降价促销、原材料价格解释。"""
    if view.variable in ("asp", "unit_cost") or view.has_any(("ASP", "售价", "价格", "成本")):
        return ("价格战/降价促销/原材料价格周期可产生同样的 ASP 或成本变化，"
                "技术溢价并非唯一解释")
    return None


def _cond_metric_mix(view: _AssumptionView) -> Optional[str]:
    """口径混杂：可比性非 comparable 或 provenance 含未归一/raw/推算 时，
    观察到的「差距」部分来自口径而非真实技术差异。"""
    if view.qualitative_only:
        return None  # 定性假设由 NA-QUAL 规则覆盖，不重复惩罚
    raw_mixed = view.has_any(("未归一", "raw", "推算", "approximate", "按 approximate"))
    if view.target_comparability == "approximate" or raw_mixed:
        return ("该假设的部分样本未做口径归一（raw/推算值混入），"
                "观察到的相对差距部分来自口径差异而非真实技术差异")
    return None


# ── 内置规则表 ──

BUILTIN_RULES: Tuple[AlternativeRule, ...] = (
    AlternativeRule(
        rule_id="ALT-IND-001",
        name="行业总量增长（行业β）",
        alt_type="industry",
        description="销量类经济变量的共同上行/下行因子：行业总需求增长会推高"
                    "行业内所有公司的销量，不能把行业增量归因于单一公司的技术因素。",
        applies_to=("sales_volume",),
        compatibility="coexists",
        confidence_penalty=0.10,
        basis="常识性机制（共同因子）；industry_data_summary.csv 载有行业销量/需求"
              "增速（如中国工业机器人减速器需求量 CAGR 28.11%，2019-2023）",
        condition=_cond_industry_beta,
        counterfactuals=(
            CounterfactualTemplate(
                evidence_key="peer_volume_growth",
                requirement="同行（非目标公司）同期的销量/出货增速数据，"
                            "作为行业β对照组",
                purpose="排除「行业整体放量」替代解释：若同行增速与公司一致，"
                        "则增长主要是行业β而非公司技术α",
                priority="high",
            ),
            CounterfactualTemplate(
                evidence_key="share_counterfactual",
                requirement="「若无该技术因素」的目标公司市场份额反事实估计"
                            "（如基于历史份额趋势外推的对照）",
                purpose="分离技术因素的净贡献：份额提升超出趋势外推的部分"
                        "才可初步归因于技术因素",
                priority="high",
            ),
        ),
    ),
    AlternativeRule(
        rule_id="ALT-COMP-001",
        name="竞争格局变化",
        alt_type="competitive",
        description="竞争对手产能受限、退出、策略收缩或质量事件，可使目标公司"
                    "被动获得订单与份额；该机制与目标公司技术表现无因果关系。",
        applies_to=("sales_volume", "asp"),
        compatibility="partial_overlap",
        confidence_penalty=0.05,
        basis="competitor_market_share.csv 载有竞争格局快照（如 2021 年哈默纳科"
              "35.5% vs 绿的谐波 24.7%）；格局单点快照无法排除动态变化",
        condition=_cond_competitive_shift,
        counterfactuals=(
            CounterfactualTemplate(
                evidence_key="competitor_capacity",
                requirement="主要竞争对手同期的产能利用率、扩产/减产公告或"
                            "退出事件记录",
                purpose="排除「竞争对手产能受限」替代解释：若对手满产且份额稳定，"
                        "公司份额提升才更可能源于自身因素",
                priority="high",
            ),
        ),
    ),
    AlternativeRule(
        rule_id="ALT-POL-001",
        name="政策性替代（国产化替代）",
        alt_type="policy",
        description="国产化率政策、供应链安全审查与本土化采购趋势可独立推动"
                    "国产供应商份额提升，与相对技术性能无因果关联。",
        applies_to=("sales_volume",),
        compatibility="coexists",
        confidence_penalty=0.05,
        basis="industry_data_summary.csv 载有国产化率（2022 年 35.7% → "
              "2023 年 45.1%，单年 +9.4pct），说明政策性替代正在进行",
        condition=_cond_policy_localization,
        counterfactuals=(
            CounterfactualTemplate(
                evidence_key="policy_window",
                requirement="政策性替代的时间窗与力度证据（政策发布时点、"
                            "补贴/采购倾斜范围），及窗口外同类公司的份额表现",
                purpose="排除「政策性替代」解释：窗口外若份额提升同样发生，"
                        "政策性解释的权重下降",
                priority="medium",
            ),
        ),
    ),
    AlternativeRule(
        rule_id="ALT-PRICE-001",
        name="价格因素（价格战/原材料周期）",
        alt_type="other",
        description="ASP 变化可由价格战、降价促销、产品组合下移解释；单位成本"
                    "变化可由原材料价格周期、规模效应解释——均非技术因素。",
        applies_to=("asp", "unit_cost"),
        compatibility="partial_overlap",
        confidence_penalty=0.08,
        basis="常识性机制（价格竞争与投入品价格周期是制造业 ASP/成本变动的"
              "常规来源）",
        condition=_cond_price_factor,
        counterfactuals=(
            CounterfactualTemplate(
                evidence_key="peer_asp_change",
                requirement="同行同期 ASP 与单位成本变动对照（区分行业性价格"
                            "周期与公司特异性变化）",
                purpose="排除「价格战/原材料周期」解释：若全行业 ASP 同向变动，"
                        "技术溢价解释的权重下降",
                priority="medium",
            ),
        ),
    ),
    AlternativeRule(
        rule_id="ALT-MET-001",
        name="口径混杂",
        alt_type="metric",
        description="样本含未归一的 raw 值或推算值（可比性 approximate）时，"
                    "「相对差距」部分由口径差异贡献；把口径差异当作技术差异会"
                    "高估技术因素的因果作用。",
        applies_to=(),  # 全部定量假设
        compatibility="partial_overlap",
        confidence_penalty=0.10,
        basis="engineering_analyzer 的可比性分级：approximate 样本含推算值/"
              "口径修正，显式不确定性；口径差异贡献无法从测量差距中剥离",
        condition=_cond_metric_mix,
        counterfactuals=(
            CounterfactualTemplate(
                evidence_key="recalibrated_measurement",
                requirement="统一口径下的复测数据（同工况、同装配范围实测），"
                            "替换 raw/推算样本后重算相对差距",
                purpose="排除「口径混杂」解释：统一口径后差距若消失或显著缩小，"
                        "原归因不成立",
                priority="high",
            ),
        ),
    ),
)


# ── 不可归因判定规则（显式、保守）──

def _na_qualitative(view: _AssumptionView) -> Optional[NonAttributable]:
    """定性假设：没有定量链条，60-100% 无法归因于技术因素。"""
    if view.qualitative_only:
        return NonAttributable(
            portion_pct_range=(60.0, 100.0),
            description="整条定性假设的经济含义",
            reason="该假设未建立定量因果链（无 delta_pct），无法把任何具体"
                   "比例 confidently 归因于技术因素；保守起见不归因",
            rule_id="NA-QUAL-001",
        )
    return None


def _na_metric(view: _AssumptionView) -> Optional[NonAttributable]:
    """口径混杂：approximate 样本中 30-50% 的差距可能来自口径而非技术。"""
    if view.qualitative_only:
        return None
    if view.target_comparability == "approximate" or view.has_any(("未归一", "raw", "推算")):
        return NonAttributable(
            portion_pct_range=(30.0, 50.0),
            description="相对差距中由未归一样本贡献的部分",
            reason="目标样本可比性为 approximate（含推算值/口径修正），"
                   "口径差异贡献无法从测量差距中剥离，保守按 30-50% 不计入技术归因",
            rule_id="NA-MET-001",
        )
    return None


def _na_industry_beta(view: _AssumptionView,
                      alt_hit: bool) -> Optional[NonAttributable]:
    """行业β：销量类假设在行业上行期有 20-40% 的共性成分不可归因于公司技术。"""
    if not alt_hit:
        return None
    if view.variable == "sales_volume" or view.has_any(_VOLUME_KEYS):
        return NonAttributable(
            portion_pct_range=(20.0, 40.0),
            description="销量/份额变化中的行业共同成分（行业β）",
            reason="行业总需求增长同时抬升所有参与者；缺少同行对照证据时，"
                   "保守按 20-40% 的行业β成分不计入目标公司技术因素",
            rule_id="NA-IND-001",
        )
    return None


def _na_missing_industry_data(view: _AssumptionView) -> Optional[NonAttributable]:
    """行业数据缺失：provenance 标注缺失的引用，其支撑力不计入归因。"""
    if "行业数据缺失" in view.provenance_text:
        return NonAttributable(
            portion_pct_range=(10.0, 20.0),
            description="由缺失行业数据支撑的那部分推断",
            reason="provenance 中存在未解析的行业数据引用，该部分推断缺少"
                   "外部锚点，保守按 10-20% 不计入技术归因",
            rule_id="NA-DATA-001",
        )
    return None


NA_RULES: Tuple[Callable[..., Optional[NonAttributable]], ...] = (
    _na_qualitative,
    _na_metric,
    _na_industry_beta,
    _na_missing_industry_data,
)


# ============================================================
# 规则注册表
# ============================================================

class AlternativeRuleRegistry:
    """
    替代解释规则注册表（对齐 state_verifier 的注册表模式）。

    规则显式声明：id、机制说明、触发条件、兼容度、置信度惩罚；
    支持注册自定义规则（如针对特定政策事件或公司事件的机制），
    register() 做字段校验，重复 id 拒绝注册。
    """

    def __init__(self, rules: Optional[Tuple[AlternativeRule, ...]] = None) -> None:
        self._rules: List[AlternativeRule] = []
        for rule in (rules if rules is not None else BUILTIN_RULES):
            self.register(rule)

    def register(self, rule: AlternativeRule) -> None:
        """注册一条自定义规则；id 重复或字段非法抛 ValueError（属调用方错误）。"""
        if not rule.rule_id or not isinstance(rule.rule_id, str):
            raise ValueError("规则缺少 rule_id")
        if any(r.rule_id == rule.rule_id for r in self._rules):
            raise ValueError(f"规则 id 重复：{rule.rule_id}")
        if rule.alt_type not in ALT_TYPES:
            raise ValueError(f"规则 {rule.rule_id} alt_type 必须是 {ALT_TYPES}")
        if rule.compatibility not in COMPATIBILITY:
            raise ValueError(f"规则 {rule.rule_id} compatibility 必须是 {COMPATIBILITY}")
        if not (0.0 <= rule.confidence_penalty <= 1.0):
            raise ValueError(f"规则 {rule.rule_id} confidence_penalty 必须在 [0,1]")
        if not callable(rule.condition):
            raise ValueError(f"规则 {rule.rule_id} condition 必须可调用")
        self._rules.append(rule)

    @property
    def rules(self) -> List[AlternativeRule]:
        return list(self._rules)


def default_registry() -> AlternativeRuleRegistry:
    """内置规则注册表（5 条确定性机制规则）。"""
    return AlternativeRuleRegistry()


# ============================================================
# CausalCritic：因果批判器
# ============================================================

class CausalCritic:
    """
    经济假设的因果批判层（确定性、无 LLM、无网络）。

    对每条 EconomicAssumption 输出三部分：
    1. alternative_explanations —— 替代解释列表（内置规则 + 自定义规则触发）；
    2. counterfactual_requirements —— 反事实证据需求（含是否已满足、优先级）；
    3. non_attributable —— 不能归因于技术因素的部分（保守区间 + 理由）。

    并据此下调原假设的有效置信度（adjusted_confidence），
    调整明细逐条可解释（rule_id + 幅度 + 理由）。
    """

    def __init__(self, registry: Optional[AlternativeRuleRegistry] = None) -> None:
        self.registry = registry if registry is not None else default_registry()

    # ── 单条假设审查 ──

    def review_assumption(
        self,
        assumption: Union["EconomicAssumption", Dict, object],
        available_evidence: Optional[Dict[str, str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> AssumptionReview:
        """
        审查单条经济假设。

        Args:
            assumption: EconomicAssumption（或其 dict / 任意对象形式；
                        缺字段不崩溃，进 warnings）
            available_evidence: {evidence_key: 证据描述}，用于判定反事实
                                需求是否已满足；缺省 = 全部未满足（保守）
            warnings: 调用方的警告列表（原地追加）

        Returns:
            AssumptionReview
        """
        warn = warnings if warnings is not None else []
        view = _AssumptionView(assumption)

        if not view.variable and not view.rule_id:
            warn.append("critic：收到既无 variable 也无 rule_id 的假设，按匿名假设审查")

        original_confidence = view.confidence
        try:
            original = float(original_confidence) if original_confidence is not None else 0.0
        except (TypeError, ValueError):
            original = 0.0
            warn.append(f"critic：假设 {view.rule_id or view.variable} 的 confidence 不可解析，按 0.0 处理")
        original = max(0.0, min(1.0, original))

        review = AssumptionReview(
            variable=view.variable,
            variable_label=view.variable_label,
            rule_id=view.rule_id,
            qualitative_only=view.qualitative_only,
            original_confidence=round(original, 4),
            adjusted_confidence=round(original, 4),
        )

        # ── 替代解释规则触发 ──
        industry_beta_hit = False
        penalty_total = 0.0
        for rule in self.registry.rules:
            if rule.applies_to and view.variable not in rule.applies_to:
                continue
            hit_text = rule.condition(view)
            if hit_text is None:
                continue
            if rule.rule_id == "ALT-IND-001":
                industry_beta_hit = True
            review.alternative_explanations.append(AlternativeExplanation(
                explanation=hit_text,
                variables=[v for v in (view.variable, view.engineering_metric) if v],
                compatibility=rule.compatibility,
                basis=rule.basis,
                alt_type=rule.alt_type,
                rule_id=rule.rule_id,
                confidence_penalty=rule.confidence_penalty,
            ))
            penalty_total += rule.confidence_penalty
            review.confidence_adjustments.append({
                "rule_id": rule.rule_id,
                "delta": -rule.confidence_penalty,
                "reason": f"替代解释「{rule.name}」成立会分流对该假设的因果归因",
            })
            # ── 反事实证据需求 ──
            for template in rule.counterfactuals:
                evidence_desc = (available_evidence or {}).get(template.evidence_key)
                review.counterfactual_requirements.append(CounterfactualRequirement(
                    requirement=template.requirement,
                    purpose=template.purpose,
                    satisfied=evidence_desc is not None,
                    basis=(f"已提供证据：{evidence_desc}" if evidence_desc
                           else "未提供该对照证据（available_evidence 中无此 key），保守判未满足"),
                    priority=template.priority,
                    rule_id=rule.rule_id,
                ))

        # ── 置信度调整（显式、单调、有下限）──
        adjusted = max(_CONFIDENCE_FLOOR, round(original - penalty_total, 4))
        review.adjusted_confidence = adjusted

        # ── 不可归因部分（诚实性输出，宁可保守）──
        for na_rule in NA_RULES:
            if na_rule is _na_industry_beta:
                entry = na_rule(view, industry_beta_hit)  # type: ignore[misc]
            else:
                entry = na_rule(view)  # type: ignore[operator]
            if entry is not None:
                review.non_attributable.append(entry)

        return review

    # ── 假设集审查 ──

    def review(
        self,
        assumption_set: Union["AssumptionSet", List, Dict],
        available_evidence: Optional[Dict[str, str]] = None,
    ) -> CriticReview:
        """
        审查整个 AssumptionSet（或假设列表）。

        Args:
            assumption_set: AssumptionSet / List[EconomicAssumption] / dict；
                            非列表输入进 warning 并返回空审查
            available_evidence: {evidence_key: 证据描述}，见 review_assumption

        Returns:
            CriticReview（逐假设审查 + 警告）
        """
        result = CriticReview()
        target = ""
        assumptions: List = []

        if isinstance(assumption_set, dict):
            target = str(assumption_set.get("target_company", "") or "")
            raw = assumption_set.get("assumptions", [])
            assumptions = list(raw) if isinstance(raw, list) else []
            if not isinstance(raw, list):
                result.warnings.append("critic：dict 输入的 assumptions 字段不是列表，已忽略")
        elif isinstance(assumption_set, (list, tuple)):
            assumptions = list(assumption_set)
        else:
            target = str(getattr(assumption_set, "target_company", "") or "")
            raw = getattr(assumption_set, "assumptions", None)
            if isinstance(raw, list):
                assumptions = raw
            else:
                result.warnings.append("critic：输入缺少 assumptions 列表，返回空审查")
                result.target_company = target
                return result
            extra_warns = getattr(assumption_set, "warnings", None)
            if isinstance(extra_warns, list):
                result.warnings.extend(str(w) for w in extra_warns)

        result.target_company = target
        for assumption in assumptions:
            try:
                review = self.review_assumption(assumption, available_evidence,
                                                warnings=result.warnings)
                result.reviews.append(review)
            except Exception as exc:  # 防御：单条假设审查失败不拖垮整批
                result.warnings.append(
                    f"critic：审查假设时发生未预期错误，已跳过该条：{exc}"
                )
        return result


# ============================================================
# 便捷入口
# ============================================================

def review(
    assumption_set: Union["AssumptionSet", List, Dict],
    available_evidence: Optional[Dict[str, str]] = None,
    registry: Optional[AlternativeRuleRegistry] = None,
) -> CriticReview:
    """一次函数入口：CriticCritic(registry).review(...)。"""
    return CausalCritic(registry=registry).review(assumption_set, available_evidence)


# ============================================================
# 快速自测（真实数据端到端）
# ============================================================

if __name__ == "__main__":
    # 允许 `python src/causal_critic.py` 直接运行（与兄弟模块的 import 风格一致，
    # 仅在本模块的 __main__ 内补 repo 根路径）
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    from src.economic_mapper import load_aux_rows, map_engineering_to_economics
    from src.engineering_analyzer import load_and_normalize

    assumption_set = map_engineering_to_economics(
        load_and_normalize(), aux_rows=load_aux_rows(), target_company="绿的谐波",
    )
    result = CausalCritic().review(assumption_set)

    print(f"目标公司：{result.target_company}，审查假设 {len(result.reviews)} 条，"
          f"替代解释 {result.total_alternatives} 条，"
          f"未满足反事实需求 {result.total_open_counterfactuals} 条\n")
    for r in result.reviews:
        kind = "定性" if r.qualitative_only else "定量"
        print(f"[{r.rule_id}] {r.variable_label}（{kind}）：置信度 "
              f"{r.original_confidence} → {r.adjusted_confidence}")
        for a in r.alternative_explanations:
            print(f"  替代解释（{ALT_TYPE_LABEL[a.alt_type]}/{COMPATIBILITY_LABEL[a.compatibility]}）："
                  f"{a.explanation}")
            print(f"      依据：{a.basis}")
        for c in r.counterfactual_requirements:
            mark = "已满足" if c.satisfied else "未满足"
            print(f"  反事实需求[{c.priority}/{mark}]：{c.requirement}")
        for n in r.non_attributable:
            lo, hi = n.portion_pct_range
            print(f"  不可归因 {lo:.0f}-{hi:.0f}%：{n.description}（{n.reason}）")
        print()
    if result.warnings:
        print("警告：")
        for w in result.warnings:
            print(f"  {w}")
