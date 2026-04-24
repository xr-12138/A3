from __future__ import annotations

from typing import Any, Dict

from src.api.base import BaseAIClient

from .resource_subagents import (
    DocumentAgent,
    MindmapAgent,
    QuestionBankAgent,
    CodeAgent,
    VideoAgent,
)


class ResourceAgent:
    """资源生成总控，拆分为多个子智能体。"""

    def __init__(self, ai_client: BaseAIClient):
        self.doc = DocumentAgent(ai_client)
        self.mind = MindmapAgent(ai_client)
        self.qbank = QuestionBankAgent(ai_client)
        self.code = CodeAgent(ai_client)
        self.video = VideoAgent(ai_client)

    def run(self, topic: str) -> Dict[str, Any]:
        return {
            "document": self.doc.run(topic),
            "mindmap": self.mind.run(topic),
            "question_bank": self.qbank.run(topic),
            "code": self.code.run(topic),
            "video_script": self.video.run(topic),
        }
