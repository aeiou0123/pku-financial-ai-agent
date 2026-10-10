from copy import deepcopy
from datetime import date

import pytest

from src.harness.conditions import forward, reverse, sensitivity, confirm_parameter, market_cap_to_ev, vary
from src.harness.documents import parse
from src.harness.research import document_scope, retrieve, anchor_assessment


def model():
    return {'company': '公司甲', 'product': '减速器', 'cutoff': '2026-10-10', 'whole_company': False,
            'rows': [{'year': y, 'units': 60000., 'asp_yuan': 2000., 'unit_cost_yuan': 1200.,
                      'existing_capacity': 100000., 'incremental_capacity': 50000.,
                      'commissioning_date': '2027-07-01', 'confirmed_orders': None} for y in range(2027, 2032)],
            'opex_ratio': .15, 'depreciation_ratio': .03, 'tax_rate': .25, 'capex_ratio': .05,
            'nwc_ratio': .2, 'opening_nwc': 24000000., 'stub_fcff': 0., 'discount_rate': .1, 'terminal_growth': .02, 'bindings': []}


def candidate():
    docs = [parse('公司甲减速器设计产能100万台/年。'.encode(), 'capacity.txt')]
    scope = document_scope(docs, [{'name': 'capacity.txt', 'published_at': '2026-01-01', 'company': '公司甲',
                                   'product': '减速器', 'confirmed': True}], date(2026, 10, 10))
    pieces, _ = retrieve(docs, scope, ['产能'])
    assessment = anchor_assessment({'evidence': [{'piece_id': pieces[0]['piece_id'], 'quote': '产能100万台/年',
        'stance': 'supports', 'fact_type': 'forecast', 'explanation': '待确认'}], 'parameter_candidates':
        [{'evidence_index': 0, 'key': 'annual_capacity', 'value_text': '100', 'unit': '万台/年', 'period': ''}]},
        pieces, {'id': 'C1', 'label': '产能'})
    return assessment['parameter_candidates'][0], assessment['evidence'][0]


def test_forward_cash_flow_is_accounting_not_profit_causality():
    result = forward(model())
    row = result['years'][0]
    assert row['revenue'] == 120000000 and row['gross_margin'] == .4
    assert row['nopat'] == 19800000 and row['fcff'] == 17400000
    assert result['enterprise_value'] > 0 and len(result['gaps']) == 5


def test_capacity_prorates_by_commissioning_day_and_delay_creates_conflict():
    m = model()
    m['rows'][0]['units'] = 120000
    result = forward(m)
    assert result['years'][0]['available_capacity'] == pytest.approx(100000 + 50000 * 184 / 365)
    assert result['enterprise_value'] is not None
    delayed = forward(vary(m, 'commissioning_delay_days', 365))
    assert delayed['enterprise_value'] is None and '2027' in delayed['conflicts'][0]


def test_missing_capacity_is_explicit_gap_not_infinite_verified_capacity():
    m = model()
    m['rows'][0]['existing_capacity'] = None
    result = forward(m)
    assert result['years'][0]['available_capacity'] is None
    assert any('产能' in s for s in result['gaps']) and result['status'] == 'conditional_assumption_scenario'


def test_orders_are_a_demand_gap_not_volume_hard_cap():
    m = model()
    m['rows'][0]['confirmed_orders'] = 10000
    result = forward(m)
    assert result['years'][0]['uncovered_demand_units'] == 50000
    assert not result['conflicts']


def test_negative_terminal_cash_flow_withholds_perpetuity():
    m = model()
    m['capex_ratio'] = .8
    assert forward(m)['enterprise_value'] is None


def test_reverse_volume_and_price_and_margin_match_known_forward_values():
    for lever in ('volume_scale', 'price_scale', 'cost_scale'):
        target = forward(vary(model(), lever, 1.1))['enterprise_value']
        result = reverse(model(), target, lever=lever, lower=.8, upper=1.3)
        assert result['status'] == 'conditional_feasible_target'
        assert result['required_multiplier'] == pytest.approx(1.1)
        assert result['achieved'] == pytest.approx(target)
        assert result['years'][0]['gross_margin'] is not None


def test_reverse_cannot_promise_target_above_capacity():
    result = reverse(model(), 1e12, lower=.5, upper=5)
    assert result['status'] == 'target_outside_feasible_sampled_range' and 'required_multiplier' not in result


def test_parameter_confirmation_checks_scope_units_and_binding_changes():
    p, e = candidate()
    with pytest.raises(ValueError, match='范围'):
        confirm_parameter(p, e, '公司乙', '减速器', True)
    confirmed = confirm_parameter(p, e, '公司甲', '减速器', True)
    assert confirmed['normalized_value'] == 1000000
    m = model()
    m['bindings'] = [{**confirmed, 'application': {'field': 'existing_capacity', 'years': [2027]}}]
    with pytest.raises(ValueError, match='模型值已改变'):
        forward(m)
    m['rows'][0]['existing_capacity'] = 1000000
    assert forward(m)['enterprise_value'] is not None
    e2 = deepcopy(e); p2 = deepcopy(p)
    e2['quote'] = p2['quote'] = '产能100台/年'
    with pytest.raises(ValueError, match='万台'):
        confirm_parameter(p2, e2, '公司甲', '减速器', True)


def test_ambiguous_dates_and_orders_period_not_guessed():
    p, e = candidate()
    p.update(key='commissioning_date', unit='日期', value_text='2027年')
    p['quote'] = e['quote'] = '2027年计划投产'
    with pytest.raises(ValueError, match='年月日'):
        confirm_parameter(p, e, '公司甲', '减速器', True)


def test_sensitivity_declares_ranges_and_withholds_conflicted_endpoints():
    m = model()
    m['rows'][0]['units'] = 120000
    rows = sensitivity(m, [{'key': 'commissioning_delay_days', 'low': 0, 'high': 365}, {'key': 'price_scale', 'low': .9, 'high': 1.1}])
    assert rows[0]['ev_span'] > 0
    assert rows[1]['ev_span'] is None and rows[1]['conflicts']
    assert all('not_probability' in r['basis'] for r in rows)


def test_product_value_cannot_compare_full_company_market_cap_or_mixed_dates():
    with pytest.raises(ValueError, match='全公司'):
        market_cap_to_ev(model(), 100, -20, 5, 10, ['2026-10-10'] * 4)
    m = model(); m['whole_company'] = True
    assert market_cap_to_ev(m, 100, -20, 5, 10, ['2026-10-10'] * 4)['target_ev'] == 75
    with pytest.raises(ValueError, match='同一日期'):
        market_cap_to_ev(m, 100, -20, 5, 10, ['2026-10-01'] * 3 + ['2026-09-30'])


def test_calendar_cashflow_discounting_and_remaining_year_cashflow_are_explicit():
    m = model(); m['stub_fcff'] = 1000000
    result = forward(m)
    years = result['years']
    expected = 1000000 / 1.1 ** ((date(2026, 12, 31) - date(2026, 10, 10)).days / 365.2425)
    expected += sum(r['fcff'] / 1.1 ** ((date(r['year'], 12, 31) - date(2026, 10, 10)).days / 365.2425) for r in years)
    expected += years[-1]['fcff'] * 1.02 / .08 / 1.1 ** ((date(2031, 12, 31) - date(2026, 10, 10)).days / 365.2425)
    assert result['enterprise_value'] == pytest.approx(expected)
    assert years[0]['discount_years'] > 1 and result['valuation_date'] == m['cutoff']


def test_past_forecast_year_not_relabelled_as_future():
    m = model(); m['rows'][0]['year'] = 2025
    with pytest.raises(ValueError, match='预测年度'):
        forward(m)


def test_reverse_samples_actual_capacity_boundary_instead_of_missing_nearby_target():
    m = model()
    target = forward(vary(m, 'volume_scale', 2.05))['enterprise_value']
    assert target is not None
    result = reverse(m, target, lower=.5, upper=5)
    assert result['required_multiplier'] == pytest.approx(2.05)


def test_bound_historical_orders_cannot_masquerade_as_future_confirmed_orders():
    p, e = candidate()
    p.update(key='orders_units', unit='台', value_text='100', period='2025')
    p['quote'] = e['quote'] = '2025年订单100台'
    confirmed = confirm_parameter(p, e, '公司甲', '减速器', True)
    m = model(); m['rows'][0]['confirmed_orders'] = 100
    m['bindings'] = [{**confirmed, 'application': {'field': 'confirmed_orders', 'years': [2027]}}]
    with pytest.raises(ValueError, match='订单期间'):
        forward(m)
