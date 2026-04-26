from __future__ import annotations

from typing import Dict, Any

from src.api.base import BaseAIClient
from .profile_agent import ProfileAgent
from .resource_agent import ResourceAgent
from .path_agent import PathAgent
from .tutoring_agent import TutoringAgent
from .evaluation_agent import EvaluationAgent


class MultiAgentScheduler:
    """多智能体调度器：负责任务分发与结果汇总。

    说明：本实现保持轻量，不依赖 langchain 运行时；各智能体通过 `BaseAIClient` 调用 AI。
    """

    def __init__(self, ai_client: BaseAIClient):
        self.ai = ai_client
        self.profile_agent = ProfileAgent(ai_client)
        self.resource_agent = ResourceAgent(ai_client)
        self.path_agent = PathAgent(ai_client)
        self.tutoring_agent = TutoringAgent(ai_client)
        self.evaluation_agent = EvaluationAgent(ai_client)

    def run_full_flow(self, user_prompt: str, topic: str) -> Dict[str, Any]:
        # 1. 用户画像
        profile = self.profile_agent.run(user_prompt)

        # 2. 资源生成（并行可选，这里同步）
        resources = self.resource_agent.run(topic)

        # 3. 路径规划
        plan = self.path_agent.run(topic)

        # 4. 简单辅导示例：对第一个题目进行答疑（若存在）
        q_item = None
        qlist = resources.get("question_bank")
        if qlist and isinstance(qlist, list) and len(qlist) > 0:
            q_item = qlist[0].get("q") if isinstance(qlist[0], dict) else str(qlist[0])

        tutoring = None
        if q_item:
            tutoring = self.tutoring_agent.run(f"请解答：{q_item}")

        # 5. 评估：对文档给出评价
        evaluation = self.evaluation_agent.run(resources.get("document", ""))

        # 汇总
        return {
            "profile": profile,
            "resources": resources,
            "plan": plan,
            "tutoring": tutoring,
            "evaluation": evaluation,
        }

    def execute_task(self, task_name: str, payload: Any = None) -> Any:
        """执行指定任务并返回结果"""
        try:
            if task_name == "profile":
                if not payload:
                    return {"error": "No input provided for profile task"}
                return self.profile_agent.run(payload)
            elif task_name == "resource":
                if not payload:
                    return {"error": "No input provided for resource task"}
                # 提取必要参数
                topic = payload.get("kp", payload.get("knowledge_point", "人工智能"))
                return self.resource_agent.run(topic)
            elif task_name == "path":
                if not payload:
                    return {"error": "No profile provided for path task"}
                return self.path_agent.run(payload)
            elif task_name == "tutoring":
                if not payload:
                    return {"error": "No question provided for tutoring task"}
                return self.tutoring_agent.run(payload)
            else:
                return {"error": f"Unknown task type: {task_name}"}
        except Exception as e:
            return {"error": f"Task execution failed: {str(e)}"}