import unittest
from pathlib import Path

from src.engineering_analyzer import (
    DEFAULT_FACTORS,
    DEFAULT_PARAMETER_CSV,
    AssemblyScope,
    Comparability,
    ConversionFactors,
    OperatingPoint,
    back_calculate_motor_torque,
    convert_unit,
    filter_comparable,
    TORQUE_UNIT_TO_NM,
    infer_scope,
    load_and_normalize,
    normalize_parameter_row,
    normalize_torque,
    parse_numeric,
    torque_conversion_basis,
)


class TorqueConversionTests(unittest.TestCase):
    def test_peak_to_rated_uses_default_factor(self):
        # 峰值扭矩 130 N·m × 0.5 → 65 N·m（连续额定口径）
        self.assertEqual(normalize_torque(130.0, OperatingPoint.PEAK, OperatingPoint.RATED), 65.0)

    def test_rated_to_rated_is_identity(self):
        self.assertEqual(normalize_torque(51.0, OperatingPoint.RATED, OperatingPoint.RATED), 51.0)

    def test_custom_factor_is_respected(self):
        factors = ConversionFactors(peak_to_rated_torque=0.4)
        self.assertEqual(normalize_torque(100.0, OperatingPoint.PEAK, factors=factors), 40.0)

    def test_basis_is_auditable(self):
        basis = torque_conversion_basis()
        self.assertIn("0.5", basis)
        self.assertIn("state_verifier", basis)


class ScopeAndBackCalculationTests(unittest.TestCase):
    def test_infer_scope_motor_vs_gear_vs_module(self):
        self.assertEqual(infer_scope("FMK", "无框力矩电机"), AssemblyScope.MOTOR_BODY)
        self.assertEqual(infer_scope("LCS", "谐波减速器"), AssemblyScope.GEAR_UNIT)
        self.assertEqual(infer_scope("KAS", "旋转执行器"), AssemblyScope.JOINT_MODULE)

    def test_module_to_motor_back_calculation(self):
        # 模组输出 100 N·m，减速比 100，效率 0.8 → 电机 1.25 N·m
        motor, err = back_calculate_motor_torque(100.0, 100)
        self.assertIsNone(err)
        self.assertAlmostEqual(motor, 1.25)

    def test_back_calculation_requires_ratio(self):
        motor, err = back_calculate_motor_torque(100.0, None)
        self.assertIsNone(motor)
        self.assertIsNotNone(err)

    def test_row_with_ratio_marks_inferred_provenance(self):
        row = {"company": "甲", "product_series": "LHS", "model": "X-1",
               "rated_torque_nm": "100", "weight_kg": "2"}
        result = normalize_parameter_row(row, reduction_ratio=50)
        self.assertIn("motor_torque_nm", result.provenance)
        self.assertTrue(result.provenance["motor_torque_nm"].startswith("推算"))
        self.assertEqual(result.comparability, Comparability.APPROXIMATE)


class RowNormalizationTests(unittest.TestCase):
    def test_peak_only_row_is_converted_and_graded_approximate(self):
        row = {"company": "甲", "product_series": "LHT", "model": "LHT-32",
               "peak_torque_nm": "178", "weight_kg": "3.15"}
        result = normalize_parameter_row(row)
        self.assertEqual(result.torque_nm, 89.0)  # 178 × 0.5
        self.assertEqual(result.operating_point_raw, OperatingPoint.PEAK)
        self.assertAlmostEqual(result.torque_density_nm_kg, 28.25, places=4)
        self.assertTrue(result.provenance["torque_nm"].startswith("推算"))
        self.assertEqual(result.comparability, Comparability.APPROXIMATE)

    def test_rated_peak_equal_triggers_data_quality_warning(self):
        row = {"company": "甲", "product_series": "RV", "model": "RV-20E",
               "rated_torque_nm": "412", "peak_torque_nm": "412", "weight_kg": "8.5",
               "torque_density_nm_kg": "48.5"}
        result = normalize_parameter_row(row)
        self.assertTrue(any("疑似" in w for w in result.warnings))
        self.assertEqual(result.comparability, Comparability.APPROXIMATE)

    def test_missing_weight_and_density_is_not_comparable(self):
        row = {"company": "甲", "product_series": "FMK", "model": "M-1",
               "rated_torque_nm": "0.063"}
        result = normalize_parameter_row(row)
        self.assertEqual(result.torque_nm, 0.063)
        self.assertIsNone(result.torque_density_nm_kg)
        self.assertIn("weight_kg", result.missing_fields)
        self.assertEqual(result.comparability, Comparability.NOT_COMPARABLE)

    def test_fully_missing_torque_is_not_comparable(self):
        row = {"company": "甲", "product_series": "Y", "model": "Y-1",
               "weight_kg": "2.0"}
        result = normalize_parameter_row(row)
        self.assertIsNone(result.torque_nm)
        self.assertIn("torque_nm", result.missing_fields)
        self.assertEqual(result.comparability, Comparability.NOT_COMPARABLE)

    def test_non_numeric_and_invalid_inputs_are_defensive(self):
        self.assertIsNone(parse_numeric("待补充"))
        self.assertIsNone(parse_numeric(""))
        self.assertIsNone(parse_numeric(None))
        self.assertIsNone(parse_numeric(float("nan")))
        row = {"company": "甲", "product_series": "LHS", "model": "B-1",
               "rated_torque_nm": "not_a_number", "weight_kg": "-1"}
        result = normalize_parameter_row(row)
        self.assertIsNone(result.torque_nm)
        self.assertTrue(result.errors)  # 负重量 → 合法性错误，不抛异常

    def test_unit_conversion_recognizes_torque_units(self):
        value, err = convert_unit(100.0, "N·cm", TORQUE_UNIT_TO_NM)
        self.assertIsNone(err)
        self.assertAlmostEqual(value, 1.0)
        value, err = convert_unit(100.0, "帕斯卡", {"nm": 1.0})
        self.assertIsNone(value)
        self.assertIn("帕斯卡", err)


class CsvEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.params = load_and_normalize()
        cls.by_model = {p.model: p for p in cls.params}

    def test_csv_file_is_present(self):
        self.assertTrue(Path(DEFAULT_PARAMETER_CSV).exists())

    def test_lhs32_fully_comparable(self):
        p = self.by_model["LHS-32"]
        self.assertEqual(p.comparability, Comparability.COMPARABLE)
        self.assertEqual(p.torque_nm, 51.0)
        self.assertEqual(p.torque_density_nm_kg, 20.4)
        self.assertEqual(p.scope, AssemblyScope.GEAR_UNIT)
        self.assertEqual(p.provenance["torque_nm"], "实测：datasheet 额定扭矩（连续工况）")
        self.assertEqual(p.adjustments, [])

    def test_kinco_motor_row_is_not_comparable_due_to_missing_weight(self):
        p = self.by_model["FMK02509-0004-5511-7DP02"]
        self.assertEqual(p.scope, AssemblyScope.MOTOR_BODY)
        self.assertEqual(p.comparability, Comparability.NOT_COMPARABLE)
        self.assertIn("weight_kg", p.missing_fields)

    def test_nabtesco_official_spec_is_rated_not_start_stop_torque(self):
        """Official table restores explicit values; density stays derived."""
        p = self.by_model["RV-20E"]
        self.assertEqual(p.torque_nm, 167)
        self.assertEqual(p.torque_density_nm_kg, 35.53)  # four significant digits
        self.assertEqual(p.comparability, Comparability.APPROXIMATE)
        self.assertTrue(p.provenance['torque_density_nm_kg'].startswith('推算'))
        self.assertFalse(any('额定扭矩(167.0)≈峰值' in w for w in p.warnings))

    def test_shpr_speed_range_is_not_peak_torque(self):
        p = self.by_model['SHPR-20E']
        self.assertEqual(p.torque_nm, 167)
        self.assertEqual(p.torque_density_nm_kg, 35.53)
        self.assertIn('15r/min', p.notes)

    def test_rows_with_pending_fields_do_not_raise(self):
        p = self.by_model["Y系列（三次谐波）"]
        self.assertEqual(p.comparability, Comparability.NOT_COMPARABLE)
        self.assertIn("torque_nm", p.missing_fields)

    def test_filter_comparable_excludes_worst_rows(self):
        kept = filter_comparable(self.params)
        self.assertGreater(len(kept), 0)
        self.assertTrue(all(p.comparability != Comparability.NOT_COMPARABLE for p in kept))
        self.assertLessEqual(len(kept), len(self.params))

    def test_results_are_dict_serializable(self):
        for p in self.params:
            d = p.to_dict()
            self.assertEqual(d["model"], p.model)
            self.assertEqual(d["comparability"], p.comparability.value)


if __name__ == "__main__":
    unittest.main()
