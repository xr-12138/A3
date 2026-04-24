from __future__ import annotations

from typing import Dict

from src.api.base import BaseAIClient


class PathAgent:
    """路径规划智能体：给出学习路径与步骤。"""

    def __init__(self, ai_client: BaseAIClient):
        self.ai = ai_client

    def run(self, goal: str) -> Dict[str, Any]:
        prompt = f"为学习目标 \"{goal}\" 设计一个分阶段学习路径，包含阶段目标与时间预估。"
        text = self.ai.generate_text(prompt)
        return {"plan_text": text}
