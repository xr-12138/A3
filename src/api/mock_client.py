from __future__ import annotations

import json
import asyncio
from typing import Dict, List, Any, Optional

from .base import BaseAIClient


class MockClient(BaseAIClient):
    """用于演示的 MockClient，实现统一接口，并兼容旧的 `generate` / `async_generate` 调用。

    这样既满足新的接口定义，也能被 `ResourceGenerator` 等旧组件重用。
    """

    def generate_text(self, prompt: str) -> str:
        # 简单规则：如果看起来是用户画像输入，返回 JSON 描述；否则返回回答文本
        low = prompt.lower()
        if any(k in low for k in ("学生", "我是一名", "专业", "学习")) and len(prompt) < 200:
            profile = {
                "knowledge_base": "中等",
                "cognitive_style": "视觉 + 阅读",
                "weak_points": "概率论、线性代数",
                "learning_goal": "掌握机器学习基础并能实现模型",
                "study_time": "每天 1 小时",
                "resource_pref": "示例代码 + 视频讲解",
            }
            return json.dumps(profile, ensure_ascii=False)

        # 常规问答（模拟）
        return (
            "这是模拟答复：\n\n1) 概念说明：示例解释。\n"
            "2) 实践建议：动手实现一个小例子。\n"
            "3) 参考：阅读教材与示例代码。"
        )

    def generate_mindmap(self, topic: str) -> Dict[str, Any]:
        tree = {
            "title": topic,
            "children": [
                {"title": "基础概念", "children": [{"title": "定义"}, {"title": "示例"}]},
                {"title": "应用场景", "children": [{"title": "分类"}, {"title": "回归"}]},
            ],
        }
        return tree

    def generate_code(self, topic: str, language: str = "python") -> str:
        if language.lower() == "python":
            return f"# {topic} 示例代码\nprint('Hello, {topic}!')\n"
        return f"// {topic} 示例代码 ({language})\nconsole.log('Hello, {topic}!');\n"

    def generate_questions(self, topic: str, num: int = 5) -> List[Dict[str, str]]:
        questions = []
        for i in range(num):
            questions.append({"q": f"{topic} 的第 {i+1} 个练习题？", "a": "示例答案"})
        return questions

    # 兼容 ResourceGenerator 等使用的旧接口
    def generate(self, prompt: str, **kwargs) -> str:
        # 若 ResourceGenerator 的 prompt（包含 '生成知识点树'），返回 JSON 树字符串
        if "生成知识点树" in prompt or "生成知识点树" in prompt.replace('“', '"'):
            return json.dumps(self.generate_mindmap(topic=kwargs.get("topic", "主题")), ensure_ascii=False)

        # 支持通过 kwargs 指定 resource_type
        rtype = kwargs.get("resource_type")
        topic = kwargs.get("topic") or kwargs.get("knowledge_point") or "人工智能"

        if rtype == "mindmap":
            return json.dumps(self.generate_mindmap(topic), ensure_ascii=False)
        if rtype == "question_bank" or rtype == "questions":
            return json.dumps(self.generate_questions(topic, kwargs.get("num", 5)), ensure_ascii=False)
        if rtype == "code":
            return self.generate_code(topic, kwargs.get("language", "python"))
        if rtype == "document" or rtype == "video_script":
            return self.generate_text(prompt)

        # fallback
        return self.generate_text(prompt)

    async def async_generate(self, prompt: str, timeout: Optional[int] = None) -> str:
        # 简单异步包装
        return self.generate(prompt)

