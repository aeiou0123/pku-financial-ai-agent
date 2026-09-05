import unittest

from app import run_local_demo


class LocalDemoTests(unittest.TestCase):
    def test_demo_is_local_and_conservative(self):
        result = run_local_demo()
        self.assertEqual(result["demo_status"], "local_reproducible_prototype")
        self.assertEqual(result["verification"]["verdict"], "partially_supported")
        self.assertEqual(result["verification"]["verdict_source"], "state_verifier_rule")
        self.assertIn("base", result["financial_impact"])
        self.assertIn("enterprise_value_bn", result["financial_impact"]["base"])


if __name__ == "__main__":
    unittest.main()
