from src.review_ui import assumption_rows, financial_comparison, scenario_rows, verdict_html
from src.financial_evidence import load_snapshot


def test_user_text_cannot_inject_html_in_verdict():
    output = verdict_html('<img src=x onerror=alert(1)>', '<script>bad()</script>')
    assert '<img' not in output and '<script>' not in output
    assert '&lt;img' in output and '&lt;script&gt;' in output


def test_year_comparison_preserves_zero_and_missing_as_distinct():
    rows = load_snapshot()['records'][:2]
    first = {**rows[0], 'report_period': '2024-12-31', 'value_cny': '0', 'value_status': 'observed'}
    second = {**first, 'report_period': '2025-12-31', 'value_cny': None, 'value_status': 'missing'}
    result = financial_comparison([first, second])
    assert result[0]['2024'] == '0.000'
    assert result[0]['2025'] == '—'


def test_scenario_display_converts_billions_to_hundred_millions():
    result = scenario_rows({'base': {'enterprise_value_bn': 4.2915, 'revenue_2027_bn': 1, 'fcf_2027_bn': 0}})
    assert result[0]['企业价值（亿元）'] == '42.92'
    assert result[0]['2027收入（亿元）'] == '10.00'
    assert result[0]['2027自由现金流（亿元）'] == '0.00'


def test_assumption_sign_uses_actual_delta_not_direction_label():
    result = assumption_rows({'assumption_set': {'assumptions': [{'variable': 'volume', 'direction': 'positive', 'delta_pct': -0.1038}]}})
    assert result[0]['模型中的改动'] == '-10.38%'
