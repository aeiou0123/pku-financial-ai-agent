import unittest
from pathlib import Path

from src.financial_model import (
    DEFAULT_INPUT_PATH,
    FinancialModelInputs,
    run_all_scenarios,
    run_model,
)


class FinancialModelTests(unittest.TestCase):
    def setUp(self):
        self.inputs = FinancialModelInputs.from_csv(DEFAULT_INPUT_PATH)

    def test_input_types_are_separated(self):
        types = {row.input_type for row in self.inputs.rows}
        self.assertEqual(types, {"historical", "assumption"})
        result = run_model(self.inputs)
        self.assertEqual(result["traceability"]["input_types"]["historical"], 2)
        self.assertFalse(result["traceability"]["historical_inputs_used_for_forecast"])

    def test_revenue_and_dcf_are_reproducible(self):
        result_a = run_model(self.inputs, "base")
        result_b = run_model(self.inputs, "base")
        self.assertEqual(result_a, result_b)
        year_2025 = result_a["projections"][0]
        expected_revenue = (130 * 1150 + 20 * 2400) / 100_000
        self.assertAlmostEqual(year_2025["revenue_bn"], expected_revenue)
        self.assertGreater(result_a["valuation"]["enterprise_value_bn"], 0)

    def test_scenarios_have_distinct_outputs(self):
        results = run_all_scenarios(self.inputs)
        values = {
            name: result["valuation"]["enterprise_value_bn"]
            for name, result in results.items()
        }
        self.assertGreater(values["upside"], values["base"])
        self.assertLess(values["downside"], values["base"])


if __name__ == "__main__":
    unittest.main()
