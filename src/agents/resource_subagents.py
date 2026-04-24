from __future__ import annotations

from typing import Any, Dict, List

from src.api.base import BaseAIClient


class DocumentAgent:
    def __init__(self, ai_client: BaseAIClient):
        self.ai = ai_client

    def run(self, topic: str) -> str:
        prompt = f"请为主题 \"{topic}\" 生成一份教学文档，要点清晰，层次分明。"
        return self.ai.generate_text(prompt)


class MindmapAgent:
    def __init__(self, ai_client: BaseAIClient):
        self.ai = ai_client

    def run(self, topic: str) -> Dict:
        return self.ai.generate_mindmap(topic)


class QuestionBankAgent:
    def __init__(self, ai_client: BaseAIClient):
        self.ai = ai_client

    def run(self, topic: str, num: int = 5) -> List[Dict[str, str]]:
        return self.ai.generate_questions(topic, num)


class CodeAgent:
    def __init__(self, ai_client: BaseAIClient):
        self.ai = ai_client

    def run(self, topic: str, language: str = "python") -> str:
        return self.ai.generate_code(topic, language=language)


class VideoAgent:
    def __init__(self, ai_client: BaseAIClient):
        self.ai = ai_client

    def run(self, topic: str) -> str:
        prompt = f"为主题 \"{topic}\" 写一个视频讲稿，包含分镜与解说要点。"
        return self.ai.generate_text(prompt)
