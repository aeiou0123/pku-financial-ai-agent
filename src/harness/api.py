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
    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def redact(text: str, secret: str) -> str:
    text = text.replace(secret, "[已隐藏]").replace(urllib.parse.quote(secret, safe=""), "[已隐藏]")
    text = re.sub(r"(?i)Bearer\s+\S+", "Bearer [已隐藏]", text)
    text = re.sub(r"\bsk-[A-Za-z0-9_-]+", "[已隐藏]", text)
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)[:900]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward credentials after a redirect.


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

    def __post_init__(self):
        self.base_url, self.model, self.api_key = self.base_url.strip().rstrip("/"), self.model.strip(), self.api_key.strip()
        url = urllib.parse.urlsplit(self.base_url)
        local = url.hostname in {"127.0.0.1", "localhost", "::1"}
        if (url.scheme != "https" and not (url.scheme == "http" and local)) or not url.hostname:
            raise ValueError("API 地址须使用 HTTPS；本机测试可使用 HTTP。")
        if url.username or url.password or url.query or url.fragment:
            raise ValueError("API 地址不得含账号、查询参数或片段。")
        if not self.model or not self.api_key:
            raise ValueError("请填写模型名称和 API Key。")
        if any(c in self.api_key for c in "\r\n"):
            raise ValueError("API Key 含换行，请检查复制内容。")
        if self.protocol not in {"openai", "anthropic"}:
            raise ValueError("请选择 OpenAI 或 Anthropic 协议。")
        if not 1 <= self.max_calls <= 40 or not 256 <= self.max_output_tokens <= 32768:
            raise ValueError("请求上限须为 1—40，输出 token 上限须为 256—32768。")
        suffix = "/chat/completions" if self.protocol == "openai" else "/messages"
        if self.base_url.endswith(suffix):
            self.base_url = self.base_url[:-len(suffix)]
        elif self.base_url.endswith(("/messages", "/chat/completions", "/responses")):
            raise ValueError("请求地址与所选协议不一致，请选择对应协议或填写 Base URL。")
        if self.is_kimi_code and self.base_url.endswith("/coding"):
            self.base_url += "/v1"

    @property
    def is_kimi_code(self) -> bool:
        url = urllib.parse.urlsplit(self.base_url)
        return url.hostname in {"api.kimi.com", "api.kimi.ai"} and url.path.rstrip("/").startswith("/coding")

    @property
    def endpoint(self) -> str:
        if self.protocol == "openai":
            return self.base_url + "/chat/completions"
        return self.base_url + ("/messages" if self.base_url.endswith("/v1") else "/v1/messages")

    def _http_error(self, exc: urllib.error.HTTPError) -> APIError:
        detail = ""
        try:
            data = json.loads(exc.read(16384))
            error = data.get("error", data)
            detail = error.get("message", "") if isinstance(error, dict) else error if isinstance(error, str) else ""
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
        return APIError(message, status_code=exc.code)

    def _complete(self, system: str, prompt: str, *, limit: int, timeout: int, probe: bool = False) -> dict:
        if self.calls >= self.max_calls:
            raise APIError("本次任务已达到请求上限；已完成批次保留，可继续处理。")
        self.calls += 1
        payload = {"model": self.model, "max_tokens": limit, "stream": False}
        headers = {"Content-Type": "application/json", "User-Agent": USER_AGENT}
        if self.protocol == "openai":
            payload["messages"] = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
            headers["Authorization"] = "Bearer " + self.api_key
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
                if isinstance(content, list):
                    content = "".join(part["text"] for part in content if part.get("type") == "text")
            else:
                content = "".join(part["text"] for part in envelope["content"] if part.get("type") == "text")
                finish = envelope.get("stop_reason", "")
            if not isinstance(content, str):
                raise APIError("模型未返回文本。")
            if self.api_key in content:
                raise APIError("模型响应包含凭据，已拒绝保存。")
            safe_usage = {k: v for k, v in envelope.get("usage", {}).items()
                          if k in {"prompt_tokens", "completion_tokens", "total_tokens", "input_tokens", "output_tokens"} and type(v) is int}
            self.usage.append(safe_usage)
            return {"content": content.strip(), "finish": finish, "usage": safe_usage,
                    "elapsed_seconds": round(time.monotonic() - started, 2)}
        except urllib.error.HTTPError as exc:
            raise self._http_error(exc) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise APIError("API 连接失败或超时；未自动重试，以免重复收费。请检查网络、代理和地址。") from None
        except (KeyError, IndexError, TypeError, AttributeError, ValueError):
            raise APIError("模型响应格式无法解析，请核对协议；本次结果未采纳。") from None

    def json(self, system: str, payload: dict) -> dict:
        result = self._complete(system, json.dumps(payload, ensure_ascii=False), limit=self.max_output_tokens, timeout=90)
        if result["finish"] in {"length", "max_tokens"}:
            raise APIError("模型输出达到 token 上限，未采纳本批次。请增加输出上限或减少单批内容。")
        content = result["content"]
        if self.api_key and self.api_key in content:
            raise APIError('模型响应意外包含本次密钥，未采纳或写入成果。')
        if not content:
            raise APIError("API 已响应，但模型未返回文本；请检查模型思考设置和输出 token 上限。")
        fence = chr(96) * 3
        if content.startswith(fence) and content.endswith(fence):
            content = content.split("\n", 1)[1].rsplit(fence, 1)[0]
        try:
            parsed = json.loads(content)
        except ValueError:
            raise APIError("API 已响应，但模型未返回合法 JSON；本批次未采纳。") from None
        if not isinstance(parsed, dict):
            raise APIError("模型必须返回 JSON 对象。")
        return parsed

    def test_connection(self) -> dict:
        result = self._complete("This is a connection test. Reply only OK. Do not use tools.", "Reply OK.",
                                limit=256, timeout=30, probe=True)
        return {"status": "connected", "http_status": 200, "endpoint": self.endpoint, "model": self.model,
                "protocol": self.protocol, "elapsed_seconds": result["elapsed_seconds"], "usage": result["usage"],
                "text_response_received": bool(result["content"]), "finish_reason": result["finish"],
                "response_preview": redact(result["content"], self.api_key)[:160]}
