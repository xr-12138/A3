from __future__ import annotations

from typing import Dict, Any

from src.api.base import BaseAIClient


class TutoringAgent:
    """辅导智能体：根据用户进度提供分步辅导或答疑。"""

    def __init__(self, ai_client: BaseAIClient):
        self.ai = ai_client

    def run(self, question: str) -> Dict[str, Any]:
        text = self.ai.generate_text(question)
        return {"answer": text}
