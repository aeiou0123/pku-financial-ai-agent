"""A failed repeat must not display the successful result from the previous attempt."""
from pathlib import Path
import hashlib
from streamlit.testing.v1 import AppTest


def item(elements,label):
    return next(e for e in elements if e.label==label)


def test_repeated_diagnostic_failure_clears_stale_result_and_keeps_prior_snapshot(monkeypatch):
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'harness_app.py'),default_timeout=25).run()
    item(app.button,'测试策略表现').click().run()
    item(app.button,'载入这项任务的样例').click().run()
    item(app.checkbox,'我确认价格已经复权，因子可得时间真实；本次按完整面板、下一交易日收盘成交研究。').check().run()
    item(app.button,'校验数据并运行回测').click().run()
    app.toggle(key='enable_strategy_diagnostics').set_value(True).run()
    item(app.checkbox,'我预先声明这些参数；本次是已查看样本的研究，不称未触碰留出集。').check().run()
    item(app.button,'运行策略诊断').click().run()
    assert not app.exception and app.session_state['strategy_diagnostic_result']
    prior=app.session_state['run']
    before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (prior.path/'outputs').iterdir()}
    def failed(*args,**kwargs):
        raise ValueError('合成故障：本次诊断未完成')
    monkeypatch.setattr('src.harness.strategy_diagnostics.diagnose',failed)
    item(app.button,'运行策略诊断').click().run()
    assert not app.exception
    assert 'strategy_diagnostic_result' not in app.session_state
    assert app.session_state['run'].metadata['status']=='strategy_diagnostic_failed'
    assert app.session_state['run'].path != prior.path
    assert all(hashlib.sha256((prior.path/'outputs'/n).read_bytes()).hexdigest()==sha for n,sha in before.items())
    assert any('这一步需要修正' in e.value for e in app.error)
    assert any('本次诊断未完成' in e.value for e in app.markdown)
