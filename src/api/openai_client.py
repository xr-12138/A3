from __future__ import annotations

import json
from pathlib import Path  # noqa: F401 (kept for back-compat if other code imported)
import os
from typing import Any, Dict, List

import requests

from .base import BaseAIClient
import re
import sys as _sys

def _p(*a, **kw):
    """Safe print — stderr, ignores broken pipe."""
    try: print(*a, **kw, file=_sys.stderr)
    except: pass


# Error kind tags used to produce deterministic, user-facing messages.
ERR_MISSING_CONFIG = "missing_config"
ERR_CONNECTION = "connection_error"
ERR_AUTH = "auth_error"
ERR_HTTP = "http_error"
ERR_PARSE = "parse_error"
ERR_EMPTY = "empty_response"
ERR_UNKNOWN = "unknown_error"


class OpenAIClient(BaseAIClient):
    """Minimal OpenAI-compatible client used across the project.

    Reads ``OPENAI_API_KEY`` / ``OPENAI_API_URL`` / ``OPENAI_MODEL`` from the
    shell environment first, then falls back to values supplied in ``cfg``
    (typically produced by :func:`src.api.ai_client._load_env`).

    **Guaranteed behaviour**: every public call either returns a useful
    payload from the configured API *or* returns a clear, prefix-marked error
    message such as ``[AI错误: connection_error] ...``. The client never
    silently falls back to hard-coded sample content.
    """

    DEFAULT_URL = "https://api.openai.com/v1/chat/completions"
    DEFAULT_MODEL = "gpt-3.5-turbo"
    ERROR_PREFIX = "[AI错误]"

    def __init__(self, cfg: dict | None = None):
        # ``cfg`` is usually produced by ``src.api.ai_client._load_env()``.
        self._cfg: Dict[str, Any] = dict(cfg or {})
        self.api_url: str = self.DEFAULT_URL
        self.api_key: str = ""
        self.model: str = self.DEFAULT_MODEL
        self._load_config()

    # ---------------------------------------------------------------- config
    def _load_config(self) -> None:
        try:
            self.api_url = (
                os.getenv('OPENAI_API_URL')
                or self._cfg.get('OPENAI_API_URL')
                or self.DEFAULT_URL
            )
            self.api_key = (
                os.getenv('OPENAI_API_KEY')
                or self._cfg.get('OPENAI_API_KEY')
                or ""
            )
            self.model = (
                os.getenv('OPENAI_MODEL')
                or self._cfg.get('OPENAI_MODEL')
                or self.DEFAULT_MODEL
            )

            if os.getenv('OPENAI_API_KEY'):
                source = "env"
            elif self._cfg.get('OPENAI_API_KEY'):
                source = "file (config/.env)"
            else:
                source = "missing"
            _p(
                f"[信息] OpenAIClient 配置: URL={self.api_url}, "
                f"Model={self.model}, KeySource={source}"
            )
        except Exception as exc:  # pragma: no cover - defensive
            _p(f"[错误] 加载 OpenAIClient 配置失败: {exc}")

    # ---------------------------------------------------------------- helpers
    def _is_configured(self) -> bool:
        return bool(self.api_key) and bool(self.api_url)

    @classmethod
    def _format_error(cls, kind: str, detail: str) -> str:
        """Produce a stable, greppable error string for text-mode callers."""
        return f"{cls.ERROR_PREFIX}:{kind} {detail}"

    def _is_error_text(self, value: Any) -> bool:
        return isinstance(value, str) and value.startswith(self.ERROR_PREFIX)

    def _extract_error_kind(self, value: str) -> str:
        """Pull the `<kind>` token out of an ``[AI错误]:<kind> <detail>`` string.
        Falls back to ``unknown_error`` when the prefix cannot be parsed."""
        try:
            after_prefix = value[len(self.ERROR_PREFIX):]
            if after_prefix.startswith(":"):
                rest = after_prefix[1:]
                token = rest.split(" ", 1)[0]
                return token if token else ERR_UNKNOWN
        except Exception:
            pass
        return ERR_UNKNOWN

    def _build_error_dict(self, kind: str, detail: str, topic: str = "") -> Dict[str, Any]:
        """Return a JSON-serializable dict that callers can render instead of
        silently producing sample content when the API call fails."""
        return {
            "_ai_error": True,
            "error_kind": kind,
            "detail": detail,
            "topic": topic,
        }

    def _post(self, payload: Dict[str, Any], timeout: int = 120) -> Dict[str, Any]:
        if not self._is_configured():
            return {
                "error_kind": ERR_MISSING_CONFIG,
                "error": (
                    "缺少 OPENAI_API_KEY 或 OPENAI_API_URL。"
                    "请确认 config/.env 存在并填写正确，然后重试。"
                ),
                "status_code": 0,
            }

        headers: Dict[str, str] = {'Content-Type': 'application/json'}
        headers['Authorization'] = f'Bearer {self.api_key}'

        try:
            resp = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=timeout,
            )
        except requests.exceptions.ConnectionError as exc:
            return {
                "error_kind": ERR_CONNECTION,
                "error": f"无法连接到 API 服务 {self.api_url}: {exc}",
                "status_code": 0,
            }
        except requests.exceptions.Timeout as exc:
            return {
                "error_kind": ERR_CONNECTION,
                "error": f"请求 API 超时 ({timeout}s): {exc}",
                "status_code": 0,
            }
        except requests.exceptions.RequestException as exc:
            return {
                "error_kind": ERR_UNKNOWN,
                "error": f"请求异常: {exc}",
                "status_code": 0,
            }

        if resp.status_code in (401, 403):
            kind = ERR_AUTH
            detail = f"鉴权失败 (HTTP {resp.status_code})，请检查 OPENAI_API_KEY / 模型权限。"
        elif resp.status_code >= 400:
            kind = ERR_HTTP
            detail = f"HTTP {resp.status_code}: {resp.reason}"
        else:
            kind = None
            detail = ""

        if kind is not None:
            try:
                body = resp.json()
                extra = body.get("error") if isinstance(body, dict) else None
            except Exception:
                extra = resp.text[:500]
            if extra:
                detail = f"{detail} | 服务端返回: {extra}"
            return {"error_kind": kind, "error": detail, "status_code": resp.status_code}

        try:
            return resp.json()
        except Exception as exc:
            return {
                "error_kind": ERR_PARSE,
                "error": f"无法解析 API 返回内容: {exc} | 原始文本前200字: {resp.text[:200]!r}",
                "status_code": resp.status_code,
            }

    def _format_response_text(self, result: Dict[str, Any]) -> str:
        """Extract the plain-text answer from an OpenAI-compatible response.

        If the response looks like an error dict (produced by :meth:`_post`)
        we return a prefixed error string instead of producing sample content.
        """
        try:
            if not isinstance(result, dict):
                return self._format_error(
                    ERR_PARSE, f"服务端返回类型异常: {type(result).__name__}"
                )

            if "error" in result:
                kind = result.get("error_kind") or ERR_UNKNOWN
                detail = result.get("error") or "服务端返回错误"
                return self._format_error(kind, str(detail))

            choices = result.get("choices")
            if isinstance(choices, list) and choices:
                first = choices[0]
                if isinstance(first, dict):
                    message = first.get("message")
                    if isinstance(message, dict) and message.get("content"):
                        text = message.get("content", "")
                        if isinstance(text, str) and text.strip():
                            return text
                    if isinstance(first.get("text"), str) and first["text"].strip():
                        return first["text"]

            if isinstance(result.get("text"), str) and result["text"].strip():
                return result["text"]

            return self._format_error(
                ERR_EMPTY,
                f"API 成功返回但内容为空。原始结构: {json.dumps(result, ensure_ascii=False, default=str)[:300]}",
            )
        except Exception as exc:  # pragma: no cover - defensive
            return self._format_error(ERR_PARSE, f"解析响应时异常: {exc}")

    def _extract_json_like(self, text: str) -> str | None:
        """尝试从任意文本中提取可解析的 JSON 块（对象或数组）。

        返回可直接传入 json.loads 的子串，或 None。
        """
        if not isinstance(text, str):
            return None
        s = text.strip()
        # 直接是 JSON 的常见情况
        if s.startswith('{') or s.startswith('['):
            return s

        # 尝试用正则提取最外层的 JSON 对象或数组（贪婪匹配）
        m = re.search(r"(\{.*\}|\[.*\])", text, flags=re.S)
        if m:
            return m.group(1)

        return None

    def generate_text(self, prompt: str, system_msg: str | None = None) -> str:
        default_sys = os.getenv('OPENAI_SYSTEM_MESSAGE') or self._cfg.get('OPENAI_SYSTEM_MESSAGE')
        system_msg_to_use = (
            system_msg
            if system_msg is not None
            else (default_sys if default_sys is not None else "你是一个专业的中文学习助手，始终用中文回答。")
        )
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_msg_to_use},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        result = self._post(payload)
        # _post() always returns a dict — either the API response or a structured
        # error payload — so _format_response_text handles both cases.
        return self._format_response_text(result)

    def generate_mindmap(self, topic: str) -> Dict[str, Any]:
        # JSON schema example using single-quoted string so inner double-quotes stay literal.
        schema = '{"title":"主题名称","children":[{"title":"子节点","note":"简要说明"}]}'
        prompt = (
            f"请为高校课程的知识主题'{topic}'生成一个结构化的思维导图，"
            "只返回严格的 JSON，格式例如: {\"title\":\"...\",\"children\":[{\"title\":\"...\",\"note\":\"...\"},...]}"
        )
        text = self.generate_text(prompt)
        if self._is_error_text(text):
            # Surface the actual network/auth failure instead of falling back to
            # a canned sample mindmap so users understand *why* nothing rendered.
            return self._build_error_dict(self._extract_error_kind(text), text, topic=topic)

        parsed: Any = None
        # 宽容解析：尝试提取 JSON 块，无论文本前后是否包含额外说明
        candidate = None
        if isinstance(text, str):
            candidate = self._extract_json_like(text)
            if candidate is not None:
                # 兼容单引号 JSON 风格的情况，尝试替换为双引号（谨慎处理）
                try:
                    parsed = json.loads(candidate)
                except Exception:
                    # 轻度修正：将单引号包裹的键/字符串替换为双引号后再试一次
                    try:
                        alt = candidate.replace("\"", "\\\"")
                        alt = candidate.replace("'", '"')
                        parsed = json.loads(alt)
                    except Exception:
                        parsed = None
        if parsed is None:
            return self._build_error_dict(
                ERR_PARSE,
                f"API 返回的文本无法解析为 JSON。原始内容前 300 字: {text[:300]!r}",
                topic=topic,
            )
        if not isinstance(parsed, dict):
            return self._build_error_dict(
                ERR_PARSE,
                f"API 返回的 JSON 不是对象: {type(parsed).__name__}",
                topic=topic,
            )
        return parsed

    def generate_code(self, topic: str, language: str = "python") -> str:
        prompt = (
            f"请生成关于'{topic}'的{language}代码示例，代码要完整可运行，包含必要的注释和说明。"
        )
        return self.generate_text(prompt)

    def generate_questions(self, topic: str, num: int = 5) -> List[Dict[str, Any]]:
        prompt = (
            f"请为'{topic}'生成{num}个练习题，只返回严格的 JSON 列表。"
            f"每题使用键 'q'/'a'/'explanation'。"
        )
        text = self.generate_text(prompt)
        if self._is_error_text(text):
            return [self._build_error_dict(self._extract_error_kind(text), text, topic=topic)]
        try:
            parsed = None
            if isinstance(text, str):
                candidate = self._extract_json_like(text)
                if candidate is not None:
                    parsed = json.loads(candidate)
                else:
                    parsed = json.loads(text)
            else:
                parsed = text
        except Exception:
            return [
                self._build_error_dict(
                    ERR_PARSE,
                    f"API 返回的文本无法解析为 JSON。原始内容前 300 字: {text[:300]!r}",
                    topic=topic,
                )
            ]
        if isinstance(parsed, list):
            return parsed
        return [
            self._build_error_dict(
                ERR_PARSE,
                f"API 返回的 JSON 不是列表: {type(parsed).__name__}",
                topic=topic,
            )
        ]

    def generate_reading_material(self, topic: str, num: int = 5) -> List[Dict[str, Any]]:
        prompt = (
            f"请为高校课程主题 '{topic}' 生成 {num} 条拓展阅读推荐，只返回严格的 JSON 列表，"
            "每项使用键 'title'/'type'/'summary'/'difficulty'/'order'/'link'。"
        )
        text = self.generate_text(prompt)
        if self._is_error_text(text):
            return [self._build_error_dict(self._extract_error_kind(text), text, topic=topic)]
        try:
            parsed = None
            if isinstance(text, str):
                candidate = self._extract_json_like(text)
                if candidate is not None:
                    parsed = json.loads(candidate)
                else:
                    parsed = json.loads(text)
            else:
                parsed = text
        except Exception:
            return [
                self._build_error_dict(
                    ERR_PARSE,
                    f"API 返回的文本无法解析为 JSON。原始内容前 300 字: {text[:300]!r}",
                    topic=topic,
                )
            ]
        if isinstance(parsed, list):
            return parsed
        return [
            self._build_error_dict(
                ERR_PARSE,
                f"API 返回的 JSON 不是列表: {type(parsed).__name__}",
                topic=topic,
            )
        ]

    def generate(self, prompt: str, **kwargs) -> str:
        return self.generate_text(prompt)