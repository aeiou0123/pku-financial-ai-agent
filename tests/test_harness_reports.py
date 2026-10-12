"""Readable exports keep scope, calculation values and literal untrusted content."""
from datetime import date

import pandas as pd
import pytest

from src.harness.presentation import report_markup,literal_markup
from src.harness.reports import quant_report,financial_report,thesis_report
from src.harness.experience import offline_example
from src.harness.financial import dcf,save_dcf
from src.harness.store import Run
from src.harness.results import overview,FILES,REPORTS


@pytest.mark.parametrize('payload',['<script>alert(1)</script>','<img src="https://example.org/probe">',
    '![extract](https://example.org/probe.png)','[click](javascript:alert(1))','<iframe src="https://example.org"></iframe>'])
def test_report_and_model_text_never_create_active_markup(payload):
    html=report_markup('# Report\n\n'+payload+'\n\n| Name | Value |\n| --- | --- |\n| quote | '+payload+' |')
    assert '<script' not in html and '<img' not in html and '<iframe' not in html and '<a ' not in html
    assert '<table>' in html and '<h2>Report</h2>' in html
    assert '<img' not in literal_markup(payload) and '<script' not in literal_markup(payload)


def test_quant_report_includes_actual_benchmark_settings_and_undefined_sharpe():
    result={'metrics':{'strategy':'factor','lookback':None,'top_n':1,'direction':'low','fee_bps_single_side':10,
        'days':2,'stocks':2,'total_return':-.03,'max_drawdown':-.04,'sharpe_zero_rf_252':None,'limitations':['未模拟停牌']},
        'daily':pd.DataFrame({'benchmark_nav':[1.,1.02]},index=pd.to_datetime(['2026-01-05','2026-01-06']))}
    text=quant_report(result)
    assert '2.00%' in text and '-3.00%' in text and '-4.00%' in text
    assert '2026-01-05 至 2026-01-06' in text and '取较低值' in text and '不适用' in text
    assert 'None' not in text and '未计算' in text and '样本外收益' in text


def test_conflicted_scenario_export_withholds_value_and_avoids_internal_status(tmp_path):
    examples=tmp_path/'docs/harness/examples';examples.mkdir(parents=True)
    run=offline_example(tmp_path,'industry',2.)
    text=(run.path/'outputs/realization_conditions.md').read_text(encoding='utf-8')
    assert '暂缓估值' in text and '未计算：存在约束冲突' in text
    assert 'None' not in text and 'constraint_conflict_valuation_withheld' not in text
    assert '## 年度预测' in text and '订单未绑定证据' in text


def test_partial_financial_export_preserves_dates_scope_revision_and_missing_batch():
    ratios=[{'company':'公司甲','report_period':'2024-12-31','published_at':'2025-04-01','statement_scope':'parent',
        'revision_flag':'restated','period_type':'annual','ratio':'gross_margin','value':.23}]
    text=financial_report(date(2025,5,1),[{}],{'status':'partial','warnings':[{}]},ratios,
        {'complete':False,'completed_batches':1,'total_batches':3})
    assert '23.00%' in text and '母公司' in text and 'restated' in text
    assert '2025-04-01' in text and '完成1／3批' in text and '部分候选' in text
    assert '存在缺项' in text and '来源' in text


def test_thesis_report_keeps_forecast_and_counterevidence_explicit():
    text=thesis_report({'question':'订单是否支持扩产？'},[{'condition':{'label':'订单'},'status':'conflicting_candidates',
        'evidence':[{'stance':'contradicts','fact_type':'forecast','quote':'计划订单不等于实际成交',
            'source_file':'report.txt','source_locator':'line:2'}],'missing_in_supplied_material':['实际成交量']}])
    assert '反证候选 · 预测或目标' in text and '支持与反证并存，待核对' in text
    assert 'report.txt · line:2' in text and '实际成交量' in text
    assert 'conflicting_candidates' not in text


def test_report_preview_is_bounded_and_unknown_markup_stays_literal():
    text=report_markup('start\n\n'+('a'*21000)+'\n\nEND_NOT_IN_PREVIEW')
    assert 'END_NOT_IN_PREVIEW' not in text and len(text)<20500
    assert '![extract]' in report_markup('![extract](https://example.org/probe)')


def test_cashflow_report_keeps_five_actual_assumptions_and_withholds_missing_equity(tmp_path):
    run=Run(tmp_path,'valuation',[])
    save_dcf(run,dcf([100,110,120,130,140],.1,.02))
    text=(run.path/'outputs/valuation.md').read_text(encoding='utf-8')
    assert '| 5 | 140.00 |' in text and '未计算：未提供净债务' in text
    assert '10.00%' in text and '2.00%' in text and 'None' not in text


def test_saved_diagnostic_workflows_are_recognized_with_correct_limits(tmp_path):
    run=Run(tmp_path,'earnings_diagnostics',[])
    run.write('earnings_diagnostics.json',{'bridge':[],'earlier':'2023-12-31','later':'2024-12-31','target_change_cny':'1234.56'})
    summary=overview(run.path,run.metadata)
    assert any(r['本次记录']=='1234.56' for r in summary['facts'])
    assert any('不是技术进步' in r for r in summary['next_steps'])
    assert 'earnings_diagnostics.md' in REPORTS and 'strategy_diagnostics.xlsx' in FILES
