from __future__ import annotations

import json
from typing import Dict, Any

from src.api.base import BaseAIClient


class ProfileAgent:
    """用户画像智能体：调用 `BaseAIClient.generate_text` 返回 JSON 字符串并解析为 dict。"""

    def __init__(self, ai_client: BaseAIClient):
        self.ai = ai_client

    def run(self, prompt: str) -> Dict[str, Any]:
        # 构造严格的指令，要求返回中文且仅返回 JSON 格式的画像。
        instruction = (
            "请根据以下学生信息生成一个结构化的学习画像（JSON 格式），" \
            "必须使用中文输出且仅返回 JSON 对象，不要添加多余说明或解释。\n" \
            "要求字段（至少6个维度）：\n" \
            "- 专业: 专业（字符串）\n" \
            "- 知识水平: 知识水平（例如：基础薄弱/中等/基础扎实）\n" \
            "- 认知风格: 认知风格（例如：视觉/听觉/动手型等）\n" \
            "- 薄弱环节: 易错点或薄弱环节（字符串列表）\n" \
            "- 学习目标: 学习目标（字符串列表）\n" \
            "- 学习建议: 针对性的学习建议（字符串列表）\n" \
            "可选字段：兴趣（兴趣）、偏好资源类型（偏好资源类型）、估计水平分数（估计水平分数）等。\n" \
            "输入文本：\n" + prompt
        )
        text = self.ai.generate_text(instruction)
        try:
            data = json.loads(text)
            return data
        except Exception:
            # 返回原始文本封装
            return {"raw": text}