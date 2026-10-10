"""Explicit product cash-flow assumptions, evidence bindings and feasible reverse targets."""
from __future__ import annotations

from .module_stamp import source_stamp
_c2v_loaded_source_hash = source_stamp(__file__)

from copy import deepcopy
from datetime import date, timedelta
import math
import re
import json
import pandas as pd

from .documents import digest
from .exports import workbook


def number(value, name, low=0, high=float('inf')):
    if isinstance(value, bool):
        raise ValueError(name + '不能为布尔值。')
    try:
        result = float(value)
    except (ValueError, TypeError):
        raise ValueError(name + '须为数字。') from None
    if not math.isfinite(result) or not low <= result <= high:
        raise ValueError(name + '超出有效范围。')
    return result


def confirm_parameter(candidate, evidence, company, product, confirmed):
    """Promote only an exact anchored, same-scope candidate; date/unit parsing never guesses."""
    if not confirmed:
        raise ValueError('参数须对照原件明确确认。')
    if candidate.get('fact_type') == 'opinion':
        raise ValueError('意见不能确认为数值参数。')
    if (candidate.get('evidence_id') != evidence.get('id') or candidate.get('quote') != evidence.get('quote')
            or candidate.get('source_sha256') != evidence.get('source_sha256')
            or candidate.get('value_text', '') not in evidence.get('quote', '')):
        raise ValueError('参数与引用记录不一致。')
    meta = evidence['metadata']
    if meta.get('company') != company or not product or meta.get('product') != product:
        raise ValueError('公司与产品范围须准确一致；不能把同行或全公司参数绑定到本产品。')
    key, unit, text = candidate['key'], candidate['unit'], candidate['value_text'].strip()
    if key == 'commissioning_date':
        if unit != '日期':
            raise ValueError('投产日单位须为日期。')
        match = re.fullmatch(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
        if match:
            value = date(*map(int, match.groups())).isoformat()
        elif re.fullmatch(r'\d{4}-\d{2}-\d{2}', text):
            value = date.fromisoformat(text).isoformat()
        else:
            raise ValueError('须有明确年月日；只披露年份或季度不能猜投产日期。')
    else:
        allowed = {'annual_capacity': {'台/年', '万台/年'}, 'orders_units': {'台', '万台'},
                   'asp_yuan': {'元/台'}, 'unit_cost_yuan': {'元/台'}}
        if unit not in allowed.get(key, set()) or not re.fullmatch(r'\d+(?:\.\d+)?', text):
            raise ValueError('参数数值须为单个明确非负数字，单位须与字段相符；区间、约数或单位混入数值均待核。')
        if not re.search(r'(?<![\d.])' + re.escape(text) + r'\s*' + re.escape(unit), evidence['quote']):
            raise ValueError('数值与单位须在原文中明确相连，不能把台误当万台。')
        value = number(text, key) * (10000 if unit.startswith('万') else 1)
    return {**deepcopy(candidate), 'normalized_value': value, 'company': company, 'product': product,
            'status': 'operator_confirmed_quote_and_parameter_not_independent_authentication',
            'forecast_use': 'user_assumption_even_if_historical_source', 'confirmation': True}


def validate_model(model):
    required = {'company', 'product', 'cutoff', 'rows', 'opex_ratio', 'depreciation_ratio', 'tax_rate',
                'capex_ratio', 'nwc_ratio', 'opening_nwc', 'discount_rate', 'terminal_growth', 'whole_company', 'stub_fcff'}
    if not isinstance(model, dict) or set(model) - required - {'bindings', 'scenario_overrides'} or required - set(model):
        raise ValueError('兑现条件模型字段不完整或不支持。')
    if not model['company'].strip() or not model['product'].strip():
        raise ValueError('须明确公司及建模业务范围。')
    cutoff = date.fromisoformat(model['cutoff'])
    rows = model['rows']
    if not isinstance(rows, list) or len(rows) != 5:
        raise ValueError('须输入连续五个完整预测年度。')
    if any(not isinstance(r, dict) or type(r.get('year')) is not int for r in rows):
        raise ValueError('预测年度须为整数，行须为字段对象。')
    if [r.get('year') for r in rows] != list(range(cutoff.year + 1, cutoff.year + 6)):
        raise ValueError('预测年度须从截止日下一年开始，不将已发生年度当预测。')
    fields = {'year', 'units', 'asp_yuan', 'unit_cost_yuan', 'existing_capacity', 'incremental_capacity',
              'commissioning_date', 'confirmed_orders'}
    clean = deepcopy(model)
    for row in clean['rows']:
        if set(row) != fields:
            raise ValueError('预测表列名不完整。')
        for key in ('units', 'asp_yuan', 'unit_cost_yuan'):
            row[key] = number(row[key], key)
        for key in ('existing_capacity', 'incremental_capacity', 'confirmed_orders'):
            row[key] = None if row[key] in ('', None) else number(row[key], key)
        if row['commissioning_date']:
            row['commissioning_date'] = date.fromisoformat(row['commissioning_date']).isoformat()
    for key in ('opex_ratio', 'depreciation_ratio', 'tax_rate', 'capex_ratio', 'nwc_ratio'):
        clean[key] = number(clean[key], key, 0, 1)
    clean['opening_nwc'] = number(clean['opening_nwc'], '期初营运资本')
    clean['stub_fcff'] = number(clean['stub_fcff'], '截止日至本年末FCFF', -float('inf'))
    clean['discount_rate'] = number(clean['discount_rate'], '折现率', .001, .99)
    clean['terminal_growth'] = number(clean['terminal_growth'], '永续增长', -.2, .5)
    if clean['terminal_growth'] >= clean['discount_rate']:
        raise ValueError('永续增长率必须低于折现率。')
    if type(clean['whole_company']) is not bool:
        raise ValueError('须声明是否覆盖全部公司业务。')
    for binding in clean.get('bindings', []):
        if (binding.get('status') != 'operator_confirmed_quote_and_parameter_not_independent_authentication'
                or binding.get('company') != clean['company'] or binding.get('product') != clean['product']):
            raise ValueError('绑定证据未经确认或公司／业务不符。')
        if date.fromisoformat(binding['metadata']['published_at']) > cutoff:
            raise ValueError('绑定证据晚于信息截止日。')
        application = binding.get('application', {})
        fields = {'annual_capacity': {'existing_capacity', 'incremental_capacity'}, 'commissioning_date': {'commissioning_date'},
                  'asp_yuan': {'asp_yuan'}, 'unit_cost_yuan': {'unit_cost_yuan'}, 'orders_units': {'confirmed_orders'}}
        if application.get('field') not in fields.get(binding.get('key'), set()) or not application.get('years'):
            raise ValueError('证据绑定须明确预测年度和目标字段。')
        for year in application['years']:
            row = next((r for r in clean['rows'] if r['year'] == year), None)
            if row is None or row[application['field']] != binding['normalized_value']:
                raise ValueError('模型值已改变，与绑定引用不一致；移除绑定或重新核对。')
            if binding['key'] == 'orders_units' and binding.get('period') not in (str(year), str(year) + '-12-31'):
                raise ValueError('订单期间须明确匹配该预测年，历史订单不能冒充未来已确认订单。')
    return clean


def capacity_for(row):
    existing, incremental = row['existing_capacity'], row['incremental_capacity']
    if existing is None or incremental is None or (incremental > 0 and not row['commissioning_date']):
        return None
    start, end = date(row['year'], 1, 1), date(row['year'] + 1, 1, 1)
    commissioning = date.fromisoformat(row['commissioning_date']) if incremental > 0 else end
    days = max(0, (end - max(start, commissioning)).days)
    result = existing + incremental * days / (end - start).days
    if not math.isfinite(result):
        raise ValueError('产能折算溢出，请核对数量级。')
    return result


def forward(model):
    m = validate_model(model)
    valuation_date = date.fromisoformat(m['cutoff'])
    rows, conflicts, gaps = [], [], []
    previous_nwc = m['opening_nwc']
    for source in m['rows']:
        row = dict(source)
        capacity = capacity_for(row)
        row['available_capacity'] = capacity
        if capacity is None:
            gaps.append(f"{row['year']}年可售产能或明确投产日期缺失。")
        elif row['units'] > capacity + 1e-7:
            conflicts.append(f"{row['year']}年销量{row['units']:,.2f}超过按投产日折算产能{capacity:,.2f}。")
        if row['confirmed_orders'] is None:
            gaps.append(f"{row['year']}年订单未绑定证据；不能由客户名单推断。")
        row['uncovered_demand_units'] = None if row['confirmed_orders'] is None else max(0, row['units'] - row['confirmed_orders'])
        revenue, costs = row['units'] * row['asp_yuan'], row['units'] * row['unit_cost_yuan']
        gross = revenue - costs
        ebit = gross - revenue * (m['opex_ratio'] + m['depreciation_ratio'])
        # No assumed immediate tax credit on losses.
        nopat = ebit - max(0, ebit) * m['tax_rate']
        nwc = revenue * m['nwc_ratio']
        fcff = nopat + revenue * m['depreciation_ratio'] - revenue * m['capex_ratio'] - (nwc - previous_nwc)
        previous_nwc = nwc
        row.update(revenue=revenue, cogs=costs, gross_profit=gross, gross_margin=None if revenue == 0 else gross / revenue,
                   ebit=ebit, nopat=nopat, fcff=fcff, nwc=nwc,
                   discount_years=(date(row['year'], 12, 31) - valuation_date).days / 365.2425)
        rows.append(row)
    if rows[-1]['fcff'] <= 0:
        conflicts.append('第五年FCFF非正，本版永续现金流估值不适用。')
    terminal = rows[-1]['fcff'] * (1 + m['terminal_growth']) / (m['discount_rate'] - m['terminal_growth'])
    stub_years = (date(valuation_date.year, 12, 31) - valuation_date).days / 365.2425
    ev = (m['stub_fcff'] / (1 + m['discount_rate']) ** stub_years +
          sum(r['fcff'] / (1 + m['discount_rate']) ** r['discount_years'] for r in rows) +
          terminal / (1 + m['discount_rate']) ** rows[-1]['discount_years'])
    if not math.isfinite(ev) or any(not math.isfinite(r[k]) for r in rows for k in ('revenue', 'fcff', 'nopat')):
        raise ValueError('计算溢出，请核对输入数量级。')
    return {'model': m, 'years': rows, 'conflicts': conflicts, 'gaps': gaps,
            'enterprise_value': None if conflicts else ev,
            'valuation_date': m['cutoff'], 'cash_flow_timing': 'calendar_year_end; actual_days_div_365.2425; explicit_current_year_stub',
            'status': 'constraint_conflict_valuation_withheld' if conflicts else 'conditional_assumption_scenario',
            'scope': 'whole_company_operator_declared' if m['whole_company'] else 'specified_business_only',
            'limitations': ['全部未来销量、价格、成本与财务参数均是条件假设；证据绑定不证明因果效应。',
                            '设计产能为上限假设，投产后按日折算；未模拟爬坡、良率、停工或产能利用率。',
                            '订单缺口不是需求不存在；已确认订单不是未来销量上限。',
                            '利润目标采用经营NOPAT，未计算归母净利润；亏损不假设立即取得税收抵免。',
                            '缺产能证据时仅生成条件情景，不代表已满足约束。']}


def market_cap_to_ev(model, market_cap, net_debt, minority, nonoperating_assets, dates):
    m = validate_model(model)
    if not m['whole_company']:
        raise ValueError('仅覆盖一个产品或业务时，不能与全公司市值比较。')
    if len(dates) != 4 or len(set(dates)) != 1 or not all(dates) or date.fromisoformat(dates[0]).isoformat() != m['cutoff']:
        raise ValueError('市值、净债务、少数股东价值及非经营资产须同一日期，且与本次估值信息截止日一致。')
    value = (number(market_cap, '市值') + number(net_debt, '净债务', -float('inf'))
             + number(minority, '少数股东价值') - number(nonoperating_assets, '非经营资产'))
    return {'target_ev': number(value, '目标企业价值'), 'date': dates[0],
            'formula': 'equity_market_cap + net_debt + minority_value - nonoperating_assets', 'operator_assumptions': True}


def vary(model, key, value):
    m = deepcopy(model)
    if key not in {'volume_scale', 'price_scale', 'cost_scale', 'commissioning_delay_days'}:
        raise ValueError('不支持的情景参数。')
    value = number(value, key, 0, 3650 if key == 'commissioning_delay_days' else 50)
    if key == 'commissioning_delay_days' and value != int(value):
        raise ValueError('延期天数须为整数。')
    for row in m['rows']:
        if key == 'commissioning_delay_days':
            if row['incremental_capacity'] not in (None, '', 0) and not row['commissioning_date']:
                raise ValueError('缺明确投产日，不能计算延期情景。')
            if row['commissioning_date']:
                row['commissioning_date'] = (date.fromisoformat(row['commissioning_date']) + timedelta(days=int(value))).isoformat()
        else:
            field = {'volume_scale': 'units', 'price_scale': 'asp_yuan', 'cost_scale': 'unit_cost_yuan'}[key]
            row[field] *= value
    affected = {'volume_scale': 'units', 'price_scale': 'asp_yuan', 'cost_scale': 'unit_cost_yuan', 'commissioning_delay_days': 'commissioning_date'}[key]
    overridden = [b for b in m.get('bindings', []) if b['application']['field'] == affected]
    m['bindings'] = [b for b in m.get('bindings', []) if b['application']['field'] != affected]
    m['scenario_overrides'] = m.get('scenario_overrides', []) + [{'key': key, 'value': value, 'original_bindings': overridden,
                                                              'status': 'explicit_assumption_override_not_source_update'}]
    return m


def reverse(model, target, metric='enterprise_value', lever='volume_scale', lower=.05, upper=5):
    """Bounded monotonic root search; never return a conflicted valuation as achievable."""
    model = validate_model(model)
    if metric not in {'enterprise_value', 'nopat'} or lever not in {'volume_scale', 'price_scale', 'cost_scale'}:
        raise ValueError('仅反推企业价值／第五年经营NOPAT与销量／售价／单位成本倍数。')
    target, lower, upper = number(target, '目标'), number(lower, '下界', .001, 50), number(upper, '上界', .001, 50)
    if lower >= upper:
        raise ValueError('反推下界须低于上界。')
    declared_range = [lower, upper]
    if lever == 'volume_scale':
        capacity_bounds = [capacity_for(r) / r['units'] for r in model['rows'] if r['units'] > 0 and capacity_for(r) is not None]
        if capacity_bounds:
            upper = min(upper, min(capacity_bounds))
        if upper <= lower:
            return {'status': 'no_feasible_search_interval', 'target': target, 'metric': metric, 'lever': lever,
                    'range': declared_range, 'message': '声明下界已超出按投产日折算的产能约束。'}
    def evaluate(x):
        result = forward(vary(model, lever, x))
        return result, result['enterprise_value'] if metric == 'enterprise_value' else result['years'][-1]['nopat']
    # Nonpositive terminal FCFF/capacity conflicts create invalid points, not valid objective values.
    grid = [(lower + (upper - lower) * i / 40) for i in range(41)]
    valid = [(x, *evaluate(x)) for x in grid]
    valid = [(x, r, v) for x, r, v in valid if v is not None and not r['conflicts']]
    if len(valid) < 2:
        return {'status': 'no_feasible_search_interval', 'target': target, 'metric': metric, 'lever': lever,
                'range': declared_range, 'feasible_search_range': [lower, upper], 'message': '范围内没有足够无冲突情景，补证据或调整范围。'}
    increasing = lever != 'cost_scale'
    if any((b[2] - a[2]) * (1 if increasing else -1) < -1e-6 for a, b in zip(valid, valid[1:])):
        raise ValueError('声明范围内目标不单调，本版不作单根反推。')
    bracket = next(((a[0], b[0]) for a, b in zip(valid, valid[1:]) if min(a[2], b[2]) <= target <= max(a[2], b[2])), None)
    if bracket is None:
        return {'status': 'target_outside_feasible_sampled_range', 'target': target, 'metric': metric, 'lever': lever,
                'range': declared_range, 'feasible_search_range': [lower, upper], 'feasible_values_sampled': [min(v[2] for v in valid), max(v[2] for v in valid)],
                'message': '目标超出声明范围内无冲突样本，不将受产能约束的目标说成可兑现。'}
    lo, hi = bracket
    for _ in range(70):
        mid = (lo + hi) / 2
        result, value = evaluate(mid)
        if value is None or result['conflicts']:
            raise ValueError('反推区间出现约束冲突，未生成兑现结论。')
        if (value < target) == increasing:
            lo = mid
        else:
            hi = mid
    result, value = evaluate((lo + hi) / 2)
    return {'status': 'conditional_feasible_target', 'target': target, 'achieved': value, 'metric': metric, 'lever': lever,
            'required_multiplier': (lo + hi) / 2, 'years': result['years'], 'gaps': result['gaps'],
            'method': '41_point_monotonicity_check_then_70_bisections_with_capacity_checks',
            'note': '反推是模型条件，不证明销量、价格或利润会实现；未校准概率。'}


def sensitivity(model, ranges):
    if not isinstance(ranges, list) or not 1 <= len(ranges) <= 4 or len({r['key'] for r in ranges}) != len(ranges):
        raise ValueError('须预先声明1—4个不同参数范围。')
    rows = []
    for row in ranges:
        low, high = number(row['low'], '情景下界'), number(row['high'], '情景上界')
        if low > high:
            raise ValueError('情景范围上下界颠倒。')
        a, b = forward(vary(model, row['key'], low)), forward(vary(model, row['key'], high))
        values = [a['enterprise_value'], b['enterprise_value']]
        rows.append({'key': row['key'], 'low': low, 'high': high, 'low_ev': values[0], 'high_ev': values[1],
                     'ev_span': None if None in values else abs(values[1] - values[0]),
                     'conflicts': a['conflicts'] + b['conflicts'], 'basis': 'user_declared_ranges_not_probability_or_information_value'})
    return sorted(rows, key=lambda r: (r['ev_span'] is None, -(r['ev_span'] or 0)))


def save_conditions(run, result, reverse_result=None, sensitivities=None):
    payload = {'forward': result, 'reverse': reverse_result, 'sensitivity': sensitivities,
               'input_sha256': digest(json.dumps(result['model'], sort_keys=True, ensure_ascii=False).encode())}
    run.write('realization_conditions.json', payload)
    run.write('realization_conditions.xlsx', workbook({'预测年度': pd.DataFrame(result['years']),
              '敏感性': pd.DataFrame(sensitivities or []), '绑定来源': pd.DataFrame(result['model'].get('bindings', [])),
              '缺口与冲突': pd.DataFrame([{'type': 'conflict', 'text': s} for s in result['conflicts']] +
                                        [{'type': 'gap', 'text': s} for s in result['gaps']])}))
    lines = ['# 盈利与估值兑现条件', '', '结果是显式假设情景；冲突时不提供有效估值。', '',
             '状态：' + result['status'], '企业价值（元）：' + str(result['enterprise_value']), '', '约束冲突：']
    lines += ['- ' + s for s in result['conflicts']] + ['', '待补证据：'] + ['- ' + s for s in result['gaps']]
    lines += ['', '口径与局限：'] + ['- ' + s for s in result['limitations']]
    if reverse_result:
        lines += ['', '反推：' + json.dumps(reverse_result, ensure_ascii=False)]
    run.write('realization_conditions.md', '\n'.join(lines))
    run.event('realization_conditions_computed', status=result['status'])
