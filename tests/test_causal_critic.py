import unittest

from src.causal_critic import (
    ALT_TYPES,
    BUILTIN_RULES,
    COMPATIBILITY,
    AlternativeRule,
    AlternativeRuleRegistry,
    CausalCritic,
    CounterfactualTemplate,
    default_registry,
    review,
)
from src.economic_mapper import (
    EconomicAssumption,
    load_aux_rows,
    map_engineering_to_economics,
)
from src.engineering_analyzer import load_and_normalize


def _assumption(**overrides):
    """构造一条带默认值的经济假设，字段可被测试覆盖。"""
    base = dict(
        variable="sales_volume",
        variable_label="销量（份额/渗透率）",
        rule_id="test_rule",
        rule_name="测试规则",
        engineering_metric="torque_density_nm_kg",
        direction="positive",
        elasticity=0.3,
        qualitative_only=False,
        confidence=0.8,
        target_comparability="comparable",
        provenance_chain=[
            "工程参数：绿的谐波 torque_density_nm_kg 中位 20.4（样本 1 个）",
            "同业基准：中位 31.2，相对差距 -34.62%",
        ],
        notes="测试假设",
    )
    base.update(overrides)
    return EconomicAssumption(**base)


class BuiltinRuleTests(unittest.TestCase):
    def test_builtin_rules_are_auditable(self):
        """内置规则清单：每条都有 id、说明、触发条件、兼容度、惩罚、依据。"""
        self.assertGreaterEqual(len(BUILTIN_RULES), 5)
        for rule in BUILTIN_RULES:
            self.assertTrue(rule.rule_id.startswith("ALT-"), rule.rule_id)
            self.assertGreater(len(rule.description), 10, rule.rule_id)
            self.assertIn(rule.alt_type, ALT_TYPES, rule.rule_id)
            self.assertIn(rule.compatibility, COMPATIBILITY, rule.rule_id)
            self.assertGreater(rule.confidence_penalty, 0.0, rule.rule_id)
            self.assertGreater(len(rule.basis), 10, f"{rule.rule_id} 缺少依据")
            self.assertTrue(callable(rule.condition), rule.rule_id)

    def test_builtin_mechanism_types_cover_at_least_three(self):
        """内置规则至少覆盖 3 类机制（行业性/竞争性/政策性/口径性）。"""
        types = {r.alt_type for r in BUILTIN_RULES}
        self.assertGreaterEqual(len(types - {"other"}), 3, types)

    def test_registry_rejects_duplicate_and_invalid(self):
        registry = default_registry()
        n = len(registry.rules)
        with self.assertRaises(ValueError):
            registry.register(BUILTIN_RULES[0])  # 重复 id
        bad = AlternativeRule(
            rule_id="ALT-X-001", name="坏规则", alt_type="不存在的类型",
            description="x" * 20, applies_to=(), compatibility="coexists",
            confidence_penalty=0.1, basis="x" * 20,
            condition=lambda view: "hit",
        )
        with self.assertRaises(ValueError):
            registry.register(bad)
        self.assertEqual(len(registry.rules), n)

    def test_custom_rule_can_be_registered(self):
        registry = default_registry()
        custom = AlternativeRule(
            rule_id="ALT-CUST-001", name="人形机器人行业事件", alt_type="industry",
            description="下游人形机器人客户集中放量可独立解释销量假设上行" + "。" * 5,
            applies_to=("sales_volume",), compatibility="coexists",
            confidence_penalty=0.07,
            basis="常识性机制：单一大客户订单节奏主导供应商出货",
            condition=lambda view: "hit" if view.variable == "sales_volume" else None,
            counterfactuals=(CounterfactualTemplate(
                evidence_key="customer_order_split",
                requirement="分客户订单拆分，分离单一客户放量的贡献",
                purpose="排除「单一大客户放量」解释",
                priority="high",
            ),),
        )
        registry.register(custom)
        critic = CausalCritic(registry=registry)
        result = critic.review([_assumption()])
        hits = [a for r in result.reviews
                for a in r.alternative_explanations if a.rule_id == "ALT-CUST-001"]
        self.assertEqual(len(hits), 1)
        cfs = [c for r in result.reviews
               for c in r.counterfactual_requirements if c.rule_id == "ALT-CUST-001"]
        self.assertEqual(len(cfs), 1)
        self.assertFalse(cfs[0].satisfied)


class AlternativeExplanationTests(unittest.TestCase):
    def test_sales_volume_triggers_industry_competitive_policy(self):
        """销量假设触发行业性、竞争性、政策性三类替代解释。"""
        result = CausalCritic().review([_assumption()])
        types = {a.alt_type for a in result.reviews[0].alternative_explanations}
        self.assertIn("industry", types)
        self.assertIn("competitive", types)
        self.assertIn("policy", types)

    def test_asp_triggers_price_factor(self):
        asp = _assumption(variable="asp", variable_label="平均售价（ASP）",
                          engineering_metric="backlash_arcsec")
        result = CausalCritic().review([asp])
        types = {a.alt_type for a in result.reviews[0].alternative_explanations}
        self.assertIn("other", types)  # 价格因素规则 alt_type=other
        self.assertNotIn("industry", types)  # 行业β规则只作用于 sales_volume

    def test_unit_cost_triggers_price_and_metric(self):
        cost = _assumption(variable="unit_cost", variable_label="单位成本",
                           engineering_metric="weight_kg",
                           target_comparability="approximate",
                           provenance_chain=["工程参数：raw，未归一，按 approximate 处理"])
        result = CausalCritic().review([cost])
        types = {a.alt_type for a in result.reviews[0].alternative_explanations}
        self.assertIn("other", types)   # 价格因素
        self.assertIn("metric", types)  # 口径混杂

    def test_comparable_assumption_does_not_trigger_metric_rule(self):
        result = CausalCritic().review([_assumption(target_comparability="comparable")])
        metric_hits = [a for a in result.reviews[0].alternative_explanations
                       if a.alt_type == "metric"]
        self.assertEqual(metric_hits, [])

    def test_explanation_fields_complete(self):
        result = CausalCritic().review([_assumption()])
        for alt in result.reviews[0].alternative_explanations:
            self.assertTrue(alt.explanation)
            self.assertTrue(alt.variables)
            self.assertTrue(alt.basis)
            self.assertIn(alt.compatibility, COMPATIBILITY)
            self.assertIn(alt.alt_type, ALT_TYPES)


class CounterfactualTests(unittest.TestCase):
    def test_counterfactuals_generated_with_priorities(self):
        result = CausalCritic().review([_assumption()])
        cfs = result.reviews[0].counterfactual_requirements
        self.assertGreaterEqual(len(cfs), 3)
        for cf in cfs:
            self.assertIn(cf.priority, ("high", "medium", "low"))
            self.assertTrue(cf.requirement)
            self.assertTrue(cf.purpose)
            self.assertTrue(cf.rule_id)

    def test_unsatisfied_by_default_is_conservative(self):
        """不提供 available_evidence 时，所有反事实需求保守判未满足。"""
        result = CausalCritic().review([_assumption()])
        self.assertGreater(len(result.reviews[0].open_counterfactuals), 0)
        for cf in result.reviews[0].counterfactual_requirements:
            self.assertFalse(cf.satisfied)
            self.assertIn("未提供", cf.basis)

    def test_satisfied_with_available_evidence(self):
        evidence = {
            "peer_volume_growth": "环动科技/来福谐波 2024 出货增速 +12%",
            "share_counterfactual": "按 2019-2023 份额趋势外推的对照份额",
        }
        result = CausalCritic().review([_assumption()], available_evidence=evidence)
        by_key = {(c.rule_id, c.requirement): c
                  for c in result.reviews[0].counterfactual_requirements}
        satisfied = [c for c in by_key.values() if c.satisfied]
        self.assertEqual(len(satisfied), 2)
        for cf in satisfied:
            self.assertIn("已提供证据", cf.basis)


class NonAttributableTests(unittest.TestCase):
    def test_qualitative_assumption_is_mostly_non_attributable(self):
        qual = _assumption(qualitative_only=True, confidence=0.3,
                           variable="addressable_market",
                           variable_label="可服务市场分层（高端/中端）")
        result = CausalCritic().review([qual])
        na = result.reviews[0].non_attributable
        self.assertTrue(na)
        entry = na[0]
        lo, hi = entry.portion_pct_range
        self.assertGreaterEqual(lo, 60.0)
        self.assertLessEqual(hi, 100.0)
        self.assertTrue(entry.reason)

    def test_approximate_assumption_gets_metric_non_attributable(self):
        approx = _assumption(target_comparability="approximate",
                             provenance_chain=["raw，未归一，按 approximate 处理"])
        result = CausalCritic().review([approx])
        na_rules = {n.rule_id for n in result.reviews[0].non_attributable}
        self.assertIn("NA-MET-001", na_rules)
        entry = next(n for n in result.reviews[0].non_attributable
                     if n.rule_id == "NA-MET-001")
        lo, hi = entry.portion_pct_range
        self.assertGreaterEqual(lo, 30.0)
        self.assertLessEqual(hi, 50.0)

    def test_industry_beta_non_attributable_only_when_rule_hit(self):
        result = CausalCritic().review([_assumption()])
        na_rules = {n.rule_id for n in result.reviews[0].non_attributable}
        self.assertIn("NA-IND-001", na_rules)

    def test_missing_industry_data_marks_non_attributable(self):
        bad = _assumption(provenance_chain=["行业数据缺失：catalog 中无条目 xxx"])
        result = CausalCritic().review([bad])
        na_rules = {n.rule_id for n in result.reviews[0].non_attributable}
        self.assertIn("NA-DATA-001", na_rules)


class ConfidenceAdjustmentTests(unittest.TestCase):
    def test_adjustment_is_explained_and_monotonic(self):
        result = CausalCritic().review([_assumption(confidence=0.8)])
        r = result.reviews[0]
        self.assertLess(r.adjusted_confidence, r.original_confidence)
        expected = round(0.8 - sum(a["delta"] * -1 for a in r.confidence_adjustments), 4)
        self.assertAlmostEqual(r.adjusted_confidence, max(0.1, expected), places=4)
        for adj in r.confidence_adjustments:
            self.assertTrue(adj["rule_id"].startswith("ALT-"))
            self.assertLess(adj["delta"], 0.0)
            self.assertTrue(adj["reason"])

    def test_adjustment_penalty_matches_rule_sum(self):
        critic = CausalCritic()
        result = critic.review([_assumption(confidence=0.8)])
        r = result.reviews[0]
        total_penalty = sum(a.confidence_penalty
                            for a in r.alternative_explanations)
        self.assertAlmostEqual(
            r.original_confidence - r.adjusted_confidence,
            min(total_penalty, r.original_confidence - 0.1), places=4)

    def test_confidence_floored_at_0_1(self):
        low = _assumption(confidence=0.2, target_comparability="approximate",
                          variable="unit_cost", variable_label="单位成本",
                          provenance_chain=["raw，未归一"])
        result = CausalCritic().review([low])
        self.assertGreaterEqual(result.reviews[0].adjusted_confidence, 0.1)


class DefensiveTests(unittest.TestCase):
    def test_dict_input_with_missing_fields(self):
        result = CausalCritic().review([{"variable": "sales_volume"}])
        self.assertEqual(len(result.reviews), 1)
        self.assertGreaterEqual(len(result.reviews[0].alternative_explanations), 1)

    def test_empty_and_garbage_inputs(self):
        critic = CausalCritic()
        for payload in ([], {"assumptions": []}, object()):
            result = critic.review(payload)
            self.assertIsNotNone(result)
        self.assertEqual(critic.review([]).reviews, [])
        self.assertEqual(critic.review({"assumptions": "不是列表"}).reviews, [])
        self.assertTrue(critic.review({"assumptions": "不是列表"}).warnings)

    def test_anonymous_assumption_goes_to_warnings(self):
        result = CausalCritic().review([{}])
        self.assertTrue(any("匿名假设" in w for w in result.warnings))

    def test_module_level_review_entry(self):
        result = review([_assumption()])
        self.assertEqual(len(result.reviews), 1)

    def test_to_dict_serializable(self):
        import json
        result = CausalCritic().review([_assumption()])
        json.dumps(result.to_dict(), ensure_ascii=False)


class EndToEndTests(unittest.TestCase):
    """真实数据端到端：parameter_table_filled.csv → engineering_analyzer
    → economic_mapper → causal_critic，跑通一条完整链。"""

    @classmethod
    def setUpClass(cls):
        params = load_and_normalize()
        cls.assumption_set = map_engineering_to_economics(
            params, aux_rows=load_aux_rows(), target_company="绿的谐波",
        )
        cls.result = CausalCritic().review(cls.assumption_set)

    def test_full_chain_produces_reviews(self):
        self.assertTrue(self.result.reviews)
        self.assertEqual(len(self.result.reviews),
                         len(self.assumption_set.assumptions))

    def test_quantitative_sales_assumption_is_critiqued(self):
        quant = [r for r in self.result.reviews
                 if r.variable == "sales_volume" and not r.qualitative_only]
        self.assertTrue(quant, "真实链上应至少有一条定量销量假设")
        review = quant[0]
        # 行业β/竞争/政策三类替代解释都被触发
        types = {a.alt_type for a in review.alternative_explanations}
        self.assertIn("industry", types)
        self.assertIn("competitive", types)
        # 反事实需求含 high 优先级
        priorities = {c.priority for c in review.counterfactual_requirements}
        self.assertIn("high", priorities)
        # 置信度被下调且可解释
        self.assertLess(review.adjusted_confidence, review.original_confidence)
        self.assertTrue(review.confidence_adjustments)
        # 行业β不可归因部分存在
        self.assertIn("NA-IND-001", {n.rule_id for n in review.non_attributable})

    def test_approximate_unit_cost_assumption_flagged(self):
        approx = [r for r in self.result.reviews
                  if r.variable == "unit_cost" and not r.qualitative_only
                  and r.original_confidence == 0.5]
        self.assertTrue(approx, "真实链上应存在 approximate 的定量成本假设")
        for r in approx:
            types = {a.alt_type for a in r.alternative_explanations}
            self.assertIn("metric", types)
            self.assertIn("NA-MET-001", {n.rule_id for n in r.non_attributable})

    def test_no_unexpected_errors_in_warnings(self):
        for w in self.result.warnings:
            self.assertNotIn("未预期错误", w)


if __name__ == "__main__":
    unittest.main()
