import json

import numpy as np
import pandas as pd
import pytest

from src.harness.quant import prepare, backtest
from src.harness.store import Run
from src.harness.strategy_diagnostics import diagnose


def panel():
    dates = pd.bdate_range('2024-12-16', periods=75)
    frame = pd.DataFrame([{'date': dt.date().isoformat(), 'stock': f'{s:06d}', 'close': 100 * np.exp(.001 * s * i + .015 * np.sin(i + s))}
                          for i, dt in enumerate(dates) for s in (1, 2, 3)])
    return prepare(frame, {k: k for k in ('date', 'stock', 'close')}, 'momentum')


def settings(lb=5, fee=10):
    return {'lookback': lb, 'top_n': 1, 'fee_bps': fee, 'direction': 'high'}


def test_different_windows_compared_on_common_carried_account_returns(tmp_path):
    data = panel()
    report, nav = diagnose(Run(tmp_path / 'runs', 'diagnostic', []), data, 'momentum', [settings(), settings(20)], tmp_path / 'registry.jsonl')
    assert len({(r['start'], r['end'], r['days']) for r in report['comparisons']}) == 1
    expected = backtest(data, strategy='momentum', **settings())['daily'].loc[nav.index]
    assert report['comparisons'][0]['net_return'] == pytest.approx((1 + expected['net_return']).prod() - 1)
    assert len(report['year_segments']) == 2  # Common interval begins in 2025 for both accounts.
    assert report['comparisons'][0]['full_lifecycle_return_with_entry_fee'] != report['comparisons'][0]['net_return']


def test_fee_stress_all_groups_retained_in_declared_order(tmp_path):
    report, _ = diagnose(Run(tmp_path / 'runs', 'diagnostic', []), panel(), 'momentum', [settings(fee=0), settings(fee=100)], tmp_path / 'registry.jsonl')
    assert [r['fee_bps'] for r in report['comparisons']] == [0, 100]
    assert report['comparisons'][0]['gross_net_gap'] == pytest.approx(0)
    assert report['comparisons'][1]['gross_net_gap'] > 0
    assert report['comparisons'][0]['net_return'] > report['comparisons'][1]['net_return']


def test_seen_ranges_and_failed_parameters_registered_not_erased(tmp_path):
    registry = tmp_path / 'registry.jsonl'
    first = Run(tmp_path / 'runs', 'diagnostic', [])
    report, _ = diagnose(first, panel(), 'momentum', [settings(), {**settings(), 'top_n': 99}], registry)
    assert len(report['failures']) == 1
    second = Run(tmp_path / 'runs', 'diagnostic', [])
    next_report, _ = diagnose(second, panel(), 'momentum', [settings()], registry)
    assert first.path.name in next_report['declaration']['prior_overlapping_run_ids']
    assert 'not_untouched' in next_report['declaration']['classification']
    with pytest.raises(ValueError, match='全部声明'):
        diagnose(Run(tmp_path / 'runs', 'diagnostic', []), panel(), 'momentum', [{**settings(), 'top_n': 99}], registry)
    assert len(registry.read_text(encoding='utf-8').splitlines()) == 3


def test_factor_future_availability_masked_and_reported(tmp_path):
    frame = panel().copy()
    frame['date'] = frame['date'].dt.strftime('%Y-%m-%d')
    frame['factor'] = frame['stock'].astype(float)
    frame['available_at'] = frame['date'] + 'T14:00:00+08:00'
    frame.loc[frame['stock'] == '000003', 'available_at'] = frame.loc[frame['stock'] == '000003', 'date'] + 'T16:00:00+08:00'
    data = prepare(frame, {k: k for k in ('date', 'stock', 'close', 'factor', 'available_at')}, 'factor')
    report, _ = diagnose(Run(tmp_path / 'runs', 'diagnostic', []), data, 'factor', [settings()], tmp_path / 'registry.jsonl')
    assert report['timing']['late_availability_masked_rows'] == 75
    run = backtest(data, strategy='factor', **settings())
    assert '000003' not in set(run['positions']['stock'])


def test_history_corruption_does_not_become_new_holdout(tmp_path):
    registry = tmp_path / 'registry.jsonl'; registry.write_text('broken', encoding='utf-8')
    with pytest.raises(json.JSONDecodeError):
        diagnose(Run(tmp_path / 'runs', 'diagnostic', []), panel(), 'momentum', [settings()], registry)
