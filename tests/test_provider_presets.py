"""Provider switches, subscriber guidance and official protocol routes; no live keys."""
import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from src.harness.providers import PRESETS, apply_preset, connection_blocker
from src.harness.api import ModelClient, api_endpoints, USER_AGENT


def test_switch_drops_previous_credential_and_success_but_custom_keeps_explicit_config():
    state = {'api_secret':'synthetic-old','api_secret_widget':'synthetic-old','model_catalog':['old'], 'connection_result':{'status':'connected'}}
    apply_preset(state,'DeepSeek API')
    assert state['api_secret'] == state['api_secret_widget'] == ''
    assert 'model_catalog' not in state and 'connection_result' not in state
    state['api_secret'] = 'synthetic-new'
    before = state.copy()
    apply_preset(state,'自定义')
    assert state == before


def test_nonstandard_api_versions_are_preserved():
    for name in ('智谱 GLM API','百度千帆／文心 API','Gemini API','豆包／火山方舟 API'):
        p = PRESETS[name]
        assert api_endpoints(p.base,p.protocol)['completion'] == p.base+'/chat/completions'
    assert api_endpoints(PRESETS['Claude API'].base,'anthropic')['models'].endswith('/v1/models')


def test_info_only_plan_cannot_trigger_model_test_or_discovery():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'harness_app.py'),default_timeout=25).run()
    app.text_input(key='api_secret_widget').set_value('synthetic-old').run()
    app.selectbox(key='api_preset').select('百炼 Coding Plan（说明）').run()
    assert not app.exception
    assert not app.session_state['api_secret']
    assert all(b.disabled for b in app.button if b.label in {'测试连接','获取模型列表'})
    assert connection_blocker('百炼 Coding Plan（说明）')
    assert not connection_blocker('DeepSeek API')
    app.radio(key='desk_page').set_value('模型与套餐').run()
    app.selectbox(key='provider_guide_choice').select('Claude API').run()
    next(b for b in app.button if b.label=='在侧栏使用这项预设').click().run()
    assert not app.exception and app.session_state['api_preset']=='Claude API'
    assert app.session_state['api_protocol']=='anthropic'


def test_empty_probe_does_not_claim_usable_model_in_sidebar(monkeypatch):
    monkeypatch.setattr(ModelClient,'test_connection',lambda self: {'text_response_received':False,'elapsed_seconds':0,'http_status':200})
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/'harness_app.py'),default_timeout=25).run()
    app.text_input(key='api_secret_widget').set_value('synthetic-key').run()
    app.text_input(key='api_model').set_value('synthetic-model').run()
    next(b for b in app.button if b.label=='测试连接').click().run()
    # The sidebar caption updates at the next rerun, independently of probe diagnostics.
    app.run()
    assert any('接口已响应，但无正文' in c.value for c in app.caption)
    assert not any(c.value=='模型：连接已测试' for c in app.caption)
    assert any('没有生成文本' in w.value for w in app.warning)
    assert not app.exception


@pytest.mark.parametrize('name',['Gemini API','MiniMax API（国际）','MiniMax API（国内）','OpenAI','Claude API'])
def test_requests_use_service_specific_headers_and_token_field(name):
    calls = []
    p = PRESETS[name]
    def opening(request,**kwargs):
        calls.append(request)
        if request.get_method()=='GET':
            return io.BytesIO(json.dumps({'data':[{'id':'text-model'}]}).encode())
        envelope = {'choices':[{'message':{'content':'OK'},'finish_reason':'stop'}]} if p.protocol=='openai' else {'content':[{'type':'text','text':'OK'}],'stop_reason':'end_turn'}
        return io.BytesIO(json.dumps(envelope).encode())
    class Opener:
        open = staticmethod(opening)
    with patch('urllib.request.build_opener',return_value=Opener()):
        client = ModelClient(p.base,'text-model','synthetic-provider-key',protocol=p.protocol)
        assert client.list_models()['models']==['text-model']
        assert client.test_connection()['text_response_received']
    assert len(calls)==2
    headers = {k.lower():v for k,v in calls[-1].header_items()}
    body = json.loads(calls[-1].data)
    if name=='Gemini API':
        assert all(dict((k.lower(),v) for k,v in r.header_items())['x-goog-api-client']==USER_AGENT for r in calls)
    else:
        assert 'x-goog-api-client' not in headers
    if name in {'OpenAI','MiniMax API（国际）','MiniMax API（国内）'}:
        assert body['max_completion_tokens']==2048 and 'max_tokens' not in body
        assert 'thinking' not in body
    else:
        assert body['max_tokens']==256
    if name=='Claude API':
        assert headers['x-api-key']=='synthetic-provider-key' and 'authorization' not in headers
