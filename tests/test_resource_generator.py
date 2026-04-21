# tests/test_resource_generator.py
import sys
from pathlib import Path

# 修复路径
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

# 🔥 直接在这里写 Mock，不用导入任何文件
class SimpleMockAI:
    def generate(self, prompt):
        return f"这是针对问题 '{prompt}' 的模拟AI回答。人工智能是研究使计算机模拟人类智能的学科。"

def test_simple_mock():
    print("🚀 测试 Mock AI 客户端...")

    ai = SimpleMockAI()
    prompt = "介绍人工智能"
    result = ai.generate(prompt)

    print("✅ Mock 返回结果：")
    print(result)
    print("\n🎉 Mock 客户端调用成功！项目可以继续开发！")

if __name__ == "__main__":
    test_simple_mock()
