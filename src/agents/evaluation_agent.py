from __future__ import annotations

from typing import Dict, Any

from src.api.base import BaseAIClient


class EvaluationAgent:
    """评估智能体：对资源或学习成果进行质量/掌握度评估。"""

    def __init__(self, ai_client: BaseAIClient):
        self.ai = ai_client

    def run(self, artifact: str) -> Dict[str, Any]:
        prompt = f"请评价以下学习资源或答案的质量：\n{artifact}\n请给出评分（1-5）与改进建议。"
        text = self.ai.generate_text(prompt)
        return {"evaluation": text}
