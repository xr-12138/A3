# src/api/mock_client.py
class MockClient:
    def generate(self, prompt):
        if "人工智能" in prompt:
            return """
人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，
它旨在创建能够执行通常需要人类智能的任务的系统。
主要分支包括：机器学习、深度学习、自然语言处理、计算机视觉等。
            """
        elif "思维导图" in prompt:
            return """
{
  "title": "人工智能概述",
  "nodes": [
    {"id": 1, "label": "定义", "parent": 0},
    {"id": 2, "label": "发展历史", "parent": 0},
    {"id": 3, "label": "主要分支", "parent": 0},
    {"id": 4, "label": "机器学习", "parent": 3},
    {"id": 5, "label": "深度学习", "parent": 3}
  ]
}
            """
        else:
            return "这是模拟的AI回答内容。"

mock_client = MockClient()
