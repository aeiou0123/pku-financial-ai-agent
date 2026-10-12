"""Explicit model discovery, URL variants, credential boundaries and widget selection."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading

import pytest
from streamlit.testing.v1 import AppTest

from src.harness.api import APIError, ModelClient, api_endpoints

KEY = 'synthetic_catalog_key_123456'


@pytest.mark.parametrize('ending', ['', '/', '/v1', '/v1/', '/v1/chat/completions', '/v1/chat/completions/', '/v1/completions', '/v1/models'])
def test_openai_address_variants_produce_same_generation_and_catalog_routes(ending):
    endpoints = api_endpoints('https://api.openai.com' + ending)
    assert endpoints['completion'] == 'https://api.openai.com/v1/chat/completions'
    assert endpoints['models'] == 'https://api.openai.com/v1/models'


@pytest.mark.parametrize('ending', ['', '/', '/v1', '/v1/', '/v1/messages', '/v1/messages/', '/v1/models'])
def test_anthropic_address_variants_do_not_duplicate_v1(ending):
    endpoints = api_endpoints('https://api.anthropic.com' + ending, 'anthropic')
    assert endpoints['completion'] == 'https://api.anthropic.com/v1/messages'
    assert endpoints['models'] == 'https://api.anthropic.com/v1/models'


def test_custom_proxy_path_is_retained_and_wrong_protocol_is_rejected():
    assert api_endpoints('https://example.org/gateway/api/v2/chat/completions')['models'] == 'https://example.org/gateway/api/v2/models'
    with pytest.raises(ValueError, match='协议不一致'):
        api_endpoints('https://example.org/v1/messages', 'openai')
    with pytest.raises(ValueError, match='协议不一致'):
        api_endpoints('https://example.org/v1/responses')


@pytest.fixture
def catalog_server():
    state = {'requests': [], 'status': 200, 'body': {'data': [{'id': 'text-b'}, {'id': 'text-a'}, {'id': 'text-a'}]}}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_GET(self):
            state['requests'].append({'path': self.path, 'headers': dict(self.headers), 'method': self.command})
            self.send_response(state['status'])
            if state['status'] == 302:
                self.send_header('Location', '/credential-trap')
            self.end_headers()
            self.wfile.write(json.dumps(state['body']).encode())
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}/v1/chat/completions', state
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


@pytest.mark.parametrize('protocol', ['openai', 'anthropic'])
def test_discovery_needs_no_model_and_uses_one_authenticated_get(catalog_server, protocol):
    url, state = catalog_server
    if protocol == 'anthropic':
        url = url.replace('/chat/completions', '/messages')
    client = ModelClient(url, '', KEY, protocol=protocol)
    result = client.list_models()
    assert result['models'] == ['text-a', 'text-b'] and not result['partial']
    assert result['endpoint'].endswith('/v1/models')
    assert client.calls == 1 and not client.usage
    assert len(state['requests']) == 1 and state['requests'][0]['method'] == 'GET'
    headers = {key.lower(): value for key, value in state['requests'][0]['headers'].items()}
    if protocol == 'openai':
        assert headers['authorization'] == 'Bearer ' + KEY
        assert 'x-api-key' not in headers
    else:
        assert headers['x-api-key'] == KEY and headers['anthropic-version'] == '2023-06-01'
        assert 'authorization' not in headers
    with pytest.raises(ValueError, match='模型名称'):
        client.test_connection()
    assert len(state['requests']) == 1


@pytest.mark.parametrize('body', [{'data': []}, {'models': ['invented']}, {'data': [{'id': 123}]}, {'data': [{'id': KEY}]}])
def test_empty_malformed_and_credential_containing_catalogs_are_not_accepted(catalog_server, body):
    url, state = catalog_server
    state['body'] = body
    with pytest.raises(APIError) as exc:
        ModelClient(url, '', KEY).list_models()
    assert KEY not in str(exc.value) and len(state['requests']) == 1


@pytest.mark.parametrize('status', [401, 404, 429, 302])
def test_discovery_errors_do_not_retry_redirect_or_expose_key(catalog_server, status):
    url, state = catalog_server
    state.update(status=status, body={'error': {'message': 'Rejected Bearer ' + KEY}})
    with pytest.raises(APIError) as exc:
        ModelClient(url, '', KEY).list_models()
    assert KEY not in str(exc.value) and exc.value.status_code == status
    assert len(state['requests']) == 1


def test_partial_catalog_is_explicit_instead_of_claiming_all_models(catalog_server):
    url, state = catalog_server
    state['body']['has_more'] = True
    assert ModelClient(url, '', KEY).list_models()['partial']
    assert len(state['requests']) == 1


def test_widget_fetch_selection_manual_override_and_settings_invalidation(monkeypatch):
    calls = []
    def models(client):
        calls.append((client.base_url, client.model))
        return {'models': ['text-a', 'text-b'], 'partial': False, 'endpoint': client.base_url + '/models'}
    monkeypatch.setattr(ModelClient, 'list_models', models)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'harness_app.py'), default_timeout=25).run()
    assert not calls
    app.text_input(key='api_secret_widget').set_value(KEY).run()
    next(button for button in app.button if button.label == '获取模型列表').click().run()
    assert len(calls) == 1 and not calls[0][1]
    app.selectbox(key='api_model_choice').select('text-b').run()
    assert app.text_input(key='api_model').value == 'text-b'
    app.text_input(key='api_model').set_value('manual-special-model').run()
    assert app.session_state['api_model'] == 'manual-special-model'
    assert app.selectbox(key='api_model_choice').value is None
    app.text_input(key='api_base').set_value('https://example.org/custom/v1/').run()
    assert 'model_catalog' not in app.session_state
    assert app.text_input(key='api_model').value == 'manual-special-model'
    assert app.session_state['api_secret'] == KEY and len(calls) == 1
    assert not app.exception


def test_catalog_failure_keeps_manual_model_and_clear_key_removes_catalog(monkeypatch):
    def fail(client):
        raise APIError('HTTP 404')
    monkeypatch.setattr(ModelClient, 'list_models', fail)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'harness_app.py'), default_timeout=25).run()
    app.text_input(key='api_secret_widget').set_value(KEY).run()
    app.text_input(key='api_model').set_value('manual-model').run()
    next(button for button in app.button if button.label == '获取模型列表').click().run()
    assert any('仍可手动填写' in warning.value for warning in app.warning)
    assert app.text_input(key='api_model').value == 'manual-model'
    next(button for button in app.button if button.label == '清除本次会话的密钥').click().run()
    assert app.session_state['api_secret'] == '' and 'model_catalog_error' not in app.session_state
    assert not app.exception
