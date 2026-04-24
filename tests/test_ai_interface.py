import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from src.api.mock_client import MockClient

def test_ai_interface():
    ai = MockClient()
    
    # 测试所有接口
    text = ai.generate_text("介绍人工智能")
    mindmap = ai.generate_mindmap("机器学习")
    code = ai.generate_code("快速排序")
    questions = ai.generate_questions("神经网络")
    
    print("✅ 文本生成成功：", text[:50], "...")
    print("✅ 思维导图生成成功：", mindmap["title"])
    print("✅ 代码生成成功：", code[:50], "...")
    print("✅ 题库生成成功：共", len(questions), "道题")
    
    print("\n🎉 所有AI接口测试通过！")

if __name__ == "__main__":
    test_ai_interface()
