from __future__ import annotations

import os
import json
import time
import requests
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..base import BaseAIClient


class XFYunClient(BaseAIClient):
    """归档：讯飞星火大模型客户端实现（HTTP服务接口版本）"""
    # 原始实现已归档到此处以便回溯
    def __init__(self, cfg: dict | None = None):
        # 支持注入 cfg（来自统一的配置加载器），优先使用环境变量
        self._cfg = cfg or {}
        self._load_config()

    def _load_config(self):
        env_path = Path(__file__).resolve().parent.parent.parent / "config" / ".env"
        # 优先读取环境变量，再读取注入的 cfg，最后回退到默认/文件（若 cfg 来自文件则已包含）
        self.api_key = os.getenv('XF_API_KEY') or self._cfg.get('XF_API_KEY', '')
        self.api_url = os.getenv('XF_API_URL') or self._cfg.get('XF_API_URL', 'http://127.0.0.1:11434/v1/chat/completions')
        self.model = os.getenv('XF_MODEL') or self._cfg.get('XF_MODEL', 'qwen3.5:2b')
        # 若未通过 env 或 cfg 获取到值且文件存在，可从文件读取（向后兼容）
        if env_path.exists() and not (os.getenv('XF_API_KEY') or self._cfg.get('XF_API_KEY')):
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    k, v = line.split('=', 1)
                    v = v.strip().strip('"').strip("'")
                    if k == 'XF_API_KEY':
                        self.api_key = v
                    elif k == 'XF_API_URL':
                        self.api_url = v
                    elif k == 'XF_MODEL':
                        self.model = v

    def generate_text(self, prompt: str, system_msg: str | None = None) -> str:
        # 简化归档实现：调用原地址；若传入 system_msg，则在 messages 中包含它
        messages = []
        if system_msg:
            messages.append({"role": "system", "content": system_msg})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": getattr(self, 'model', ''), "messages": messages}
        try:
            r = requests.post(getattr(self, 'api_url', ''), json=payload, timeout=60)
            if r.status_code == 200:
                try:
                    return r.json().get('choices', [])[0].get('message', {}).get('content', '')
                except Exception:
                    return r.text
            return f"HTTP {r.status_code}: {r.text}"
        except Exception as e:
            return f"异常: {e}"
