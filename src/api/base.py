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
