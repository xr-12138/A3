from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class BaseAIClient(ABC):
    """统一 AI 接口抽象类。

    子类需实现下面声明的方法以便在前端与资源生成器中统一调用。
    """

    @abstractmethod
    def generate_text(self, prompt: str, system_msg: str | None = None) -> str:
        """生成文本响应（可为纯文本、Markdown 或可解析为 JSON 的字符串）。"""
        raise NotImplementedError()

    @abstractmethod
    def generate_mindmap(self, topic: str) -> Dict:
        """生成思维导图的结构化表示（字典）。"""
        raise NotImplementedError()

    @abstractmethod
    def generate_code(self, topic: str, language: str = "python") -> str:
        """生成代码示例文本。"""
        raise NotImplementedError()

    @abstractmethod
    def generate_questions(self, topic: str, num: int = 5) -> List:
        """生成题目列表（可为 list 或 JSON 可序列化结构）。"""
        raise NotImplementedError()
    
    @abstractmethod
    def generate_reading_material(self, topic: str, num: int = 5) -> List:
        """生成拓展阅读材料列表，返回可序列化的列表，每项应包含 title/type/summary/difficulty/order/link 等字段。"""
        raise NotImplementedError()


def some_function(ai_client: BaseAIClient):
    result = ai_client.generate_text("问题")
