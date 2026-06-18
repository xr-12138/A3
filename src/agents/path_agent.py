from __future__ import annotations

from typing import Dict

from src.api.base import BaseAIClient
from src.core.knowledge_base import get_knowledge_base


class PathAgent:
    """路径规划智能体：给出学习路径与步骤。"""

    def __init__(self, ai_client: BaseAIClient):
        self.ai = ai_client

    def run(self, goal: str) -> Dict[str, Any]:
        # 引入课程知识库章节信息，使学习路径更贴合课程结构
        course_hint = ""
        try:
            kb = get_knowledge_base()
            manifest = kb.manifest
            course_name = manifest.get("course_name", "数据结构")
            chapters = manifest.get("chapters", [])
            if chapters:
                ch_list = ", ".join([f"{ch.get('id', '')}·{ch.get('title', '')}" for ch in chapters[:6]])
                course_hint = f"\n\n当前系统已载入课程「{course_name}」的完整知识库，该课程包含以下章节：{ch_list}。请结合上述课程体系为学生设计学习路径。"
        except Exception:
            pass

        prompt = f"为学习目标 \"{goal}\" 设计一个分阶段学习路径，包含阶段目标与时间预估。{course_hint}"
        text = self.ai.generate_text(prompt)
        return {"plan_text": text}