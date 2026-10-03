"""Read immutable completed runs and prepare source-bound technical report data."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from competition import baseline as b
from competition import experiment as e


def metrics(account):
    net = np.asarray(account['daily_net_returns'], dtype=float)
    gross = np.asarray(account['daily_gross_returns'], dtype=float)
    nav = np.asarray([1.] + [d['nav'] for d in account['details']])
    sd = net.std(ddof=1)
    sharpe = float(np.sqrt(252) * net.mean() / sd)
    if not np.isclose(sharpe, account['sharpe'], rtol=1e-12, atol=1e-12):
        raise ValueError('Report Sharpe differs from official accounting')
    return {'days': len(net), 'net_sharpe': account['sharpe'],
            'gross_sharpe_same_holdings': float(np.sqrt(252) * gross.mean() / gross.std(ddof=1)),
            'final_nav': account['final_nav'],
            'net_annualized_return_252': float(account['final_nav'] ** (252 / len(net)) - 1),
            'net_annualized_volatility_252': float(sd * np.sqrt(252)),
            'max_drawdown_including_initial_nav': float(np.min(nav / np.maximum.accumulate(nav) - 1))}


def build(run, output):
    run, output = Path(run), Path(output)
    locked = e.checked_lock(run)
    holdout = e.checked_holdout(run, locked)
    final = json.loads((run / 'final/receipt.json').read_text())
    if final.get('status') != 'COMPLETE' or final.get('official_check', {}).get('status') != 'VALID':
        raise ValueError('Final deliverables are not complete')
    for name, digest in final['files_sha256'].items():
        if b.sha256(run / 'final' / name) != digest:
            raise ValueError('Final deliverable changed')
    selected = locked['selected']
    ai = list(e.ALPHAS).index(selected['alpha'])
    bi = list(e.BONUSES).index(selected['hold_bonus'])
    rows = []
    for fold in list(e.FOLDS) + [e.HOLDOUT]:
        parent = 'holdout' if fold['id'] == '2020' else 'development'
        directory = run / parent / (f"2020_a00_b00" if parent == 'holdout' else f"{fold['id']}_a{ai:02d}_b{bi:02d}")
        account = json.loads((directory / 'accounting.json').read_text())
        control = json.loads((run / 'controls' / fold['id'] / 'accounting.json').read_text())
        result = json.loads((directory / 'result.json').read_text())
        rows.append({'fold': fold, 'strategy': metrics(account), 'fixed20': metrics(control),
                     'turnover': result['turnover'], 'accounting_sha256': b.sha256(directory / 'accounting.json')})
    # Only 2020 public-training NAV enters the editable chart. No test returns exist.
    validation = pd.read_csv(run / 'holdout/2020_a00_b00/validation.csv', dtype=str)
    dates = sorted(validation.date.unique())
    account = json.loads((run / 'holdout/2020_a00_b00/accounting.json').read_text())
    control = json.loads((run / 'controls/2020/accounting.json').read_text())
    picks = [i for i, d in enumerate(dates) if i == len(dates) - 1 or dates[i + 1][:7] != d[:7]]
    chart = {'categories': ['起点'] + [dates[i][5:7] + '月末' for i in picks],
             'strategy_nav': [1.] + [account['details'][i]['nav'] for i in picks],
             'fixed20_nav': [1.] + [control['details'][i]['nav'] for i in picks],
             'sample_note': 'Public 2020 holdout only. Month-end actual account NAV; initial NAV 1. Terminal fee included.'}
    runtime = [json.loads((run.parent / f'official_{phase}_runtime_20261003.json').read_text())
               for phase in ('develop', 'holdout', 'finalize')]
    data = {'date': '2026-10-03', 'scope': 'REAL_OFFICIAL_DATA_BASELINE_NOT_COMPETITION_SCORE',
            'selection_rule': e.RULE, 'selected': selected, 'candidates': locked['candidates'],
            'fold_comparisons': rows, 'holdout_used_for_selection': False,
            'holdout_attempts': 1, 'test_sharpe': None, 'final': final,
            'environment': e.read_json(run / 'plan.json')['environment'], 'runtime': runtime,
            'runtime_total_seconds': sum(x['elapsed_seconds'] for x in runtime),
            'chart': chart, 'provenance_sha256': {name: b.sha256(run / name) for name in
                ('plan.json', 'selection_lock.json', 'holdout_started.json', 'holdout_summary.json', 'final/receipt.json')},
            'data_sha256': b.DATA_SHA, 'tools_sha256': b.TOOLS_SHA,
            'prediction_run': e.read_json(run / 'final/prediction/run_summary.json'),
            'reproduction_run': e.read_json(run / 'final/reproduction/run_summary.json'),
            'ai_tools': final['ai_tools'], 'limitations': [
                'Anonymous factors have no verified economic names.',
                'Single 2020 holdout, no independent multi-year test-return evaluation.',
                'Development selection uses 9 candidates and has selection risk.',
                'Full test-period returns and competition rank/bonus are not public.',
                'Prediction determinism is checked in the same Linux environment only.',
                'Compute monetary cost is not metered; no model API calls.']}
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    return data


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    data = build(a.run, a.out)
    print(json.dumps({'status': 'REPORT_DATA_CREATED', 'selected': data['selected'],
                      'test_sharpe': data['test_sharpe']}, ensure_ascii=False))
