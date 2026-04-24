from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class BaseAIClient(ABC):
    """统一 AI 接口抽象类。

    子类需实现下面声明的方法以便在前端与资源生成器中统一调用。
    """

    @abstractmethod
    def generate_text(self, prompt: str) -> str:
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
# src/api/base.py（统一接口）
class BaseAIClient:
    def generate(self, prompt):
        raise NotImplementedError

# src/api/mock_client.py（临时实现）
class MockClient(BaseAIClient):
    def generate(self, prompt):
        return "模拟回答"

# src/api/xfyun_api.py（后续真实实现）
class XFYunClient(BaseAIClient):
    def generate(self, prompt):
        # 调用真实讯飞API
        pass

# 其他代码只依赖 BaseAIClient，不关心具体实现
def some_function(ai_client: BaseAIClient):
    result = ai_client.generate("问题")
