"""Small OpenAI-compatible JSON adapter. Credentials stay in memory only."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field


class APIError(RuntimeError):
    pass


@dataclass
class ModelClient:
    base_url: str
    model: str
    api_key: str = field(repr=False)
    max_calls: int = 12
    calls: int = 0
    usage: list[dict] = field(default_factory=list)

    def __post_init__(self):
        url = urllib.parse.urlsplit(self.base_url)
        local = url.hostname in {"127.0.0.1", "localhost", "::1"}
        if (url.scheme != "https" and not (url.scheme == "http" and local)) or not url.hostname:
            raise ValueError("API 地址须使用 HTTPS；本机测试可使用 HTTP。")
        if url.username or url.password or url.query or url.fragment:
            raise ValueError("API 地址不得含账号、查询参数或片段。")
        if not self.model.strip() or not self.api_key.strip():
            raise ValueError("请填写模型名称和 API Key。")
        if not 1 <= self.max_calls <= 40:
            raise ValueError("单次任务请求上限须在 1—40 之间。")

    def json(self, system: str, payload: dict) -> dict:
        if self.calls >= self.max_calls:
            raise APIError("本次任务已达到请求上限；已完成批次保留，可继续处理。")
        self.calls += 1
        body = json.dumps({"model": self.model,
                           "messages": [{"role": "system", "content": system},
                                        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
                           "temperature": 0, "max_tokens": 3500}).encode("utf-8")
        request = urllib.request.Request(self.base_url.rstrip("/") + "/chat/completions",
                                         data=body, headers={"Authorization": "Bearer " + self.api_key,
                                                             "Content-Type": "application/json"})
        # Normal certificate verification; no retry after ambiguous paid requests.
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise APIError("模型响应过大。")
            envelope = json.loads(raw)
            choice = envelope["choices"][0]
            if choice.get("finish_reason") == "length":
                raise APIError("模型输出被截断，未采纳本批次。")
            content = choice["message"]["content"].strip()
            if self.api_key in content:
                raise APIError("模型响应包含凭据，已拒绝保存。")
            if content.startswith("```") and content.endswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise APIError("模型必须返回 JSON 对象。")
            usage = envelope.get("usage", {})
            self.usage.append({k: v for k, v in usage.items()
                               if k in {"prompt_tokens", "completion_tokens", "total_tokens"}
                               and isinstance(v, int)})
            return parsed
        except urllib.error.HTTPError as exc:
            raise APIError(f"API 请求失败（HTTP {exc.code}）。已停止，请检查账号、额度或配置。") from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise APIError("API 连接失败或超时；未自动重试，以免重复收费。") from None
        except (KeyError, IndexError, TypeError, AttributeError, ValueError):
            raise APIError("模型响应格式无法解析，本批次未采纳。") from None
