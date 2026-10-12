"""Widget transitions preserve an in-memory synthetic credential and explicit clear works."""
from pathlib import Path
from streamlit.testing.v1 import AppTest
import pytest
from src.harness.api import ModelClient, APIError


def test_model_secret_survives_workflow_changes_and_clear_removes_both_keys():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'harness_app.py'), default_timeout=25).run()
    app.text_input(key='api_secret_widget').set_value('synthetic_not_real_key').run()
    assert app.session_state['api_secret'] == 'synthetic_not_real_key'
    next(r for r in app.radio if r.label == '研究方向').set_value('量化处理与回测').run()
    assert app.session_state['api_secret'] == 'synthetic_not_real_key'
    next(r for r in app.radio if r.label == '研究方向').set_value('财务／估值研究').run()
    assert app.session_state['api_secret'] == 'synthetic_not_real_key'
    next(b for b in app.button if b.label == '清除本次会话的密钥').click().run()
    assert app.session_state['api_secret'] == '' and app.session_state['api_secret_widget'] == ''
    assert not app.exception


def test_success_body_containing_secret_is_rejected_before_export(monkeypatch):
    client = ModelClient('http://localhost/v1', 'mock', 'synthetic_header_key')
    monkeypatch.setattr(client, '_complete', lambda *a, **kw: {'finish': 'stop', 'content': '{"notes":"synthetic_header_key"}'})
    with pytest.raises(APIError, match='密钥'):
        client.json('test', {})
