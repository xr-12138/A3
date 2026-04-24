import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from src.agents.multi_agent_scheduler import MultiAgentScheduler
from src.api.mock_client import MockClient

def test_multi_agent():
    ai = MockClient()
    scheduler = MultiAgentScheduler(ai)
    
    # 测试不同任务
    print("🚀 测试画像构建智能体...")
    profile = scheduler.profile_agent.run("我是计算机专业大二学生，想学习机器学习")
    print("✅ 画像生成成功：", profile.keys())
    
    print("\n🚀 测试资源生成智能体...")
    resource = scheduler.resource_agent.run("机器学习概述")
    print("✅ 资源生成成功：包含", list(resource.keys()), "等资源")
    
    print("\n🚀 测试路径规划智能体...")
    path = scheduler.path_agent.run("机器学习")
    print("✅ 学习路径生成成功：", path)
    
    print("\n🎉 所有智能体测试通过！")

if __name__ == "__main__":
    test_multi_agent()