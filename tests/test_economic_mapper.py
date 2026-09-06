import unittest
from pathlib import Path

from src.economic_mapper import (
    AssumptionSet,
    IndustryData,
    generate_financial_model_inputs,
    load_aux_rows,
    load_industry_data,
    load_ontology,
    map_engineering_to_economics,
    validate_ontology,
)
from src.engineering_analyzer import (
    AssemblyScope,
    Comparability,
    NormalizedParameter,
    load_and_normalize,
)
from src.financial_model import (
    DEFAULT_INPUT_PATH,
    FORECAST_YEARS,
    FinancialModelInputs,
    run_model,
)


def _param(company, model, metric_value, comparability, scope=AssemblyScope.GEAR_UNIT,
           metric="torque_density_nm_kg"):
    """构造一个带指定可比性的 NormalizedParameter 测试样本。"""
    param = NormalizedParameter(
        company=company, product_series="LHS", model=model, scope=scope,
        comparability=comparability,
    )
    setattr(param, metric, metric_value)
    return param


class OntologyTests(unittest.TestCase):
    def test_default_ontology_loads(self):
        ontology = load_ontology()
        self.assertEqual(ontology["ontology_id"], "tech_to_economics")
        self.assertGreaterEqual(len(ontology["rules"]), 5)

    def test_rule_fields_are_complete(self):
        ontology = load_ontology()
        self.assertEqual(validate_ontology(ontology), [])
        directions = {"positive", "negative"}
        for rule in ontology["rules"]:
            for key in ("rule_id", "name", "engineering_metric", "trigger",
                        "economic_variable", "direction", "default_elasticity",
                        "elasticity_basis", "evidence_requirement",
                        "industry_data_refs", "qualitative_note"):
                self.assertIn(key, rule, f"规则 {rule.get('rule_id')} 缺少 {key}")
            self.assertIn(rule["direction"], directions)
            self.assertIsInstance(rule["default_elasticity"], (int, float))
            self.assertGreater(len(rule["elasticity_basis"]), 20, "弹性系数必须带依据注释")
            self.assertIn(rule["metric_source"], ("normalized", "raw"))
            self.assertIn(rule["economic_variable"], ontology["economic_variables"])

    def test_invalid_ontology_is_rejected(self):
        ontology = load_ontology()
        broken = dict(ontology)
        broken["rules"] = [dict(ontology["rules"][0])]
        del broken["rules"][0]["default_elasticity"]
        errors = validate_ontology(broken)
        self.assertTrue(any("default_elasticity" in e for e in errors))


class MappingProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.ontology = load_ontology()
        self.params = load_and_normalize()
        self.aux_rows = load_aux_rows()
        self.industry = load_industry_data()

    def test_single_parameter_maps_with_full_provenance(self):
        result = map_engineering_to_economics(
            self.params, ontology=self.ontology, aux_rows=self.aux_rows,
            target_company="绿的谐波", industry_data=self.industry,
        )
        self.assertIsInstance(result, AssumptionSet)
        torque = [a for a in result.quantitative()
                  if a.rule_id == "torque_density_to_share"]
        self.assertEqual(len(torque), 1)
        assumption = torque[0]
        self.assertEqual(assumption.variable, "sales_volume")
        self.assertEqual(assumption.input_class, "assumption")
        self.assertAlmostEqual(assumption.engineering_value, 20.4)
        self.assertAlmostEqual(assumption.elasticity, 0.30)
        self.assertAlmostEqual(
            assumption.delta_pct,
            (20.4 / 31.2 - 1.0) * 0.30, places=6,
        )
        # 依据链四段齐全：工程参数 / ontology 规则 / 同业基准 / 行业数据
        chain = "\n".join(assumption.provenance_chain)
        self.assertIn("工程参数", chain)
        self.assertIn("ontology 规则 torque_density_to_share", chain)
        self.assertIn("同业基准", chain)
        self.assertIn("行业数据", chain)
        self.assertIn("绿的谐波", chain)

    def test_not_comparable_is_hard_excluded_from_quantitative(self):
        # 目标公司唯一的扭矩密度样本标 not_comparable：必须只出定性说明
        bad = _param("测试公司", "X-1", 99.0, Comparability.NOT_COMPARABLE)
        good_peer = _param("同业甲", "Y-1", 30.0, Comparability.COMPARABLE)
        result = map_engineering_to_economics(
            [bad, good_peer], ontology=self.ontology,
            aux_rows=[], target_company="测试公司", industry_data=self.industry,
        )
        self.assertEqual(result.quantitative(), [])
        related = [a for a in result.assumptions
                   if a.rule_id == "torque_density_to_share"]
        self.assertEqual(len(related), 1)
        self.assertTrue(related[0].qualitative_only)
        self.assertEqual(related[0].evidence_grade, "low")
        self.assertTrue(any("not_comparable" in w or "无可用定量样本" in w
                            for w in result.warnings))

    def test_not_comparable_does_not_pollute_peer_baseline(self):
        # not_comparable 的同业样本不得进入基准中位数
        target = _param("测试公司", "X-1", 20.0, Comparability.COMPARABLE)
        peer_ok = _param("同业甲", "Y-1", 30.0, Comparability.COMPARABLE)
        peer_bad = _param("同业乙", "Z-1", 999.0, Comparability.NOT_COMPARABLE)
        result = map_engineering_to_economics(
            [target, peer_ok, peer_bad], ontology=self.ontology,
            aux_rows=[], target_company="测试公司", industry_data=self.industry,
        )
        assumption = [a for a in result.quantitative()
                      if a.rule_id == "torque_density_to_share"][0]
        self.assertAlmostEqual(assumption.peer_median, 30.0)
        self.assertTrue(any("not_comparable" in w for w in result.warnings))

    def test_approximate_downgrades_confidence(self):
        params = load_and_normalize()
        target = _param("测试公司", "X-1", 20.0, Comparability.COMPARABLE)
        peer = _param("同业甲", "Y-1", 30.0, Comparability.COMPARABLE)
        base = map_engineering_to_economics(
            [target, peer], ontology=self.ontology, aux_rows=[],
            target_company="测试公司", industry_data=self.industry,
        )
        approx_param = _param("测试公司", "X-1", 20.0, Comparability.APPROXIMATE)
        approx = map_engineering_to_economics(
            [approx_param, peer], ontology=self.ontology, aux_rows=[],
            target_company="测试公司", industry_data=self.industry,
        )
        base_a = [a for a in base.quantitative()
                  if a.rule_id == "torque_density_to_share"][0]
        approx_a = [a for a in approx.quantitative()
                    if a.rule_id == "torque_density_to_share"][0]
        self.assertEqual(base_a.evidence_grade, "high")
        self.assertLess(approx_a.confidence, base_a.confidence)
        self.assertIn(approx_a.evidence_grade, ("medium", "low"))
        # 数值相同，仅可比性不同 → 调整幅度一致，差异只在证据/置信度
        self.assertAlmostEqual(approx_a.delta_pct, base_a.delta_pct)

    def test_missing_industry_data_warns_but_does_not_crash(self):
        empty = IndustryData.from_files(
            summary_path=Path("data/processed/__不存在__.csv"),
            share_path=Path("data/processed/__不存在__.csv"),
        )
        self.assertTrue(empty.warnings)
        result = map_engineering_to_economics(
            self.params, ontology=self.ontology, aux_rows=self.aux_rows,
            target_company="绿的谐波", industry_data=empty,
        )
        # 行业数据全部缺失：假设仍在，provenance 显式标注缺失，置信度被惩罚
        torque = [a for a in result.quantitative()
                  if a.rule_id == "torque_density_to_share"][0]
        self.assertIn("行业数据缺失", "\n".join(torque.provenance_chain))
        self.assertLess(torque.confidence, 0.8)
        full = map_engineering_to_economics(
            self.params, ontology=self.ontology, aux_rows=self.aux_rows,
            target_company="绿的谐波", industry_data=load_industry_data(),
        )
        full_torque = [a for a in full.quantitative()
                       if a.rule_id == "torque_density_to_share"][0]
        self.assertGreater(torque.confidence + 0.05, full_torque.confidence - 0.2)
        self.assertTrue(any("行业数据缺失" in w for w in result.warnings))

    def test_missing_aux_rows_fall_back_to_qualitative(self):
        # 不传 aux_rows：raw 规则不得崩溃，只能产出定性说明
        result = map_engineering_to_economics(
            self.params, ontology=self.ontology, aux_rows=None,
            target_company="绿的谐波", industry_data=self.industry,
        )
        raw_rules = {r["rule_id"] for r in self.ontology["rules"]
                     if r["metric_source"] == "raw" and not r.get("qualitative_only")}
        produced = {a.rule_id for a in result.assumptions}
        self.assertTrue(raw_rules.issubset(produced))
        for rule_id in raw_rules:
            related = [a for a in result.assumptions if a.rule_id == rule_id]
            self.assertTrue(all(a.qualitative_only for a in related))


class FinancialModelIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.ontology = load_ontology()
        self.base = FinancialModelInputs.from_csv(DEFAULT_INPUT_PATH)

    def test_generated_inputs_are_financial_model_compatible(self):
        params = load_and_normalize()
        assumptions = map_engineering_to_economics(
            params, ontology=self.ontology, aux_rows=load_aux_rows(),
            target_company="绿的谐波",
        )
        adjusted = generate_financial_model_inputs(assumptions, self.base, self.ontology)
        self.assertIsInstance(adjusted, FinancialModelInputs)
        # 关键：能通过 financial_model 的完整性校验并真实跑通三情景
        adjusted.validate(FORECAST_YEARS)
        base_result = run_model(self.base, "base")
        adjusted_result = run_model(adjusted, "base")
        self.assertNotAlmostEqual(
            adjusted_result["projections"][0]["revenue_bn"],
            base_result["projections"][0]["revenue_bn"],
        )
        # 历史披露行原样保留，未被映射污染
        historical = [r for r in adjusted.rows if r.input_type == "historical"]
        self.assertGreaterEqual(len(historical), 2)
        # 被调整的行全部标注为 assumption 且带来源定位
        changed = [r for r in adjusted.rows if r.source == "economic_mapper"]
        self.assertTrue(changed)
        for row in changed:
            self.assertEqual(row.input_type, "assumption")
            self.assertIn("tech_to_economics_ontology.json", row.source_locator)

    def test_qualitative_only_assumptions_do_not_touch_model(self):
        # 目标公司无任何可比样本：全部规则降级为定性，模型输入应保持不变
        params = load_and_normalize()
        assumptions = map_engineering_to_economics(
            params, ontology=self.ontology, aux_rows=load_aux_rows(),
            target_company="与参数表无关的公司",
        )
        adjusted = generate_financial_model_inputs(assumptions, self.base, self.ontology)
        self.assertEqual(
            [(r.metric, r.year, r.value) for r in adjusted.rows],
            [(r.metric, r.year, r.value) for r in self.base.rows],
        )


if __name__ == "__main__":
    unittest.main()
