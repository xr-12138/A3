from __future__ import annotations

from abc import ABC, abstractmethod
import json
from typing import Any, Dict


class BaseAIClient(ABC):
    """统一 AI 接口抽象类，子类需实现 `generate(prompt, **kwargs)` 方法。
    返回值为字符串（可为 JSON、Markdown、纯文本等）。
    """

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError()


class MockClient(BaseAIClient):
    """用于界面演示的 Mock Client。

    支持通过 `mode` 参数区分生成类型：
    - mode='profile'：返回包含 6 维画像的 JSON 字符串
    - mode='resource'：返回生成资源的文本/Markdown
    - mode='answer'：返回对问题的解答文本
    """

    def generate(self, prompt: str, **kwargs) -> str:
        mode = kwargs.get("mode", "resource")
        if mode == "profile":
            profile = {
                "knowledge_base": "中等",
                "cognitive_style": "视觉 + 阅读",
                "weak_points": "概率论、线性代数",
                "learning_goal": "掌握机器学习基础并能实现模型",
                "study_time": "每天 1 小时",
                "resource_pref": "示例代码 + 视频讲解",
            }
            return json.dumps(profile, ensure_ascii=False)

        if mode == "answer":
            # 简单模拟分段式回答（可在前端做流式展示）
            return (
                "这是模拟答复：\n\n1) 概念说明：卷积神经网络用于提取局部特征。\n"
                "2) 实践建议：先实现简单的卷积层并观察特征图。\n"
                "3) 参考代码片段已保存为示例。"
            )

        # 默认 resource
        rtype = kwargs.get("resource_type", "document")
        topic = kwargs.get("topic", "人工智能入门")
        kp = kwargs.get("knowledge_point", "机器学习")
        if rtype == "document":
            return f"# {topic} - {kp} 文档\n\n本节介绍 {kp} 的核心概念与案例。"
        if rtype == "question_bank":
            q = [
                {"q": f"{kp} 的核心任务是什么？", "a": "分类/回归"},
                {"q": "给出一个简单的练习题", "a": "实现线性回归"},
            ]
            return json.dumps(q, ensure_ascii=False)
        if rtype == "code":
            return (
                "# 示例代码：线性回归\nimport numpy as np\n\ndef predict(w,x):\n    return np.dot(x,w)"
            )
        if rtype == "video_script":
            return f"镜头1：引入{kp}背景。\n镜头2：概念讲解 + 示例。\n镜头3：练习与扩展。"

        # 思维导图 / mindmap 返回结构化 JSON
        if rtype == "mindmap":
            tree = {
                "title": topic,
                "children": [
                    {"title": kp, "children": [{"title": "概念"}, {"title": "例子"}]},
                    {"title": "扩展", "children": [{"title": "实践"}, {"title": "阅读"}]},
                ],
            }
            return json.dumps(tree, ensure_ascii=False)

        return ""
