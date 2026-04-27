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
    def __init__(self):
        self._load_config()

    def _load_config(self):
        env_path = Path(__file__).resolve().parent.parent.parent / "config" / ".env"
        if not env_path.exists():
            self.api_key = ""
            self.api_url = "http://127.0.0.1:11434/v1/chat/completions"
            self.model = "qwen3.5:2b"
            return
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                k, v = line.split('=', 1)
                v = v.strip().strip('"').strip("'")
                if k == 'XF_API_KEY':
                    self.api_key = v
                elif k == 'XF_API_URL':
                    self.api_url = v
                elif k == 'XF_MODEL':
                    self.model = v

    def generate_text(self, prompt: str) -> str:
        # 简化归档实现：调用原地址
        payload = {"model": getattr(self, 'model', ''), "messages": [{"role": "user", "content": prompt}]}
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
