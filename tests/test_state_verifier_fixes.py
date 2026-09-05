"""StateVerifier 误报修复回归测试
====================================

覆盖 2026-09-05 修复的 6 条规则层误伤（hit→miss），
每条对应 benchmark 中的真实用例。修复详情见 pipeline_report.md。

误报根因分类：
1. 列举式证据数值错位（GH_006 系列）——「A、B、C 分别增长 x%、y%、z%」句式
2. 口径词对误报（GH_007/SH_002_VALU）——claim 含对立词对之一即口径明确
3. 限定词抢优先级（GH_004_SRCD）——来源降级应优先于限定词缺失
4. 数值窗口截断（GH_006）——「47.31」被切成「47」导致数值归属误判
5. 跨指标数值交叉匹配（SH_002_VALU）——±10% 容差放走真矛盾
6. 约数表述误判（SH_005_QUAL）——「超过100%」vs 精确值 101.30% 是粒度差异
"""

import unittest

from src.state_verifier import StateVerifier


class StateVerifierFixRegressionTests(unittest.TestCase):
    """误报修复回归：修复前这些场景会覆盖 LLM 的正确判断"""

    def setUp(self):
        self.verifier = StateVerifier()

    # ── 根因 1+4：列举式证据 + 窗口截断（GH_006_VALU/SRCD/TEMP）──

    def test_enumerated_evidence_no_false_definition_mismatch(self):
        """GH_006：列举式证据（A、B、C 分别增长 x%、y%、z%）不应误判口径偷换。

        修复前：claim「营业收入增长47.31%」被误判与 source「净利润」口径偷换，
        因为 30 字符窗口把 source 中「营业收入」附近的 47.31 截断成 47。
        """
        result = self.verifier.verify(
            "绿的谐波2025年营业收入同比增长47.31%，归母净利润同比增长121.42%",
            "2025年年报：本报告期营业收入、利润总额、归属于上市公司股东的净利润"
            "较上年同期分别增长47.31%、137.48%、121.42%",
        )
        self.assertFalse(
            result.has_definition_mismatch,
            "列举式证据不应误判口径偷换（修复前误报：营业收入/净利润）",
        )

    def test_enumerated_evidence_value_tampering_still_detected(self):
        """GH_006_VALU：列举式证据下，真正的数值篡改仍要检出。"""
        result = self.verifier.verify(
            "绿的谐波2025年营业收入同比增长47.31%，归母净利润同比增长226.64%",
            "2025年年报：本报告期营业收入、利润总额、归属于上市公司股东的净利润"
            "较上年同期分别增长47.31%、137.48%、121.42%",
        )
        self.assertEqual(result.verdict_override, "refuted")
        self.assertTrue(result.value_contradictions)

    def test_enumerated_evidence_temporal_shift_still_detected(self):
        """GH_006_TEMP：列举式证据下，时间错位仍要检出（优先于限定词）。"""
        result = self.verifier.verify(
            "绿的谐波2026年营业收入同比增长47.31%，归母净利润同比增长121.42%",
            "2025年年报：本报告期营业收入、利润总额、归属于上市公司股东的净利润"
            "较上年同期分别增长47.31%、137.48%、121.42%",
        )
        self.assertEqual(result.verdict_override, "refuted")

    def test_enumerated_evidence_source_downgrade_takes_priority(self):
        """GH_006_SRCD：来源降级应给 low_confidence，而非被误报的口径偷换覆盖。"""
        result = self.verifier.verify(
            "绿的谐波2025年营业收入同比增长47.31%，归母净利润同比增长121.42%",
            "2025年市场传闻：本报告期营业收入、利润总额、归属于上市公司股东的净利润"
            "较上年同期分别增长47.31%、137.48%、121.42%",
        )
        self.assertEqual(result.verdict_override, "low_confidence")

    # ── 根因 2：口径词对豁免（GH_007_VALU / SH_002_VALU）──

    def test_counterpart_qualifier_not_required(self):
        """GH_007/SH_002_VALU：claim 已含「额定扭矩」时，
        不应再要求 claim 包含「峰值扭矩」——口径对含其一即明确。"""
        result = self.verifier.verify(
            "绿的谐波LHS-32谐波减速器额定扭矩51-130 Nm，重量2.5 kg",
            "【研报原文摘录】LHS-32 谐波减速器：额定扭矩 51 Nm，"
            "峰值扭矩 130 Nm，重量 2.5 kg，扭矩密度 20.4 Nm/kg",
        )
        self.assertNotIn("峰值扭矩", result.missing_qualifiers)
        self.assertEqual(result.verdict_override, None)

    def test_both_qualifiers_absent_still_reported(self):
        """GH_007_QUAL（回归保护）：claim 中额定/峰值都没有时，
        仍应报限定词缺失（扭矩口径不明）。"""
        result = self.verifier.verify(
            "绿的谐波LHS-32谐波减速器扭矩51-130 Nm，重量2.5 kg",
            "【研报原文摘录】LHS-32 谐波减速器：额定扭矩 51 Nm，"
            "峰值扭矩 130 Nm，重量 2.5 kg，扭矩密度 20.4 Nm/kg",
        )
        self.assertTrue(
            any(q in ("额定扭矩", "峰值扭矩") for q in result.missing_qualifiers),
            "口径词全缺时应报限定词缺失",
        )
        self.assertEqual(result.verdict_override, "partially_supported")

    # ── 根因 3：限定词不抢来源降级的优先级（GH_004_SRCD）──

    def test_source_downgrade_beats_qualifier_flags(self):
        """GH_004_SRCD：source 含背景描述词（国内/关节模组等）而 claim 无，
        且来源是市场传闻 → 应判 low_confidence 而非 partially_supported。"""
        result = self.verifier.verify(
            "绿的谐波已成为多家头部具身智能机器人企业的核心供应商",
            "2024年市场传闻：自主研发的高扭矩密度谐波减速器和一体化关节模组，"
            "已在国内具身智能机器人产业链占据领先地位，"
            "成为多家头部具身智能机器人企业的核心供应商",
        )
        self.assertEqual(result.verdict_override, "low_confidence")
        self.assertTrue(result.has_source_downgrade)

    # ── 根因 5：跨指标数值交叉匹配（SH_002_VALU）──

    def test_cross_metric_no_tolerance(self):
        """SH_002_VALU：claim 的 172（额定扭矩）与 source 中竞对的
        扭矩密度 164.8 数值相近但指标不同——精确匹配下应报矛盾。"""
        result = self.verifier.verify(
            "双环传动SHPR-20E RV减速器额定扭矩172-231 Nm，重量4.7 kg",
            "国金证券研报：RV减速器国内外主要品牌同型号参数对比表\n"
            "【研报原文摘录】SHPR-20E RV 减速器：额定扭矩 110 Nm，"
            "峰值扭矩 231 Nm，重量 4.7 kg，扭矩密度 23.4 Nm/kg。"
            "（对比：纳博特斯克 RV-20E 额定扭矩 412 Nm，重量 2.5 kg，"
            "扭矩密度 164.8 Nm/kg）",
        )
        self.assertEqual(result.verdict_override, "refuted")
        self.assertTrue(any(c["claim_value"] == "172" for c in result.value_contradictions))

    # ── 根因 6：约数表述（SH_005_QUAL）──

    def test_approximate_value_gets_tolerance(self):
        """SH_005_QUAL：「产能利用率超过100%」是约数表述，
        source 精确值 101.30% 应容差匹配，不报数值矛盾。"""
        result = self.verifier.verify(
            "环动科技产品销量持续增长，2023年度产能利用率超过100%",
            "环动科技招股书：报告期各期，公司RV减速器产品的产能利用率"
            "分别为80.61%、87.02%、101.30%和83.08%",
        )
        self.assertFalse(
            any(c["claim_value"] == "100" for c in result.value_contradictions),
            "约数（超过100%）与精确值（101.30%）是粒度差异，不是矛盾",
        )

    def test_approximate_value_tampering_still_detected(self):
        """SH_005_VALU（回归保护）：约数被篡改到容差外仍要检出。"""
        result = self.verifier.verify(
            "环动科技RV减速器产品销量持续增长，2023年度产能利用率超过54%",
            "环动科技招股书：报告期各期，公司RV减速器产品的产能利用率"
            "分别为80.61%、87.02%、101.30%和83.08%",
        )
        self.assertEqual(result.verdict_override, "refuted")

    # ── 窗口截断保护单元测试 ──

    def test_extract_value_not_truncated_by_window(self):
        """数值提取不应返回被窗口截断的半个数值。"""
        source = (
            "2025年年报：本报告期营业收入、利润总额、归属于上市公司股东的净利润"
            "较上年同期分别增长47.31%、137.48%、121.42%"
        )
        val = self.verifier._extract_value_near_term(source, "营业收入")
        self.assertNotEqual(val, "47", "「47.31」被 30 字符窗口切成「47」时应返回 None")
        self.assertNotEqual(val, "47.3", "截断的半数值不可作为匹配依据")


if __name__ == "__main__":
    unittest.main()
