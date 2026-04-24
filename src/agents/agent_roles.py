from enum import Enum


class AgentRole(Enum):
    PROFILE = "profile"
    RESOURCE = "resource"
    PATH = "path"
    TUTORING = "tutoring"
    EVALUATION = "evaluation"


ROLE_DESCRIPTIONS = {
    AgentRole.PROFILE: "用户画像：收集并解析用户学习画像/偏好",
    AgentRole.RESOURCE: "资源生成：生成文档/思维导图/题库/代码/视频脚本等",
    AgentRole.PATH: "路径规划：给出学习路径和步骤",
    AgentRole.TUTORING: "辅导：提供分步辅导与答疑",
    AgentRole.EVALUATION: "评估：对产出进行质量与掌握度评估",
}
