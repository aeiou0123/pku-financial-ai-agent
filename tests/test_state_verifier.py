import unittest

from src.state_verifier import StateVerifier


class StateVerifierRegressionTests(unittest.TestCase):
    def setUp(self):
        self.verifier = StateVerifier()

    def test_missing_qualifier_is_partial_support(self):
        result = self.verifier.verify(
            "绿的谐波新一代谐波减速器关节模组减重30%以上",
            "国信证券研报：聚焦谐波减速器的轻量小型化技术突破，同等出力情况下减重30%以上",
        )
        self.assertEqual(result.verdict_override, "partially_supported")
        self.assertIn("同等出力情况下", result.missing_qualifiers)

    def test_definition_swap_is_detected(self):
        result = self.verifier.verify(
            "绿的谐波LHS-32谐波减速器峰值扭矩51 Nm，重量2.5 kg",
            "研报原文：LHS-32 谐波减速器：额定扭矩 51 Nm，峰值扭矩 130 Nm，重量 2.5 kg",
        )
        self.assertTrue(result.has_definition_mismatch)
        self.assertEqual(result.verdict_override, "definition_mismatch")

    def test_value_tampering_is_detected(self):
        result = self.verifier.verify(
            "绿的谐波2024年谐波减速器销量8.41万台，同比增长16.56%",
            "国信证券研报：2024年谐波减速器及金属部件收入3.25亿元，谐波减速器销量24.65万台，同比增长16.56%",
        )
        self.assertEqual(result.verdict_override, "refuted")
        self.assertTrue(result.value_contradictions)

    def test_source_downgrade_is_low_confidence(self):
        result = self.verifier.verify(
            "绿的谐波新一代谐波减速器关节模组在同等出力情况下减重30%以上",
            "网传消息：聚焦谐波减速器的轻量小型化技术突破，同等出力情况下减重30%以上",
        )
        self.assertTrue(result.has_source_downgrade)
        self.assertEqual(result.verdict_override, "low_confidence")

    def test_empty_evidence_is_not_invented(self):
        result = self.verifier.verify("任意 Claim", "")
        self.assertIsNone(result.verdict_override)
        self.assertIn("无证据，规则层跳过", result.flags)


if __name__ == "__main__":
    unittest.main()
