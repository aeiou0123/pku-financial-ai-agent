"""Customer result recovery, incomplete evidence and bounded local file handling."""
import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.harness.documents import upload_issues
from src.harness.experience import stage
from src.harness.results import overview, read_output, record_title, snapshot_path, financial_problems
from src.harness.store import Run


def test_candidates_and_failed_financial_checks_do_not_advance_to_results():
    assert stage({'candidates':[{'value':'10'}]},[('file',b'x')],'check') == 2
    assert stage({'financial_result':([],{'errors':[{'issue':'source_file_missing'}]})},[], 'check') == 2
    assert stage({'financial_result':([{'value':'10'}],{'errors':[]})},[], 'check') == 3


def test_upload_preflight_lists_concurrent_problems_without_creating_files(tmp_path,monkeypatch):
    monkeypatch.setattr('src.harness.documents.MAX_BYTES',3)
    monkeypatch.setattr('src.harness.documents.MAX_TOTAL_BYTES',4)
    errors = upload_issues([('a.txt',b''),('A.txt',b'abcd'),('bad.exe',b'x')])
    assert len(errors) == 5
    assert any('空文件' in e for e in errors) and any('名称冲突' in e for e in errors)
    assert not list(tmp_path.iterdir())


def test_partial_reviews_preserve_scope_and_followup_in_recovered_summary(tmp_path):
    run = Run(tmp_path,'industry_research',[('report.txt',b'original')])
    run.write('research_input.json',{'context':{'question':'订单是否已经实现？'}})
    run.write('thesis_partial.json',{'complete':False,'assessments':[{'missing_in_supplied_material':['订单数量']}]})
    run.event('thesis_review_interrupted')
    before = (run.path/'run.json').read_bytes()
    summary = overview(run.path,run.metadata)
    assert record_title(run.metadata,run.path) == '订单是否已经实现？'
    facts = {r['项目']:r['本次记录'] for r in summary['facts']}
    assert facts['已处理的研究条件'] == '1' and facts['材料缺口提示'] == '1'
    assert '部分完成' in facts['审查范围']
    assert any('原会话' in s for s in summary['next_steps'])
    assert not summary['synthetic'] and (run.path/'run.json').read_bytes() == before


def test_conflicting_conditions_never_show_an_effective_value(tmp_path):
    run = Run(tmp_path,'tutorial_conditions',[])
    run.write('realization_conditions.json',{'forward':{'conflicts':['销量超过产能'],'gaps':[],'enterprise_value':999999}})
    summary = overview(run.path,run.metadata)
    assert summary['synthetic']
    facts = {r['项目']:r['本次记录'] for r in summary['facts']}
    assert facts['假设企业价值（元）'] == '约束冲突，暂缓估值'


@pytest.mark.parametrize('value',['{broken','{"errors":"missing"}', '{"days":5,"stocks":1,"total_return":NaN}'])
def test_corrupt_outputs_are_reported_instead_of_fabricating_zero_results(tmp_path,value):
    run = Run(tmp_path,'financial',[])
    name = 'metrics.json' if 'days' in value else 'quality_report.json'
    run.write(name,value)
    summary = overview(run.path,run.metadata)
    assert not summary['facts'] and summary['notices']


def test_readers_reject_unknown_files_paths_and_oversized_output(tmp_path):
    run = Run(tmp_path,'quant',[])
    run.write('quant_report.md','long report')
    with pytest.raises(ValueError,match='上限'):
        read_output(run.path,'quant_report.md',3)
    with pytest.raises(ValueError):
        read_output(run.path,'../sources/private.txt')
    with pytest.raises(ValueError):
        snapshot_path(tmp_path,'../private')
    assert read_output(run.path,'metrics.json') is None


def test_history_filters_previews_and_downloads_snapshot_without_originals(tmp_path):
    root = tmp_path/'work/harness_runs'
    run = Run(root,'quant',[('真实待核行情.csv',b'private input')])
    run.write('metrics.json',{'days':6,'stocks':2,'total_return':-.12,'max_drawdown':-.2,'fee_bps_single_side':10})
    run.write('quant_report.md','# 上传样本说明\n\n不能称为样本外收益。')
    run.event('quant_completed')
    app = AppTest.from_string(f'from pathlib import Path\nfrom src.harness.experience import history\nhistory(Path({str(tmp_path)!r}))',default_timeout=25).run()
    assert not app.exception
    assert any('下一步' in md.value for md in app.markdown)
    summary = app.table[0].value.set_index('项目')['本次记录'].to_dict()
    assert summary['本次样本净收益'] == '-12.00%'
    assert any('不能称为样本外收益' in md.value for md in app.markdown)
    app.text_input[0].set_value('不存在').run()
    assert not app.table and any('没有匹配记录' in i.value for i in app.info)
    app.text_input[0].set_value('待核行情').run()
    assert app.table and not app.exception
    assert (run.path/'sources/source_真实待核行情.csv').read_bytes() == b'private input'


def test_financial_failure_guidance_includes_correct_csv_line():
    rows = financial_problems([{'line':2,'issue':'source_hash_mismatch'},{'issue':'duplicate_metric_requires_review'}])
    assert rows[0]['位置'] == 'CSV第2行（含表头）' and '不同版本' in rows[0]['需要处理']
    assert '更正版本' in rows[1]['需要处理']
