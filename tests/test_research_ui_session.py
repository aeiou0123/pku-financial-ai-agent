"""Real widget reruns for source confirmation and the evidence review gate."""
from streamlit.testing.v1 import AppTest


def desk(tmp_path):
    script = f'''
from pathlib import Path
import streamlit as st
from src.harness.research_ui import render
st.session_state['binding'] = st.text_input('test binding', value='first question')
question = st.text_area('研究要求', value='扩产能否支持增长？')
counter = st.checkbox('include counterevidence', value=True)
changed = st.checkbox('replace source bytes')
uploads = [('capacity.txt', ('设计产能100000台/年。' + ('已更新' if changed else '')).encode())]
if counter:
    uploads.append(('delay.txt', '设备调试延期。'.encode()))
render(Path({str(tmp_path)!r}), uploads, question, lambda: None)
'''
    return AppTest.from_string(script, default_timeout=25).run()


def item(elements, label):
    return next(element for element in elements if element.label == label)


def confirm_plan(app):
    item(app.checkbox, '我确认这些条件及检索词，并会核对模型返回的支持材料和反证。').check().run()


def source(app, name, published):
    item(app.text_input, '披露日期 · ' + name).set_value(published).run()
    item(app.checkbox, '已核对日期和适用范围 · ' + name).check().run()


def test_plan_confirmation_does_not_hide_missing_sources_and_valid_source_enables_review(tmp_path, monkeypatch):
    calls = []
    def review(run, client, plan, documents, scope, context):
        calls.append(scope)
        return {'assessments': []}
    monkeypatch.setattr('src.harness.research_ui.review_thesis', review)
    app = desk(tmp_path)
    item(app.text_input, '研究公司').set_value('公司甲').run()
    confirm_plan(app)
    assert item(app.button, '审查证据／继续').disabled
    assert any('capacity.txt：披露日期未知或格式错误' in message.value for message in app.warning)
    assert any('已核对日期和适用范围' in message.value for message in app.info)
    source(app, 'capacity.txt', '2099-01-01')
    confirm_plan(app)
    assert item(app.button, '审查证据／继续').disabled
    assert any('晚于信息截止日' in message.value for message in app.warning)
    item(app.text_input, '披露日期 · capacity.txt').set_value('2026-01-01').run()
    source(app, 'delay.txt', '2026-02-01')
    confirm_plan(app)
    assert not item(app.button, '审查证据／继续').disabled
    item(app.button, '审查证据／继续').click().run()
    assert len(calls) == 1 and len(calls[0]['eligible']) == 2
    assert not app.exception


def test_question_edit_keeps_file_declarations_but_requires_new_plan_confirmation(tmp_path):
    app = desk(tmp_path)
    item(app.text_input, '研究公司').set_value('公司甲').run()
    source(app, 'capacity.txt', '2026-01-01')
    confirm_plan(app)
    assert not item(app.button, '审查证据／继续').disabled
    item(app.text_input, 'test binding').set_value('edited question').run()
    item(app.text_area, '研究要求').set_value('新问题：延期会影响销量吗？').run()
    assert item(app.text_input, '披露日期 · capacity.txt').value == '2026-01-01'
    assert item(app.checkbox, '已核对日期和适用范围 · capacity.txt').value
    assert not item(app.checkbox, '我确认这些条件及检索词，并会核对模型返回的支持材料和反证。').value
    assert item(app.button, '审查证据／继续').disabled
    confirm_plan(app)
    assert not item(app.button, '审查证据／继续').disabled
    assert not app.exception


def test_adding_source_keeps_old_declaration_but_replacing_bytes_requires_confirmation(tmp_path):
    app = desk(tmp_path)
    item(app.checkbox, 'include counterevidence').uncheck().run()
    item(app.text_input, '研究公司').set_value('公司甲').run()
    source(app, 'capacity.txt', '2026-01-01')
    item(app.checkbox, 'include counterevidence').check().run()
    assert item(app.checkbox, '已核对日期和适用范围 · capacity.txt').value
    assert not item(app.checkbox, '已核对日期和适用范围 · delay.txt').value
    item(app.checkbox, 'replace source bytes').check().run()
    assert item(app.text_input, '披露日期 · capacity.txt').value == ''
    assert not item(app.checkbox, '已核对日期和适用范围 · capacity.txt').value
    confirm_plan(app)
    assert item(app.button, '审查证据／继续').disabled
    assert not app.exception
