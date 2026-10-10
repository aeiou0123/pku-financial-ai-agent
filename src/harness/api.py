"""OpenAI/Anthropic adapters with safe diagnostics and a connection probe."""
from __future__ import annotations

from .module_stamp import source_stamp
_c2v_loaded_source_hash = source_stamp(__file__)
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

USER_AGENT = "Claim2Value-Harness/0.2"


class APIError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, kind: str = 'service', retryable: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.kind = kind
        self.retryable = retryable


def decode_json_object(content: str) -> dict:
    """Accept one complete object, including fences/prose; never repair facts or truncated JSON."""
    content = re.sub(r'^\s*<think>.*?</think>\s*', '', content, flags=re.S).strip().lstrip('\ufeff')
    if content.startswith('<think>'):
        raise APIError('模型只返回了尚未结束的思考内容，没有可采纳的最终JSON。', kind='json_format', retryable=True)
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate key')
            result[key] = value
        return result
    def bad_constant(value):
        raise ValueError('nonfinite JSON')
    decoder = json.JSONDecoder(object_pairs_hook=unique_pairs, parse_constant=bad_constant)
    try:
        whole = decoder.decode(content)
    except ValueError:
        if content.startswith(('[', '"')):
            raise APIError('返回的JSON不完整或有重复字段；本批次未采纳。', kind='json_format', retryable=True) from None
    else:
        if isinstance(whole, str):
            try:
                whole = decoder.decode(whole)
            except ValueError:
                raise APIError('返回的JSON字符串无法解析。', kind='json_format', retryable=True) from None
        if not isinstance(whole, dict):
            raise APIError('模型必须返回一个JSON对象。', kind='json_format', retryable=True)
        return whole
    objects, position = [], 0
    while True:
        start = content.find('{', position)
        if start < 0:
            break
        try:
            obj, end = decoder.raw_decode(content, start)
        except ValueError:
            raise APIError('模型正文中的JSON无法完整解析。', kind='json_format', retryable=True) from None
        objects.append(obj)
        position = end
    if len(objects) != 1 or not isinstance(objects[0], dict):
        raise APIError('API已响应，但未返回唯一可解析的JSON对象；可在连接设置中使用JSON输出约束。', kind='json_format', retryable=True)
    return objects[0]


def redact(text: str, secret: str) -> str:
    text = text.replace(secret, "[已隐藏]").replace(urllib.parse.quote(secret, safe=""), "[已隐藏]")
    text = re.sub(r"(?i)Bearer\s+\S+", "Bearer [已隐藏]", text)
    text = re.sub(r"\bsk-[A-Za-z0-9_-]+", "[已隐藏]", text)
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)[:900]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward credentials after a redirect.


def normalize_base_url(base_url: str, protocol: str = 'openai') -> str:
    base_url = base_url.strip().rstrip('/')
    url = urllib.parse.urlsplit(base_url)
    local = url.hostname in {'127.0.0.1', 'localhost', '::1'}
    if (url.scheme != 'https' and not (url.scheme == 'http' and local)) or not url.hostname:
        raise ValueError('API 地址须使用 HTTPS；本机测试可使用 HTTP。')
    if url.username or url.password or url.query or url.fragment:
        raise ValueError('API 地址不得含账号、查询参数或片段。')
    if protocol not in {'openai', 'anthropic'}:
        raise ValueError('请选择 OpenAI 或 Anthropic 协议。')
    suffixes = ('/chat/completions', '/completions', '/models') if protocol == 'openai' else ('/messages', '/models')
    for suffix in suffixes:
        if base_url.endswith(suffix):
            base_url = base_url[:-len(suffix)].rstrip('/')
            break
    else:
        if base_url.endswith(('/messages', '/chat/completions', '/completions', '/responses')):
            raise ValueError('请求地址与所选协议不一致，请选择对应协议或填写 Base URL。')
    path = urllib.parse.urlsplit(base_url).path
    if not path or (url.hostname in {'api.kimi.com', 'api.kimi.ai'} and path == '/coding'):
        base_url += '/v1'
    return base_url


def api_endpoints(base_url: str, protocol: str = 'openai') -> dict:
    base = normalize_base_url(base_url, protocol)
    if protocol == 'anthropic' and not base.endswith('/v1'):
        base += '/v1'
    return {'base_url': normalize_base_url(base_url, protocol),
            'completion': base + ('/chat/completions' if protocol == 'openai' else '/messages'),
            'models': base + '/models'}


@dataclass
class ModelClient:
    base_url: str
    model: str
    api_key: str = field(repr=False)
    max_calls: int = 12
    calls: int = 0
    usage: list[dict] = field(default_factory=list)
    protocol: str = "openai"
    max_output_tokens: int = 8192
    request_timeout: int = 240
    max_retries: int = 2
    batch_chars: int = 6000
    json_mode: str = 'auto'
    on_status: object = field(default=None, repr=False)
    diagnostics: list[dict] = field(default_factory=list)
    _json_enabled: bool = field(default=True, init=False, repr=False)

    def __post_init__(self):
        self.base_url = normalize_base_url(self.base_url, self.protocol)
        self.model, self.api_key = self.model.strip(), self.api_key.strip()
        if not self.api_key:
            raise ValueError("请填写 API Key。")
        if any(c in self.api_key for c in "\r\n"):
            raise ValueError("API Key 含换行，请检查复制内容。")
        if self.protocol not in {"openai", "anthropic"}:
            raise ValueError("请选择 OpenAI 或 Anthropic 协议。")
        if not 1 <= self.max_calls <= 40 or not 256 <= self.max_output_tokens <= 32768:
            raise ValueError("请求上限须为 1—40，输出 token 上限须为 256—32768。")
        if not 30 <= self.request_timeout <= 600 or not 0 <= self.max_retries <= 3 or not 1000 <= self.batch_chars <= 16000:
            raise ValueError('研究超时须为30—600秒，重试0—3次，单批原文1000—16000字符。')
        if self.json_mode not in {'auto', 'prompt'}:
            raise ValueError('JSON输出设置无法识别。')

    def _status(self, stage: str, **values):
        event = {'stage': stage, 'calls': self.calls, **values}
        self.diagnostics.append(event)
        if self.on_status:
            self.on_status(event)

    @property
    def is_kimi_code(self) -> bool:
        url = urllib.parse.urlsplit(self.base_url)
        return url.hostname in {"api.kimi.com", "api.kimi.ai"} and url.path.rstrip("/").startswith("/coding")

    @property
    def endpoint(self) -> str:
        return api_endpoints(self.base_url, self.protocol)['completion']

    def list_models(self) -> dict:
        """One explicit GET, with no prompt, model requirement, retries or redirects."""
        if self.calls >= self.max_calls:
            raise APIError('本次操作已达到请求上限。')
        self.calls += 1
        endpoint = api_endpoints(self.base_url, self.protocol)['models']
        headers = {'Accept': 'application/json', 'User-Agent': USER_AGENT}
        if self.protocol == 'openai':
            headers['Authorization'] = 'Bearer ' + self.api_key
        else:
            headers.update({'x-api-key': self.api_key, 'anthropic-version': '2023-06-01'})
        request = urllib.request.Request(endpoint, headers=headers, method='GET')
        started = time.monotonic()
        try:
            with urllib.request.build_opener(NoRedirect()).open(request, timeout=30) as response:
                raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise APIError('模型列表响应过大，请手动填写模型名称。')
            envelope = json.loads(raw)
            if not isinstance(envelope, dict) or not isinstance(envelope.get('data'), list):
                raise APIError('服务未返回标准模型列表，请手动填写模型名称。')
            models, seen = [], set()
            for row in envelope['data']:
                if not isinstance(row, dict) or not isinstance(row.get('id'), str):
                    raise APIError('模型列表格式无法解析，请手动填写模型名称。')
                name = row['id'].strip()
                if self.api_key in name:
                    raise APIError('模型列表包含凭据，已拒绝显示。')
                if not name or len(name) > 300 or any(ord(c) < 32 or ord(c) == 127 for c in name):
                    raise APIError('模型列表包含无效名称，请手动填写模型名称。')
                if name not in seen:
                    models.append(name)
                    seen.add(name)
            if not models:
                raise APIError('服务返回空模型列表，请手动填写模型名称。')
            return {'models': sorted(models)[:1000], 'endpoint': endpoint,
                    'partial': bool(envelope.get('has_more')) or len(models) > 1000,
                    'elapsed_seconds': round(time.monotonic() - started, 2)}
        except urllib.error.HTTPError as exc:
            raise self._http_error(exc) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise APIError('获取模型列表失败或超时；未自动重试。仍可手动填写模型名称。') from None
        except (ValueError, TypeError, AttributeError):
            raise APIError('模型列表响应格式无法解析，请手动填写模型名称。') from None

    def _http_error(self, exc: urllib.error.HTTPError) -> APIError:
        detail = ""
        error_code = ''
        try:
            data = json.loads(exc.read(16384))
            error = data.get("error", data)
            detail = error.get("message", "") if isinstance(error, dict) else error if isinstance(error, str) else ""
            if isinstance(error, dict):
                error_code = str(error.get('code', '')) + ' ' + str(error.get('type', ''))
            if not isinstance(detail, str):
                detail = ""
        except (ValueError, OSError, AttributeError):
            pass
        detail = redact(detail, self.api_key)
        hint = {400: "请核对协议、模型 ID 和请求参数。", 401: "请核对密钥、模型 ID 和订阅权限。",
                402: "请检查订阅状态。", 403: "请查看额度或客户端使用权限。", 404: "请核对 Base URL、协议和模型 ID。",
                429: "请检查限额或稍后手动重试。"}.get(exc.code, "请检查服务商状态或配置。")
        if 300 <= exc.code < 400:
            hint = "地址发生重定向，未继续发送密钥；请填写最终服务地址。"
        message = f"API 请求失败（HTTP {exc.code}）。{hint}"
        if detail:
            message += " 服务端说明：" + detail
        if "coding agents" in detail.lower() or "user-agent" in detail.lower():
            message += " 当前客户端为 Claim2Value-Harness；如订阅拒绝此客户端，请使用服务商允许的接入方式。"
        diagnostic = (detail + ' ' + error_code).lower()
        quota = 'quota' in error_code.lower() or any(word in diagnostic for word in ('insufficient_quota', 'quota exceeded', 'exceeded your quota', '余额', '额度已', 'daily quota'))
        context_limit = exc.code in {400, 413} and any(word in diagnostic for word in ('context length', 'context window', 'maximum context', 'prompt too long', '上下文', '输入过长'))
        unsupported_json = exc.code in {400, 422} and 'response_format' in diagnostic and any(word in diagnostic for word in ('not support', 'unsupported', 'unknown', 'unrecognized', 'not allowed', 'not permitted', 'unexpected', '不支持'))
        kind = 'context_limit' if context_limit else 'json_unsupported' if unsupported_json else 'quota' if quota else 'auth' if exc.code in {401, 402, 403} else 'service'
        return APIError(message, status_code=exc.code, kind=kind,
                        retryable=not quota and exc.code in {408, 429, 500, 502, 503, 504})

    def _complete(self, system: str, prompt: str, *, limit: int, timeout: int, probe: bool = False) -> dict:
        if not self.model:
            raise ValueError('请先选择或填写模型名称。')
        if self.calls >= self.max_calls:
            raise APIError("本轮请求预算已达到上限；已完成批次保留，下次继续只处理未完成批次。", kind='budget')
        self.calls += 1
        payload = {"model": self.model, "max_tokens": limit, "stream": False}
        headers = {"Content-Type": "application/json", "User-Agent": USER_AGENT}
        if self.protocol == "openai":
            payload["messages"] = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
            headers["Authorization"] = "Bearer " + self.api_key
            if not probe and self.json_mode == 'auto' and self._json_enabled:
                payload['response_format'] = {'type': 'json_object'}
        else:
            payload["system"] = system
            payload["messages"] = [{"role": "user", "content": prompt}]
            headers.update({"x-api-key": self.api_key, "anthropic-version": "2023-06-01"})
        # Omit temperature/top_p; provider models enforce different sampling rules.
        if probe and self.is_kimi_code:
            payload["thinking"] = {"type": "disabled"}
        request = urllib.request.Request(self.endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers)
        started = time.monotonic()
        try:
            with urllib.request.build_opener(NoRedirect()).open(request, timeout=timeout) as response:
                raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise APIError("模型响应过大。")
            envelope = json.loads(raw)
            if self.protocol == "openai":
                choice = envelope["choices"][0]
                content = choice["message"].get("content") or ""
                finish = choice.get("finish_reason", "")
                if isinstance(content, dict):
                    content = json.dumps(content, ensure_ascii=False, allow_nan=False)
                elif isinstance(content, list):
                    content = "".join(part["text"] for part in content if part.get("type") == "text")
            else:
                content = "".join(part["text"] for part in envelope["content"] if part.get("type") == "text")
                finish = envelope.get("stop_reason", "")
            if not isinstance(content, str):
                raise APIError("模型未返回文本。")
            if self.api_key in content:
                raise APIError("模型响应包含凭据，已拒绝保存。", kind='credentials')
            safe_usage = {k: v for k, v in envelope.get("usage", {}).items()
                          if k in {"prompt_tokens", "completion_tokens", "total_tokens", "input_tokens", "output_tokens"} and type(v) is int}
            self.usage.append(safe_usage)
            return {"content": content.strip(), "finish": finish, "usage": safe_usage,
                    "elapsed_seconds": round(time.monotonic() - started, 2)}
        except urllib.error.HTTPError as exc:
            raise self._http_error(exc) from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            timed_out = isinstance(exc, TimeoutError) or isinstance(getattr(exc, 'reason', None), TimeoutError)
            raise APIError(f"本次请求{'等待超过' + str(timeout) + '秒' if timed_out else '连接中断'}；连接测试成功不保证长研究请求成功。",
                           kind='timeout' if timed_out else 'network', retryable=True) from None
        except (KeyError, IndexError, TypeError, AttributeError, ValueError):
            raise APIError("模型响应格式无法解析，请核对协议；本次结果未采纳。") from None

    def json(self, system: str, payload: dict) -> dict:
        prompt = json.dumps(payload, ensure_ascii=False)
        if self.api_key and self.api_key in prompt:
            raise APIError('研究输入包含本次API密钥，请移除后继续。', kind='credentials')
        for attempt in range(1, self.max_retries + 2):
            self._status('request_started', attempt=attempt, timeout_seconds=self.request_timeout)
            started = time.monotonic()
            try:
                result = self._complete(system + '\nReturn exactly one complete JSON object. No prose, markdown or thinking text.',
                                        prompt, limit=self.max_output_tokens, timeout=self.request_timeout)
                if result['finish'] in {'length', 'max_tokens'}:
                    raise APIError('模型输出达到 token 上限，未采纳本批次。请增加输出上限或减少单批原文；不会重复请求同一截断输出。', kind='output_limit')
                content = result['content']
                if self.api_key and self.api_key in content:
                    raise APIError('模型响应意外包含本次密钥，未采纳或写入成果。', kind='credentials')
                if not content:
                    raise APIError('API已响应但没有最终正文；思考内容不作为证据。请提高输出上限或调整模型设置。', kind='empty_response', retryable=True)
                parsed = decode_json_object(content)
                self._status('request_completed', attempt=attempt, elapsed_seconds=round(time.monotonic() - started, 2))
                return parsed
            except APIError as exc:
                self._status('request_failed', attempt=attempt, kind=exc.kind, elapsed_seconds=round(time.monotonic() - started, 2))
                compatible_fallback = exc.kind == 'json_unsupported' and self.json_mode == 'auto' and self._json_enabled
                if compatible_fallback:
                    self._json_enabled = False
                if not (exc.retryable or compatible_fallback) or attempt > self.max_retries or self.calls >= self.max_calls:
                    raise
                delay = 0 if compatible_fallback else min(2 ** (attempt - 1), 4)
                self._status('retry_wait', attempt=attempt + 1, delay_seconds=delay, kind=exc.kind)
                if delay:
                    time.sleep(delay)

    def test_connection(self) -> dict:
        result = self._complete("This is a connection test. Reply only OK. Do not use tools.", "Reply OK.",
                                limit=256, timeout=30, probe=True)
        return {"status": "connected", "http_status": 200, "endpoint": self.endpoint, "model": self.model,
                "protocol": self.protocol, "elapsed_seconds": result["elapsed_seconds"], "usage": result["usage"],
                "text_response_received": bool(result["content"]), "finish_reason": result["finish"],
                "response_preview": redact(result["content"], self.api_key)[:160]}
