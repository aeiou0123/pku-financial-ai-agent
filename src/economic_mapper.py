"""
economic_mapper.py — Claim2Value 工程结论 → 经济假设映射器
==========================================================

这是「技术创新」规则层的第三个模块，上游是 engineering_analyzer，
下游是 financial_model：

    工程参数（NormalizedParameter）
        → 本模块按 tech_to_economics_ontology.json 规则
        → 经济假设集（EconomicAssumption，每条带完整 provenance 链）
        → financial_model.FinancialModelInputs（green_harmonic_model_inputs.csv 兼容行）

问题：
    engineering_analyzer 给出的「扭矩密度领先 / 效率落后 / 精度达标」
    等工程结论，必须翻译成销量、ASP、单位成本等财务变量上的**可审计**
    假设，不能只写「技术好所以值钱」。每个数字都要能回答：
    哪个工程参数、经由哪条 ontology 规则（含弹性系数依据）、
    引用哪条行业数据、相对哪个同业基准。

方案：
    - 所有「工程指标 → 经济变量」映射规则写在
      data/processed/tech_to_economics_ontology.json 中，
      本模块零硬编码映射，只消费 ontology；
    - 每条规则显式声明：触发条件、映射方向（positive/negative）、
      默认弹性系数（带依据注释、可在 JSON 中调整）、证据强度要求；
    - 可比性硬规则：engineering_analyzer 标记 not_comparable 的行
      不得生成任何定量假设，只能产出定性说明并标注；
      approximate 行可定量但置信度强制降级；
    - 未归一化的原始 datasheet 值（efficiency/backlash/weight 等
      NormalizedParameter 未携带的指标）以 raw 通道进入，
      一律按 approximate 处理；
    - 行业数据缺失（ontology 引用的 CSV 行/文件不存在）只给 warning，
      不崩溃，假设的 provenance 中显式标注「行业数据缺失」。

与 financial_model 的衔接：
    generate_financial_model_inputs() 把假设集落到
    FinancialModelInputs 上：被调整的输入行 input_type 一律为
    "assumption"（财务模型的三分法 historical/assumption/calculated 中，
    映射输出属于人工/规则假设；calculated 结果不得写回输入表）。
    历史披露行原样保留，不参与任何调整。

设计原则（对齐兄弟模块）：
    - 全程无网络、无 LLM、无第三方依赖（仅标准库）
    - 缺失行业数据/空样本池/零基准不抛裸异常，返回带 warnings 的结构化结果
    - 数值显式四舍五入，避免浮点噪声进入下游模型

用法：
    from src.economic_mapper import (
        load_ontology, load_aux_rows, load_industry_data,
        map_engineering_to_economics, generate_financial_model_inputs,
    )
    from src.engineering_analyzer import load_and_normalize

    params = load_and_normalize()
    assumptions = map_engineering_to_economics(
        params, aux_rows=load_aux_rows(), target_company="绿的谐波",
    )
    new_inputs = generate_financial_model_inputs(
        assumptions, FinancialModelInputs.from_csv(DEFAULT_INPUT_PATH),
    )
"""

from __future__ import annotations

import csv
import json
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from src.engineering_analyzer import (
    DEFAULT_PARAMETER_CSV,
    AssemblyScope,
    Comparability,
    NormalizedParameter,
    infer_scope,
    parse_numeric,
)
from src.financial_model import FinancialModelInputs, ModelInput


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ONTOLOGY_PATH = REPO_ROOT / "data" / "processed" / "tech_to_economics_ontology.json"
DEFAULT_INDUSTRY_SUMMARY = REPO_ROOT / "data" / "processed" / "industry_data_summary.csv"
DEFAULT_SHARE_CSV = REPO_ROOT / "data" / "processed" / "competitor_market_share.csv"

FORECAST_YEARS = (2025, 2026, 2027)

# 可比性等级排序（用于 evidence_requirement 判定与置信度分级）
COMPARABILITY_RANK = {
    Comparability.COMPARABLE: 2,
    Comparability.APPROXIMATE: 1,
    Comparability.NOT_COMPARABLE: 0,
}

# 置信度基线：comparable 行从 0.8 起评，approximate 行强制降级到 0.5 起评
_CONFIDENCE_BASE = {
    Comparability.COMPARABLE: 0.8,
    Comparability.APPROXIMATE: 0.5,
}

# ontology 规则必填字段（load_ontology 校验用）
REQUIRED_RULE_FIELDS = (
    "rule_id", "name", "engineering_metric", "metric_source",
    "applicable_scopes", "trigger", "economic_variable", "direction",
    "default_elasticity", "elasticity_basis", "evidence_requirement",
    "industry_data_refs", "qualitative_note",
)

VALID_DIRECTIONS = ("positive", "negative")


# ============================================================
# 行业数据存取
# ============================================================

class IndustryData:
    """
    行业数据摘要 + 市占率两张本地 CSV 的只读视图。

    resolve(ref) 按 ontology 的 industry_data_catalog 条目定位数据行；
    文件缺失、列缺失、找不到匹配行时返回 None 并记录 warning，
    绝不抛异常（映射层对此是防御性要求）。
    """

    def __init__(self) -> None:
        self._summary: List[Dict[str, str]] = []
        self._share: List[Dict[str, str]] = []
        self.warnings: List[str] = []

    @classmethod
    def from_files(
        cls,
        summary_path: Path | str = DEFAULT_INDUSTRY_SUMMARY,
        share_path: Path | str = DEFAULT_SHARE_CSV,
    ) -> "IndustryData":
        data = cls()
        data._summary = data._read_csv(summary_path, "行业数据摘要")
        data._share = data._read_csv(share_path, "市占率表")
        return data

    def _read_csv(self, path: Path | str, label: str) -> List[Dict[str, str]]:
        path = Path(path)
        if not path.exists():
            self.warnings.append(f"{label}文件缺失：{path}，相关假设将标注「行业数据缺失」")
            return []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                self.warnings.append(f"{label}文件缺少表头：{path}")
                return []
            return [dict(row) for row in reader]

    def resolve(self, ref: Dict[str, str]) -> Tuple[Optional[str], Optional[str]]:
        """
        按 catalog 条目解析行业数据。返回 (provenance 描述, warning)；
        找不到时返回 (None, warning)。provenance 描述含文件名、键与数值。
        """
        filename = ref.get("file", "")
        metric = ref.get("metric", "")
        year = str(ref.get("year", ""))
        table = self._share if ref.get("kind") == "share" else self._summary
        for row in table:
            if row.get("metric", "").strip() != metric:
                continue
            if str(row.get("year", "")).strip() != year:
                continue
            if ref.get("kind") == "share" and row.get("company", "").strip() != ref.get("company", ""):
                continue
            value = parse_numeric(row.get("share_pct") if ref.get("kind") == "share" else row.get("value"))
            value_text = row.get("share_pct", "").strip() if ref.get("kind") == "share" else row.get("value", "").strip()
            source = row.get("source_notes", "").strip()
            if value is None:
                return None, f"行业数据行数值不可解析：{filename} {metric}/{year}"
            desc = f"行业数据：{filename} {metric}/{year}"
            if ref.get("company"):
                desc += f"/{ref['company']}"
            desc += f" = {value_text}"
            if source:
                desc += f"（{source}）"
            return desc, None
        return None, f"行业数据缺失：{filename} 中未找到 {metric}/{year}" + (
            f"/{ref.get('company')}" if ref.get("company") else ""
        )


# ============================================================
# 经济假设结构
# ============================================================

@dataclass
class EconomicAssumption:
    """
    一条「工程结论 → 经济变量」的可审计假设。

    provenance_chain 依次记录：工程参数来源（含可比性等级）→
    ontology 规则（含方向与弹性）→ 同业基准 → 行业数据，
    四段缺一不可（行业数据缺失时以显式缺失标注代替）。

    input_class 对齐 financial_model 三分法：映射输出恒为 "assumption"
    （历史披露为 historical，模型运行结果为 calculated，均不由本模块产生）。
    """
    variable: str                       # 经济变量键（ontology economic_variables 的键）
    variable_label: str
    rule_id: str
    rule_name: str
    engineering_metric: str
    direction: str                      # positive=同向 / negative=反向
    elasticity: float                   # 实际使用的弹性系数（来自 ontology，可调）
    input_class: str = "assumption"     # financial_model 三分法标注
    qualitative_only: bool = False
    # —— 定量部分（qualitative_only 时为 None）——
    engineering_value: Optional[float] = None   # 目标公司该工程指标（口径内中位）
    baseline_value: Optional[float] = None      # 财务基准值；无财务基准时为 1.0（归一乘数）
    peer_median: Optional[float] = None         # 同业基准中位数
    relative_delta: Optional[float] = None      # 工程相对差距（目标/基准 - 1）
    adjusted_value: Optional[float] = None      # 调整值 = baseline × (1 + delta_pct)
    delta_pct: Optional[float] = None           # 经济变量调整幅度（小数）
    target_comparability: Optional[str] = None  # 目标样本最差可比性等级
    evidence_grade: str = "low"                 # high / medium / low
    confidence: float = 0.0                     # 0-1
    provenance_chain: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> Dict:
        return {
            "variable": self.variable,
            "variable_label": self.variable_label,
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "engineering_metric": self.engineering_metric,
            "direction": self.direction,
            "elasticity": self.elasticity,
            "input_class": self.input_class,
            "qualitative_only": self.qualitative_only,
            "engineering_value": self.engineering_value,
            "baseline_value": self.baseline_value,
            "peer_median": self.peer_median,
            "relative_delta": self.relative_delta,
            "adjusted_value": self.adjusted_value,
            "delta_pct": self.delta_pct,
            "target_comparability": self.target_comparability,
            "evidence_grade": self.evidence_grade,
            "confidence": self.confidence,
            "provenance_chain": list(self.provenance_chain),
            "notes": self.notes,
        }


@dataclass
class AssumptionSet:
    """一次映射的完整输出：定量假设 + 定性说明 + 过程警告。"""
    target_company: str
    assumptions: List[EconomicAssumption] = field(default_factory=list)
    qualitative_notes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def quantitative(self) -> List[EconomicAssumption]:
        return [a for a in self.assumptions if not a.qualitative_only]

    def to_dict(self) -> Dict:
        return {
            "target_company": self.target_company,
            "assumptions": [a.to_dict() for a in self.assumptions],
            "qualitative_notes": list(self.qualitative_notes),
            "warnings": list(self.warnings),
        }


# ============================================================
# ontology 加载与校验
# ============================================================

def validate_ontology(ontology: Dict) -> List[str]:
    """校验 ontology 结构，返回错误列表（空列表 = 通过）。"""
    errors: List[str] = []
    if not isinstance(ontology, dict):
        return ["ontology 根节点必须是对象"]
    variables = ontology.get("economic_variables")
    if not isinstance(variables, dict) or not variables:
        errors.append("缺少 economic_variables 定义")
        variables = {}
    rules = ontology.get("rules")
    if not isinstance(rules, list) or not rules:
        errors.append("rules 必须是非空列表")
        rules = []
    for index, rule in enumerate(rules):
        label = rule.get("rule_id", f"第 {index} 条") if isinstance(rule, dict) else f"第 {index} 条"
        if not isinstance(rule, dict):
            errors.append(f"规则 {label} 不是对象")
            continue
        for key in REQUIRED_RULE_FIELDS:
            if key not in rule:
                errors.append(f"规则 {label} 缺少字段：{key}")
        if rule.get("direction") not in VALID_DIRECTIONS:
            errors.append(f"规则 {label} direction 必须是 {VALID_DIRECTIONS}")
        if rule.get("metric_source") not in ("normalized", "raw"):
            errors.append(f"规则 {label} metric_source 必须是 normalized 或 raw")
        if rule.get("economic_variable") not in variables:
            errors.append(f"规则 {label} 引用了未定义的 economic_variable：{rule.get('economic_variable')}")
        if rule.get("evidence_requirement") not in COMPARABILITY_RANK:
            errors.append(f"规则 {label} evidence_requirement 非法：{rule.get('evidence_requirement')}")
        if not isinstance(rule.get("default_elasticity"), (int, float)):
            errors.append(f"规则 {label} default_elasticity 必须是数字")
    return errors


def load_ontology(path: Path | str = DEFAULT_ONTOLOGY_PATH) -> Dict:
    """加载并校验 ontology JSON；结构错误抛 ValueError（属输入配置错误）。"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"ontology 文件不存在：{path}")
    try:
        ontology = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"ontology 不是合法 JSON：{path}：{exc}") from exc
    errors = validate_ontology(ontology)
    if errors:
        raise ValueError(f"ontology 结构错误（{path}）：" + "；".join(errors))
    return ontology


# ============================================================
# 辅助数据加载
# ============================================================

def load_aux_rows(path: Path | str = DEFAULT_PARAMETER_CSV) -> List[Dict[str, str]]:
    """
    加载 parameter_table_filled.csv 原始行（dict），
    供 metric_source="raw" 的规则取 efficiency_pct/backlash_arcsec/weight_kg
    等 NormalizedParameter 未携带的指标。文件/表头问题抛 ValueError。
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"参数表不存在：{path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"参数表为空或缺少表头：{path}")
        return [dict(row) for row in reader]


def load_industry_data(
    summary_path: Path | str = DEFAULT_INDUSTRY_SUMMARY,
    share_path: Path | str = DEFAULT_SHARE_CSV,
) -> IndustryData:
    """加载行业数据视图；文件缺失只记录 warning，不抛异常。"""
    return IndustryData.from_files(summary_path, share_path)


# ============================================================
# 样本池构建
# ============================================================

def _normalized_metric(param: NormalizedParameter, metric: str) -> Optional[float]:
    return getattr(param, metric, None)


def _raw_metric(row: Dict[str, str], metric: str) -> Optional[float]:
    return parse_numeric(row.get(metric))


def _collect_pool(
    rule: Dict,
    params: List[NormalizedParameter],
    aux_rows: List[Dict],
    target_company: str,
) -> Tuple[List[Tuple[float, Comparability, str]], List[str]]:
    """
    按规则收集（值, 可比性, 样本描述）三元组。

    返回 (池, 排除说明)。not_comparable 样本一律排除并留痕；
    raw 通道未做口径归一，一律按 APPROXIMATE 处理（显式假设）。
    """
    metric = rule["engineering_metric"]
    scopes = set(rule.get("applicable_scopes", []))
    pool: List[Tuple[float, Comparability, str]] = []
    excluded: List[str] = []

    if rule.get("metric_source") == "normalized":
        for p in params:
            if p.scope.value not in scopes:
                continue
            value = _normalized_metric(p, metric)
            if value is None:
                continue
            desc = f"{p.company} {p.model or p.product_series} = {value}（{p.comparability.value}）"
            if p.comparability == Comparability.NOT_COMPARABLE:
                excluded.append(f"not_comparable 样本已排除：{desc}")
                continue
            pool.append((value, p.comparability, desc))
    else:
        for row in aux_rows:
            company = str(row.get("company", "") or "").strip()
            scope = infer_scope(
                str(row.get("product_series", "") or ""),
                str(row.get("notes", "") or ""),
                str(row.get("model", "") or ""),
            )
            if scope.value not in scopes:
                continue
            value = _raw_metric(row, metric)
            if value is None:
                continue
            desc = f"{company} {row.get('model', '')} = {value}（raw，未归一，按 approximate 处理）"
            pool.append((value, Comparability.APPROXIMATE, desc))

    return pool, excluded


def _split_target_peers(
    pool: List[Tuple[float, Comparability, str]],
    target_company: str,
) -> Tuple[List[Tuple[float, Comparability, str]], List[Tuple[float, Comparability, str]]]:
    """按公司名前缀拆分目标样本与同业样本（参数表公司名含「/」并列写法，用前缀匹配）。"""
    target = [item for item in pool if item[2].startswith(target_company)]
    peers = [item for item in pool if not item[2].startswith(target_company)]
    return target, peers


def _confidence(worst: Comparability, n_peers: int, n_missing_refs: int) -> float:
    """
    置信度规则（显式、单调）：
      comparable 基线 0.8 / approximate 基线 0.5（强制降级）；
      同业样本 <3 个再 -0.1（小样本基准不稳）；
      每条未解析的行业数据引用 -0.05；
      截断到 [0.2, 0.95]。
    """
    base = _CONFIDENCE_BASE.get(worst, 0.3)
    score = base
    if n_peers < 3:
        score -= 0.1
    score -= 0.05 * n_missing_refs
    return max(0.2, min(0.95, round(score, 4)))


def _grade(confidence: float) -> str:
    if confidence >= 0.7:
        return "high"
    if confidence >= 0.45:
        return "medium"
    return "low"


# ============================================================
# 主映射函数
# ============================================================

def _qualitative_assumption(rule: Dict, variable_label: str, note: str,
                            provenance: List[str]) -> EconomicAssumption:
    """定性说明也落成一条 qualitative_only 假设，保证全量可追溯。"""
    return EconomicAssumption(
        variable=rule["economic_variable"],
        variable_label=variable_label,
        rule_id=rule["rule_id"],
        rule_name=rule["name"],
        engineering_metric=rule["engineering_metric"],
        direction=rule["direction"],
        elasticity=float(rule.get("default_elasticity", 0.0)),
        qualitative_only=True,
        evidence_grade="low",
        confidence=0.3,
        provenance_chain=provenance,
        notes=note,
    )


def map_engineering_to_economics(
    params: List[NormalizedParameter],
    ontology: Optional[Dict] = None,
    aux_rows: Optional[List[Dict]] = None,
    target_company: Optional[str] = None,
    industry_data: Optional[IndustryData] = None,
    financial_base: Optional[Dict[str, float]] = None,
) -> AssumptionSet:
    """
    把 engineering_analyzer 的归一化参数映射为经济假设集。

    Args:
        params: NormalizedParameter 列表（engineering_analyzer.load_and_normalize 输出）
        ontology: 规则集；None 时加载默认 tech_to_economics_ontology.json
        aux_rows: 原始参数行（dict），供 raw 规则取效率/背隙/重量等指标；
                  None 时 raw 规则只产出定性说明
        target_company: 目标公司；None 时用 ontology 的 target_company_default
        industry_data: 行业数据视图；None 时加载默认 CSV（缺失只 warning）
        financial_base: 可选，财务指标 → 基准值（如从 FinancialModelInputs 取
                        2025 年假设），用于填充假设的 baseline_value/adjusted_value；
                        不提供时基准记为 1.0 归一乘数

    Returns:
        AssumptionSet，含定量假设、定性说明与过程警告。
        可比性硬规则：not_comparable 样本不得进入任何定量假设；
        approximate 样本可定量但置信度基线从 0.5 起评（强制降级）。
    """
    if ontology is None:
        ontology = load_ontology()
    if target_company is None:
        target_company = ontology.get("target_company_default", "")
    if industry_data is None:
        industry_data = IndustryData.from_files()

    variables: Dict[str, Dict] = ontology.get("economic_variables", {})
    catalog: Dict[str, Dict] = ontology.get("industry_data_catalog", {})
    result = AssumptionSet(target_company=target_company)
    result.warnings.extend(industry_data.warnings)

    for rule in ontology.get("rules", []):
        _map_one_rule(rule, variables, catalog, params, aux_rows or [],
                      target_company, industry_data, financial_base, result)

    return result


def _map_one_rule(
    rule: Dict,
    variables: Dict[str, Dict],
    catalog: Dict[str, Dict],
    params: List[NormalizedParameter],
    aux_rows: List[Dict],
    target_company: str,
    industry_data: IndustryData,
    financial_base: Optional[Dict[str, float]],
    result: AssumptionSet,
) -> None:
    """单条规则映射；所有失败路径只降级为定性说明 + warning，不中断。"""
    variable_key = rule["economic_variable"]
    variable = variables.get(variable_key, {})
    variable_label = variable.get("label", variable_key)

    pool, excluded = _collect_pool(rule, params, aux_rows, target_company)
    result.warnings.extend(excluded)
    target_pool, peer_pool = _split_target_peers(pool, target_company)

    head_provenance = [f"ontology 规则 {rule['rule_id']}（{rule['name']}）："
                       f"方向 {rule['direction']}，弹性 {rule['default_elasticity']}"]
    qualitative_text = f"{rule['qualitative_note']}（目标公司：{target_company or '未指定'}）"

    def _to_qualitative(note: str, extra: Optional[List[str]] = None) -> None:
        provenance = list(head_provenance) + (extra or [])
        assumption = _qualitative_assumption(rule, variable_label, note, provenance)
        result.assumptions.append(assumption)
        result.qualitative_notes.append(f"[{rule['rule_id']}] {note}")

    # —— 定性专用变量 / 规则：直接落定性说明 ——
    if rule.get("qualitative_only") or variable.get("qualitative_only"):
        _to_qualitative(qualitative_text, [f"样本池共 {len(pool)} 个（目标 {len(target_pool)} / 同业 {len(peer_pool)}）"])
        return

    # —— 硬规则：目标池为空（全部 not_comparable / 缺失 / 未提供 aux）——
    if not target_pool:
        note = (f"目标公司无可用定量样本（not_comparable 或指标缺失），"
                f"按硬规则不生成定量假设；{qualitative_text}")
        _to_qualitative(note)
        result.warnings.append(f"规则 {rule['rule_id']}：目标公司 {target_company} 无定量样本，已降级为定性说明")
        return
    if not peer_pool:
        note = f"无同口径同业样本可建基准，无法计算相对差距；{qualitative_text}"
        _to_qualitative(note)
        result.warnings.append(f"规则 {rule['rule_id']}：同业样本池为空，已降级为定性说明")
        return

    # —— 触发守卫（如背隙高端门槛）：不达标只给定性说明 ——
    trigger = rule.get("trigger", {})
    guard = trigger.get("quantify_guard") if isinstance(trigger, dict) else None
    target_median = statistics.median([v for v, _, _ in target_pool])
    if guard and target_median > float(guard.get("max_value", float("inf"))):
        note = (f"目标样本中位值 {target_median} 未达定量门槛"
                f"（≤{guard.get('max_value')} {guard.get('unit', '')}，{guard.get('note', '')}）；"
                f"{qualitative_text}")
        _to_qualitative(note)
        return

    # —— 证据强度要求：目标样本最差可比性低于要求 → 降级定性 ——
    worst = min((c for _, c, _ in target_pool), key=lambda c: COMPARABILITY_RANK[c])
    requirement = Comparability(rule["evidence_requirement"])
    if COMPARABILITY_RANK[worst] < COMPARABILITY_RANK[requirement]:
        note = (f"目标样本最差可比性 {worst.value} 低于规则证据要求 {requirement.value}，"
                f"按硬规则不生成定量假设；{qualitative_text}")
        _to_qualitative(note, [f"目标样本：{[d for _, _, d in target_pool]}"])
        result.warnings.append(f"规则 {rule['rule_id']}：证据强度不足（{worst.value} < {requirement.value}），已降级")
        return

    # —— 定量映射 ——
    peer_median = statistics.median([v for v, _, _ in peer_pool])
    if peer_median == 0:
        _to_qualitative("同业基准中位数为 0，相对差距无定义，降级为定性说明")
        result.warnings.append(f"规则 {rule['rule_id']}：同业基准为 0，无法计算相对差距")
        return
    relative_delta = target_median / peer_median - 1.0
    sign = 1.0 if rule["direction"] == "positive" else -1.0
    elasticity = float(rule["default_elasticity"])
    delta_pct = round(relative_delta * elasticity * sign, 6)

    # 行业数据引用解析（缺失 → provenance 显式标注 + 置信度惩罚）
    ref_provenance: List[str] = []
    missing_refs = 0
    for ref_key in rule.get("industry_data_refs", []):
        ref = catalog.get(ref_key)
        if ref is None:
            missing_refs += 1
            ref_provenance.append(f"行业数据缺失：catalog 中无条目 {ref_key}")
            result.warnings.append(f"规则 {rule['rule_id']}：catalog 缺少条目 {ref_key}")
            continue
        desc, warn = industry_data.resolve(ref)
        if desc is None:
            missing_refs += 1
            ref_provenance.append(f"行业数据缺失：{ref_key}（{warn}）")
            result.warnings.append(f"规则 {rule['rule_id']}：{warn}")
        else:
            ref_provenance.append(desc)

    confidence = _confidence(worst, len(peer_pool), missing_refs)

    # 财务基准（可选）：取该变量映射的第一个财务指标在 financial_base 中的值
    fin_metrics = variable.get("financial_metrics", {})
    base_value: Optional[float] = None
    if financial_base and fin_metrics:
        for metric_name in fin_metrics.values():
            if metric_name in financial_base:
                base_value = float(financial_base[metric_name])
                break
    if base_value is None:
        base_value = 1.0  # 归一乘数基准
    adjusted = round(base_value * (1.0 + delta_pct), 6)

    provenance = [
        f"工程参数：{target_company} {rule['engineering_metric']} 中位 {target_median}"
        f"（样本 {len(target_pool)} 个，最差可比性 {worst.value}）",
    ] + head_provenance + [
        f"同业基准：同口径样本 {len(peer_pool)} 个，中位 {peer_median}，相对差距 {relative_delta:+.2%}",
    ] + ref_provenance + [
        f"弹性换算：{relative_delta:+.2%} × {elasticity} × 方向{'+' if sign > 0 else '-'} = {delta_pct:+.2%}",
    ]

    assumption = EconomicAssumption(
        variable=variable_key,
        variable_label=variable_label,
        rule_id=rule["rule_id"],
        rule_name=rule["name"],
        engineering_metric=rule["engineering_metric"],
        direction=rule["direction"],
        elasticity=elasticity,
        qualitative_only=False,
        engineering_value=round(target_median, 6),
        baseline_value=base_value,
        peer_median=round(peer_median, 6),
        relative_delta=round(relative_delta, 6),
        adjusted_value=adjusted,
        delta_pct=delta_pct,
        target_comparability=worst.value,
        evidence_grade=_grade(confidence),
        confidence=confidence,
        provenance_chain=provenance,
        notes=(f"{qualitative_text}；证据等级 {_grade(confidence)}，"
               f"置信度 {confidence}（可比性 {worst.value}，同业样本 {len(peer_pool)} 个，"
               f"行业数据缺失 {missing_refs} 条）"),
    )
    result.assumptions.append(assumption)


# ============================================================
# 财务模型衔接
# ============================================================

def _combined_deltas(assumption_set: AssumptionSet) -> Dict[str, float]:
    """同一经济变量的多条定量假设按乘法复合：(1+d1)(1+d2)-1。"""
    combined: Dict[str, float] = {}
    for assumption in assumption_set.quantitative():
        previous = combined.get(assumption.variable, 0.0)
        combined[assumption.variable] = round((1.0 + previous) * (1.0 + assumption.delta_pct) - 1.0, 8)
    return combined


def generate_financial_model_inputs(
    assumption_set: AssumptionSet,
    base_inputs: FinancialModelInputs,
    ontology: Optional[Dict] = None,
    years: Sequence[int] = FORECAST_YEARS,
    product_lines: Sequence[str] = ("harmonic", "joint"),
) -> FinancialModelInputs:
    """
    把经济假设集落到 financial_model 的输入格式。

    - 被调整的行 input_type 恒为 "assumption"（三分法：映射输出属规则/人工假设，
      historical 行原样保留，calculated 结果不得写回输入表——本函数不产生后者）；
    - 同一经济变量多条假设乘法复合后，施加到该变量在 ontology 中声明的
      各产品线财务指标（默认 harmonic + joint 同时调整）；
    - 调整行的 source 记为 economic_mapper，source_locator 指向 ontology
      文件与规则 id，notes 记录调整幅度，保证可审计；
    - 未被任何规则覆盖的行（费率、估值参数、历史披露）原样复制。
    """
    if ontology is None:
        ontology = load_ontology()
    variables: Dict[str, Dict] = ontology.get("economic_variables", {})
    deltas = _combined_deltas(assumption_set)
    year_set = {str(y) for y in years}

    # 财务指标 → (经济变量, 涉及的规则 id)
    metric_to_variable: Dict[str, Tuple[str, List[str]]] = {}
    for assumption in assumption_set.quantitative():
        fin_metrics = variables.get(assumption.variable, {}).get("financial_metrics", {})
        for line in product_lines:
            metric_name = fin_metrics.get(line)
            if not metric_name:
                continue
            entry = metric_to_variable.setdefault(metric_name, (assumption.variable, []))
            if assumption.rule_id not in entry[1]:
                entry[1].append(assumption.rule_id)

    new_rows: List[ModelInput] = []
    for row in base_inputs.rows:
        target = metric_to_variable.get(row.metric)
        if target is None or row.year not in year_set:
            new_rows.append(row)  # 未覆盖行原样保留（含 historical 披露锚点）
            continue
        variable_key, rule_ids = target
        delta = deltas[variable_key]
        new_rows.append(ModelInput(
            metric=row.metric,
            year=row.year,
            value=round(row.value * (1.0 + delta), 6),
            unit=row.unit,
            input_type="assumption",
            source="economic_mapper",
            source_locator=f"data/processed/tech_to_economics_ontology.json#{','.join(sorted(rule_ids))}",
            notes=(f"economic_mapper 按规则调整 {delta:+.2%}（原值 {row.value}，"
                   f"目标公司 {assumption_set.target_company}）；详见 src/economic_mapper.py"),
        ))
    return FinancialModelInputs(new_rows)


def export_model_inputs_csv(inputs: FinancialModelInputs, path: Path | str) -> Path:
    """按 green_harmonic_model_inputs.csv 的 8 列格式导出，可直接被 financial_model 读取。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = ["metric", "year", "value", "unit", "input_type", "source", "source_locator", "notes"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for record in inputs.as_records():
            writer.writerow(record)
    return path


# ============================================================
# 快速自测
# ============================================================

if __name__ == "__main__":
    from src.engineering_analyzer import load_and_normalize
    from src.financial_model import DEFAULT_INPUT_PATH, FinancialModelInputs, run_model

    ontology = load_ontology()
    params = load_and_normalize()
    assumptions = map_engineering_to_economics(
        params, ontology=ontology, aux_rows=load_aux_rows(),
        financial_base={"harmonic_units_wan": 130, "harmonic_asp_yuan": 1150,
                        "harmonic_unit_cost_yuan": 580},
    )
    print(f"目标公司：{assumptions.target_company}，假设 {len(assumptions.assumptions)} 条"
          f"（定量 {len(assumptions.quantitative())} 条），警告 {len(assumptions.warnings)} 条\n")
    for a in assumptions.assumptions:
        kind = "定性" if a.qualitative_only else f"{a.delta_pct:+.2%}"
        print(f"[{a.rule_id}] {a.variable_label} → {kind}（证据 {a.evidence_grade}，置信度 {a.confidence}）")
        for step in a.provenance_chain:
            print(f"    {step}")

    base = FinancialModelInputs.from_csv(DEFAULT_INPUT_PATH)
    adjusted = generate_financial_model_inputs(assumptions, base, ontology=ontology)
    adjusted.validate(FORECAST_YEARS)
    before = run_model(base, "base")["projections"][0]["revenue_bn"]
    after = run_model(adjusted, "base")["projections"][0]["revenue_bn"]
    print(f"\n财务模型衔接：2025 收入 {before:.4f} → {after:.4f} bn CNY（validate 通过）")
