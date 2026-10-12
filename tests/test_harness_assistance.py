"""User decisions: concurrent data faults and draft evidence must remain distinguishable."""
import io
import json
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from src.harness.assistance import quant_audit, evidence_actions, audit_tables, workbook
from src.harness.quant import prepare

MAPPING = {key:key for key in ('date','stock','close','factor','available_at')}


def panel():
    return pd.DataFrame([
        {'date':day,'stock':stock,'close':'10','factor':'1', 'available_at':day+'T07:00:00Z'}
        for day in ('2025-01-02','2025-01-03') for stock in ('000001','600000')])


def test_collects_multiple_faults_and_does_not_repair_input():
    frame = panel().iloc[:3].copy()
    frame = pd.concat([frame, frame.iloc[[0]]],ignore_index=True)
    frame.loc[1,'close'] = '0'
    frame.loc[1,'factor'] = 'infinity'
    frame.loc[2,'available_at'] = '2025-01-03T14:00:00'
    before = frame.copy(deep=True)
    report = quant_audit(frame,MAPPING,'factor')
    issues = {row['问题']:row['数量'] for row in report['issues']}
    assert issues['同日同股重复数据行'] == 2
    assert issues['日期与股票组合缺失'] == 1
    assert issues['价格缺失或不是正数'] == 1
    assert issues['因子值无法解析或无穷'] == 1
    assert issues['因子可得时间无效'] == 1
    assert not report['ready']
    pd.testing.assert_frame_equal(before,frame)
    tables = pd.read_excel(io.BytesIO(workbook(audit_tables(report))),sheet_name=None)
    assert len(tables['问题清单']) == 5
    assert tables['检查概况']['格式检查通过'].iloc[0] == False


def test_timezone_equivalence_and_late_factors_match_actual_backtest_filter():
    frame = panel()
    frame.loc[0,'available_at'] = '2025-01-02T15:00:00+08:00'
    frame.loc[1,'available_at'] = '2025-01-02T07:00:01Z'
    frame.loc[2,'factor'] = ''
    audit = quant_audit(frame,MAPPING,'factor')
    cleaned = prepare(frame,MAPPING,'factor')
    assert audit['ready']
    assert audit['issues'][0]['数量'] == 1 and not audit['issues'][0]['阻挡运行']
    assert int((~cleaned['eligible']).sum()) == 1
    assert int(cleaned['factor'].isna().sum()) == 2


@pytest.mark.parametrize('field,value', [('stock','1'),('date','2025-02-30'),('date','2025-1-2'),('close','nan'),('close','inf'),('available_at','2025-01-02')])
def test_invalid_values_fail_both_audit_and_strict_preparation(field,value):
    frame = panel()
    frame.loc[0,field] = value
    assert not quant_audit(frame,MAPPING,'factor')['ready']
    with pytest.raises((ValueError,TypeError)):
        prepare(frame,MAPPING,'factor')


def test_empty_and_duplicate_mapping_are_reported_without_crash():
    assert not quant_audit(panel().iloc[:0],MAPPING,'factor')['ready']
    assert not quant_audit(panel(),{'date':'date','stock':'date','close':'close'},'momentum')['ready']


def test_conflicts_forecasts_model_gaps_and_unprocessed_conditions_are_separate():
    plan = {'conditions':[{'id':'a','label':'订单'},{'id':'b','label':'产能'}]}
    review = {'assessments':[{'condition':plan['conditions'][0],
        'evidence':[{'stance':'supports','fact_type':'forecast','source_file':'a.pdf','source_locator':'page:1'},
                    {'stance':'contradicts','fact_type':'historical','source_file':'b.pdf','source_locator':'page:2'}],
        'missing_in_supplied_material':['核实销量','核实销量'], 'parameter_candidates':[{'id':'p1'}]}]}
    actions = evidence_actions(review,plan)
    kinds = actions['事项'].tolist()
    assert kinds.count('模型提出的材料缺口') == 1
    assert {'支持与反证冲突','未来陈述的性质','参数候选确认','尚未运行的条件'} <= set(kinds)
    assert actions.loc[actions['事项']=='尚未运行的条件','状态'].iloc[0] == '尚未处理'
    assert actions.loc[actions['事项']=='模型提出的材料缺口','状态'].iloc[0] == '待核实缺口'
    assert 'b.pdf' in actions['现有定位'].iloc[0]
    with pytest.raises(ValueError,match='重复'):
        evidence_actions({'assessments':review['assessments']*2},plan)


def test_data_audit_can_run_without_key_and_changed_mapping_hides_old_result():
    root = Path(__file__).resolve().parents[1]
    app = AppTest.from_file(str(root/'harness_app.py'),default_timeout=25).run()
    button = lambda label: next(b for b in app.button if b.label==label)
    button('测试策略表现').click().run()
    button('载入这项任务的样例').click().run()
    button('检查数据（不调用模型）').click().run()
    assert not app.exception
    assert any('数据格式检查通过' in m.value for m in app.success)
    assert not app.session_state['api_secret']
    audit = app.session_state['quant_audit'][1]
    assert audit['summary']['股票数'] == 4 and audit['rows'] > 0
    next(s for s in app.selectbox if s.label=='已复权收盘价').set_value('date').run()
    assert not any('数据格式检查通过' in m.value for m in app.success)
    assert not app.exception
