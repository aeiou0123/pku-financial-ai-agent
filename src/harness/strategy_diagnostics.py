"""Declared perturbations on a common interval with carried portfolios and seen-data history."""
from __future__ import annotations

from .module_stamp import source_stamp
_c2v_loaded_source_hash = source_stamp(__file__)

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from .documents import digest
from .quant import backtest
from .exports import workbook


def performance(daily):
    net = daily['net_return']
    nav = (1 + net).cumprod()
    gross = (1 + daily['gross_return']).prod() - 1
    benchmark = (1 + daily['benchmark_net_return']).prod() - 1
    std = net.std(ddof=1)
    return {'days': len(daily), 'start': daily.index.min().date().isoformat(), 'end': daily.index.max().date().isoformat(),
            'net_return': float(nav.iloc[-1] - 1), 'gross_return': float(gross), 'benchmark_net_return': float(benchmark),
            'gross_net_gap': float(gross - (nav.iloc[-1] - 1)), 'excess_compounded_return': float(nav.iloc[-1] - 1 - benchmark),
            'max_drawdown': float((nav / nav.cummax().clip(lower=1) - 1).min()),
            'sharpe_252_zero_rf': None if not std or not math.isfinite(std) else float(net.mean() / std * np.sqrt(252)),
            'turnover_two_sided': float(daily['turnover_two_sided'].sum()),
            'sum_cost_fractions': float(daily['cost_fraction_pretrade_nav'].sum())}


def diagnose(run, data, strategy, declared, registry: Path):
    """All configurations must be declared before computation; never automatically choose a winner."""
    if not isinstance(declared, list) or not 1 <= len(declared) <= 12:
        raise ValueError('预先声明1—12组参数，不自动搜索最优组。')
    if len(data) * len(declared) > 12000000:
        raise ValueError('本版诊断上限为1200万行×组，请缩减数据或参数。')
    required = {'lookback', 'top_n', 'fee_bps', 'direction'}
    for item in declared:
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError('参数声明须含lookback、top_n、fee_bps、direction。')
        if type(item['lookback']) is not int or type(item['top_n']) is not int:
            raise ValueError('窗口和持仓数须为整数。')
    serialized = [json.dumps(item, sort_keys=True) for item in declared]
    if len(set(serialized)) != len(serialized):
        raise ValueError('参数组重复，请去重。')
    fingerprint = digest(data.to_csv(index=False).encode())
    previous = []
    if registry.exists():
        # Corrupted history must not silently become a fresh holdout.
        previous = [json.loads(line) for line in registry.read_text(encoding='utf-8').splitlines() if line.strip()]
    start, end = data['date'].min().date().isoformat(), data['date'].max().date().isoformat()
    overlaps = [p for p in previous if p['start'] <= end and start <= p['end']]
    entry = {'run_id': run.path.name, 'data_sha256': fingerprint, 'start': start, 'end': end,
             'strategy': strategy, 'declared_parameters': declared,
             'classification': 'research_seen_interval_not_untouched_holdout',
             'prior_overlapping_run_ids': [p['run_id'] for p in overlaps]}
    registry.parent.mkdir(parents=True, exist_ok=True)
    # Register the attempt first, including failures; stopping a run cannot erase that the interval was inspected.
    with registry.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(entry, ensure_ascii=False, allow_nan=False) + '\n')
    run.write('experiment_declaration.json', entry)
    run.event('strategy_diagnostic_declared', configurations=len(declared))
    results, failures = [], []
    for index, settings in enumerate(declared):
        try:
            result = backtest(data, strategy=strategy, **settings)
            results.append((index, settings, result))
        except (ValueError, TypeError) as exc:
            failures.append({'index': index, 'settings': settings, 'reason': str(exc)})
    if not results:
        run.write('strategy_diagnostic_failures.json', failures)
        raise ValueError('全部声明参数组均无法回测；已保留失败与实验登记。')
    # Start AFTER the latest initial trade: compare daily carried-account returns, not differently warmed-up NAVs.
    first = max(r['daily'].index[0] for _, _, r in results)
    common_dates = results[0][2]['daily'].index
    for _, _, r in results[1:]:
        common_dates = common_dates.intersection(r['daily'].index)
    common_dates = common_dates[common_dates > first]
    if len(common_dates) < 3:
        raise ValueError('不同窗口的共同持仓收益区间不足3日。声明已登记；请增加样本。')
    comparisons, segments, navs = [], [], pd.DataFrame(index=common_dates)
    for index, settings, result in results:
        daily = result['daily'].loc[common_dates]
        comparisons.append({'index': index, **settings, **performance(daily),
                            'full_lifecycle_return_with_entry_fee': result['metrics']['total_return']})
        navs['declared_' + str(index)] = (1 + daily['net_return']).cumprod()
        for year, part in daily.groupby(daily.index.year):
            segments.append({'index': index, 'year': int(year), **performance(part)})
        run.write(f'diagnostic_daily_{index}.csv', daily.to_csv(index_label='date').encode('utf-8-sig'))
    timing = {'rows': len(data), 'stocks': int(data['stock'].nunique()), 'balanced_panel': True,
              'late_availability_masked_rows': int((~data['eligible']).sum()) if 'eligible' in data else 0,
              'missing_factor_after_timing_filter': int(data['factor'].isna().sum()) if 'factor' in data else 0,
              'execution': 'T_close_signal; T+1_close_trade; T+2_first_return',
              'price_adjustment': 'operator_attestation_not_authenticated'}
    report = {'declaration': entry, 'comparisons': comparisons, 'year_segments': segments, 'failures': failures,
              'timing': timing, 'common_interval': {'start': common_dates[0].date().isoformat(), 'end': common_dates[-1].date().isoformat(), 'days': len(common_dates)},
              'limitations': ['参数按声明顺序展示，不选最佳组，不证明样本外有效。',
                              '比较区间从最晚首次建仓后开始，各账户保留历史持仓，不免费重新建仓；区间以前的买入费仅计入完整生命周期收益。',
                              '年度分段保留原账户收益和成本，净值从1缩放用于展示，不重设持仓；分段回撤只对应分段峰值。',
                              '基准同一共同区间、等权日再平衡及同费率；无末期强制清仓、涨跌停和冲击模型。',
                              '历史登记按日期重叠保守标记；不识别同样日期是否是不同市场，不能据此声明新留出集。',
                              '通用工作台诊断不替代比赛匿名因子技术题；2020已查看。']}
    run.write('strategy_diagnostics.json', report)
    run.write('experiment_history.json', previous + [entry])
    run.write('strategy_diagnostics.xlsx', workbook({'共同区间': pd.DataFrame(comparisons), '年度分段': pd.DataFrame(segments),
              '失败组': pd.DataFrame(failures), '共同区间净值': navs.rename_axis('date').reset_index()}))
    run.write('strategy_diagnostics.md', '# 策略诊断\n\n' + json.dumps(report['common_interval'], ensure_ascii=False) + '\n\n' +
              '\n'.join('- ' + s for s in report['limitations']))
    run.event('strategy_diagnostics_completed', configurations=len(results), failed=len(failures))
    return report, navs
