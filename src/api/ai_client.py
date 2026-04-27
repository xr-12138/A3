from __future__ import annotations

from pathlib import Path
import os

from .ollama_client import OllamaClient


def _load_env():
    env_path = Path(__file__).resolve().parent.parent / "config" / ".env"
    cfg = {}
    if not env_path.exists():
        return cfg
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            cfg[k] = v.strip().strip('"').strip("'")
    return cfg


def get_ai_client():
    """返回项目中使用的 AI 客户端实例。根据 `config/.env` 的 `AI_BACKEND` 或 `XF_API_URL` 决定。

    目前默认返回 `OllamaClient`。如需切换，设置环境变量 `AI_BACKEND=xfyun`（兼容性模式）。
    """
    cfg = _load_env()
    backend = os.environ.get('AI_BACKEND') or cfg.get('AI_BACKEND') or ''
    backend = backend.lower()

    if backend == 'xfyun':
        # 兼容模式：如果你确实需要使用旧的讯飞实现，可以在这里导入
        try:
            from .xfyun_api import XFYunClient
            return XFYunClient()
        except Exception:
            # 回退到 Ollama
            return OllamaClient()

    # 默认：Ollama 本地部署
    return OllamaClient()
