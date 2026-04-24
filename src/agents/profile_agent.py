from __future__ import annotations

import json
from typing import Dict, Any

from src.api.base import BaseAIClient


class ProfileAgent:
    """用户画像智能体：调用 `BaseAIClient.generate_text` 返回 JSON 字符串并解析为 dict。"""

    def __init__(self, ai_client: BaseAIClient):
        self.ai = ai_client

    def run(self, prompt: str) -> Dict[str, Any]:
        text = self.ai.generate_text(prompt)
        try:
            data = json.loads(text)
            return data
        except Exception:
            # 返回原始文本封装
            return {"raw": text}
