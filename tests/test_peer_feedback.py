"""Long reports, interrupted requests, partial evidence and human input boundaries."""
import io
import json
from pathlib import Path
from types import SimpleNamespace
import urllib.error

import pytest

from src.harness.api import APIError, ModelClient, decode_json_object
from src.harness.documents import parse, chunks
from src.harness.financial import extract, parse_forecasts
from src.harness.research import local_plan, validate_plan
from src.harness.store import Run

KEY = 'synthetic_peer_feedback_credential_123'


@pytest.mark.parametrize('text', ['{"records": []}', '```json\n{"records": []}\n```',
    '结果如下：\n```json\n{"records": []}\n```\n请核对。', '{"records": []}\n请核对。',
    '<think>do not adopt {"fake": 1}</think>\n{"records": []}', '"{\\"records\\": []}"'])
def test_wrappers_preserve_the_single_complete_object(text):
    assert decode_json_object(text) == {'records': []}


@pytest.mark.parametrize('text', ['{"records": [{"x":1}', '说明 {"x":1} 再说明 {"x":2}',
    '[{"records":[]}]', '{"x": 1, "x": 2}', '{"x":NaN}', '<think>{"fake": 1}', 'OK'])
def test_ambiguous_truncated_duplicate_or_thinking_only_output_is_rejected(text):
    with pytest.raises(APIError):
        decode_json_object(text)


def envelope(content='{"records":[]}'):
    return json.dumps({'choices': [{'finish_reason': 'stop', 'message': {'content': content}}]})


def http_error(status, message, code=''):
    return urllib.error.HTTPError('https://example.org/v1', status, '', {},
        io.BytesIO(json.dumps({'error': {'message': message, 'code': code}}).encode()))


@pytest.fixture
def mocked_http(monkeypatch):
    calls, responses = [], []
    class Response(io.BytesIO):
        pass
    class Opener:
        def open(self, request, timeout):
            calls.append({'timeout': timeout, 'payload': json.loads(request.data)})
            response = responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return Response(response.encode())
    monkeypatch.setattr('urllib.request.build_opener', lambda *args: Opener())
    monkeypatch.setattr('src.harness.api.time.sleep', lambda _: None)
    return calls, responses


def test_transient_timeout_retries_with_configured_timeout_and_budget(mocked_http):
    calls, responses = mocked_http
    responses.extend([TimeoutError(), envelope()])
    client = ModelClient('https://example.org/v1', 'model', KEY, request_timeout=330)
    assert client.json('schema', {}) == {'records': []}
    assert [call['timeout'] for call in calls] == [330, 330] and client.calls == 2
    assert any(event['stage'] == 'retry_wait' for event in client.diagnostics)
    assert KEY not in json.dumps(client.diagnostics)


def test_retry_limit_can_be_disabled_and_retries_never_exceed_call_budget(mocked_http):
    calls, responses = mocked_http
    responses.append(TimeoutError())
    with pytest.raises(APIError):
        ModelClient('https://example.org/v1', 'model', KEY, max_retries=0).json('schema', {})
    assert len(calls) == 1
    responses.append(TimeoutError())
    with pytest.raises(APIError):
        ModelClient('https://example.org/v1', 'model', KEY, max_calls=1).json('schema', {})
    assert len(calls) == 2


@pytest.mark.parametrize('status,message,code', [(401, 'bad key', ''), (403, 'not permitted', ''),
    (429, 'daily quota reached', 'token_quota_exceeded'), (400, 'maximum context length', '')])
def test_auth_quota_and_context_errors_are_not_blindly_retried(mocked_http, status, message, code):
    calls, responses = mocked_http
    responses.append(http_error(status, message, code))
    with pytest.raises(APIError):
        ModelClient('https://example.org/v1', 'model', KEY).json('schema', {})
    assert len(calls) == 1


def test_unsupported_json_constraint_falls_back_once_without_changing_schema(mocked_http):
    calls, responses = mocked_http
    responses.extend([http_error(400, 'response_format is unsupported'), envelope('说明：```json\n{"records":[]}\n```')])
    client = ModelClient('https://example.org/v1', 'model', KEY)
    assert client.json('schema', {}) == {'records': []}
    assert calls[0]['payload']['response_format'] == {'type': 'json_object'}
    assert 'response_format' not in calls[1]['payload'] and client.calls == 2
    assert 'schema' in calls[1]['payload']['messages'][0]['content']


def test_model_format_failure_gets_bounded_second_attempt(mocked_http):
    calls, responses = mocked_http
    responses.extend([envelope('OK'), envelope()])
    client = ModelClient('https://example.org/v1', 'model', KEY)
    assert client.json('schema', {}) == {'records': []} and len(calls) == 2


def test_long_report_tail_is_parsed_and_every_character_is_in_a_bounded_batch():
    raw = ('财务材料\n' * 40000 + '尾部关键证据：收入100元。').encode()
    doc = parse(raw, 'long_report.txt')
    assert doc['characters'] > 120000 and doc['coverage'] == 'parsed_text'
    assert '尾部关键证据' in doc['parts'][-1]['text']
    batches = chunks([doc], limit=3000)
    assert all(sum(len(piece['text']) for piece in batch) <= 3000 for batch in batches)
    assert sum(len(piece['text']) for batch in batches for piece in batch) == doc['characters']


def fake_client(responder, batch_chars=1000):
    client = SimpleNamespace(api_key=KEY, model='mock', base_url='http://localhost/v1', protocol='openai',
                             max_output_tokens=8192, calls=0, usage=[], batch_chars=batch_chars)
    def call(system, payload):
        client.calls += 1
        return responder(payload)
    client.json = call
    return client


def one_record(piece):
    return {'source_file': piece['source_file'], 'source_locator': piece['source_locator'],
            'quote': piece['text'][:30], 'value_original': '100'}


def test_failed_middle_batch_does_not_discard_tail_and_resume_only_requests_hole(tmp_path):
    raw = ('A' * 1000 + '\n' + 'B' * 1000 + '\n' + 'C' * 1000).encode()
    doc = parse(raw, 'three.txt')
    run = Run(tmp_path, 'financial', [('three.txt', raw)])
    def first(payload):
        piece = payload['pieces'][0]
        if piece['source_locator'] == 'line:2':
            raise APIError('temporary failure', kind='timeout')
        return {'records': [one_record(piece)]}
    client = fake_client(first)
    records = extract(run, [doc], 'revenue', client)
    report = json.loads((run.path/'outputs/extraction_progress.json').read_text(encoding='utf-8'))
    assert len(records) == 2 and client.calls == 3 and not report['complete']
    assert [row['status'] for row in report['batches']] == ['completed', 'failed', 'completed']
    assert run.metadata['status'] == 'extraction_partial'
    def denied(payload):
        raise APIError('quota reached', kind='quota')
    with pytest.raises(APIError):
        extract(run, [doc], 'revenue', fake_client(denied))
    preserved = json.loads((run.path/'outputs/candidates.json').read_text(encoding='utf-8'))
    assert len(preserved) == 2
    report = json.loads((run.path/'outputs/extraction_progress.json').read_text(encoding='utf-8'))
    assert [row['status'] for row in report['batches']] == ['cached', 'failed', 'cached']
    resumed = fake_client(lambda payload: {'records': [one_record(payload['pieces'][0])]})
    records = extract(run, [doc], 'revenue', resumed)
    assert len(records) == 3 and resumed.calls == 1
    assert json.loads((run.path/'outputs/extraction_progress.json').read_text(encoding='utf-8'))['complete']


def test_context_limit_splits_exact_pieces_without_inventing_offsets_and_cache_reuses_result(tmp_path):
    raw = ('A' * 2000).encode()
    doc = parse(raw, 'split.txt')
    run = Run(tmp_path, 'financial', [('split.txt', raw)])
    def responder(payload):
        piece = payload['pieces'][0]
        if len(piece['text']) > 1000:
            raise APIError('context limit', kind='context_limit')
        return {'records': [one_record(piece)]}
    client = fake_client(responder, batch_chars=2000)
    records = extract(run, [doc], 'revenue', client)
    assert records and client.calls == 3
    cached = fake_client(lambda payload: pytest.fail('must use cache'), batch_chars=2000)
    assert extract(run, [doc], 'revenue', cached) == records and cached.calls == 0


@pytest.mark.parametrize('text', ['', '1,2', '1,,3,4,5', '1,2,3,4,abc', '1,2,3,4,NaN'])
def test_dcf_missing_invalid_or_nonfinite_input_is_explained_in_chinese(text):
    with pytest.raises(ValueError) as exc:
        parse_forecasts(text)
    assert 'could not convert' not in str(exc.value)


def test_chinese_comma_dcf_inputs_and_optional_net_debt_are_preserved():
    assert parse_forecasts('1，2，3，4，5') == ([1., 2., 3., 4., 5.], None)
    assert parse_forecasts('1,2,3,4,5', '-10') == ([1., 2., 3., 4., 5.], -10.)


def test_local_template_matches_product_research_without_claiming_model_planning():
    plan = validate_plan(local_plan('耳机路线的问题', '音响'))
    assert '音响' in plan['conditions'][0]['query_terms'] and '未调用模型' in plan['notes']
    assert plan['conditions'][0]['type'] == 'technical'
    assert local_plan('扩产能否支持增长', '减速器')['conditions'][0]['type'] == 'capacity'
