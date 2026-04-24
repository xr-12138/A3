from __future__ import annotations

from src.api.mock_client import MockClient
from src.agents.multi_agent_scheduler import MultiAgentScheduler


def demo():
    ai = MockClient()
    sched = MultiAgentScheduler(ai)
    user_prompt = "我是一名计算机专业的大学生，希望在半年内掌握机器学习基础，喜欢通过代码和视频学习。"
    topic = "机器学习入门"
    result = sched.run_full_flow(user_prompt, topic)
    print("调度器输出：")
    for k, v in result.items():
        if k == "resources":
            print("- resources keys:", list(v.keys()))
        else:
            print(f"- {k}: ", type(v))


if __name__ == "__main__":
    demo()
