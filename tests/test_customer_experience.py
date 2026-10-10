"""First-use paths, real local calculations and recovery exports."""
import io
import json
from pathlib import Path
import shutil
import zipfile

import pytest
from streamlit.testing.v1 import AppTest

from src.harness.experience import offline_example, saved_bundle, saved_runs
from src.harness.store import Run

ROOT = Path(__file__).resolve().parents[1]


def item(elements, label):
    return next(element for element in elements if element.label == label)


def example_root(tmp_path):
    target = tmp_path/'docs/harness/examples'
    target.mkdir(parents=True)
    for path in (ROOT/'docs/harness/examples').glob('*'):
        shutil.copy2(path, target/path.name)
    return tmp_path


def test_first_use_starts_with_customer_tasks_and_sample_never_confirms_evidence():
    app = AppTest.from_file(str(ROOT/'harness_app.py'), default_timeout=25).run()
    assert any(title.value == '从一个研究问题开始' for title in app.title)
    item(app.button, '检查研究观点').click().run()
    assert app.session_state['desk_page'] == '工作区'
    item(app.button, '载入这项任务的样例').click().run()
    assert app.session_state['desk_example'] == 'industry'
    assert item(app.text_input,'研究公司').value == '公司甲'
    assert item(app.text_input,'产品／业务范围').value == '减速器'
    assert not item(app.checkbox,'已核对日期和适用范围 · synthetic_industry.txt').value
    assert item(app.button,'审查证据／继续').disabled
    assert not any(button.label == '计算兑现条件' for button in app.button)
    assert not app.exception


def test_tutorial_calculations_use_local_tools_and_preserve_capacity_conflicts(tmp_path, monkeypatch):
    monkeypatch.setattr('src.harness.api.ModelClient._complete', lambda *a,**kw: pytest.fail('tutorial must not call provider'))
    root = example_root(tmp_path)
    base = offline_example(root, 'industry', 1.)
    conflict = offline_example(root, 'industry', 2.)
    read = lambda run: json.loads((run.path/'outputs/realization_conditions.json').read_text(encoding='utf-8'))['forward']
    assert read(base)['enterprise_value'] is not None
    assert read(conflict)['enterprise_value'] is None and read(conflict)['conflicts']
    quant = offline_example(root, 'quant')
    metrics = json.loads((quant.path/'outputs/metrics.json').read_text(encoding='utf-8'))
    assert metrics['days'] > 0 and (quant.path/'outputs/daily.csv').is_file()


def test_saved_outputs_are_recoverable_without_exporting_originals_or_cache(tmp_path):
    run = Run(tmp_path, 'financial', [('private.txt', b'original must stay private')])
    run.write('report.md','reviewable result')
    (run.path/'cache').mkdir()
    (run.path/'cache/model.json').write_text('private response')
    malformed = tmp_path/'20260101_010101_aaaaaaaaaa'
    malformed.mkdir()
    (malformed/'run.json').write_text('{broken')
    assert [r['id'] for r in saved_runs(tmp_path)] == [run.path.name]
    with zipfile.ZipFile(io.BytesIO(saved_bundle(tmp_path, run.path.name))) as archive:
        assert archive.testzip() is None and 'outputs/report.md' in archive.namelist()
        assert not any(n.startswith(('sources/','cache/')) for n in archive.namelist())
        manifest = json.loads(archive.read('manifest.json'))
        assert set(manifest) == set(archive.namelist()) - {'manifest.json'}
    with pytest.raises(ValueError):
        saved_bundle(tmp_path, '../private')


def test_tutorial_page_can_run_and_switch_examples_without_stale_result(tmp_path):
    root = example_root(tmp_path)
    app = AppTest.from_string(f'from pathlib import Path\nfrom src.harness.experience import guide\nguide(Path({str(root)!r}))',default_timeout=25).run()
    item(app.button, '运行本地样例').click().run()
    assert any(metric.label == '假设业务价值（元）' for metric in app.metric)
    item(app.slider, '销量相对基准的倍数').set_value(2.).run()
    assert not app.metric
    item(app.button, '运行本地样例').click().run()
    assert any('暂缓估值' in error.value for error in app.error)
    item(app.selectbox,'我想学习的任务').set_value('quant').run()
    assert not app.metric
    item(app.button,'运行本地样例').click().run()
    assert any(metric.label == '合成样本净收益' for metric in app.metric)
    assert not app.exception
