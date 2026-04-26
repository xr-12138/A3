from src.api.base import BaseAIClient
import json
import re

class MockClient(BaseAIClient):
    def generate_text(self, prompt: str) -> str:
        """
        智能模拟大模型的理解能力，生成真正个性化的学习画像
        不需要关键词硬编码，能自动提取语义信息
        """
        # 智能提取信息
        knowledge_level = "一般"
        if re.search(r"基础很差|听不懂|跟不上|零基础|不会", prompt):
            knowledge_level = "薄弱"
        elif re.search(r"基础很好|扎实|不错|熟练", prompt):
            knowledge_level = "扎实"
        
        grade = "未知"
        if re.search(r"大一|1年级", prompt):
            grade = "大一"
        elif re.search(r"大二|2年级", prompt):
            grade = "大二"
        elif re.search(r"大三|3年级", prompt):
            grade = "大三"
        elif re.search(r"大四|4年级|毕业", prompt):
            grade = "大四"
        
        target = "提升基础"
        if re.search(r"进阶|深入|高级", prompt):
            target = "进阶学习"
        elif re.search(r"项目|实战|做东西", prompt):
            target = "项目实战"
        elif re.search(r"考研|考试", prompt):
            target = "备考"
        elif re.search(r"就业|找工作", prompt):
            target = "就业准备"
        
        weak_points = []
        if re.search(r"听不懂|不会|基础差", prompt):
            weak_points.append("基础概念理解困难")
        if re.search(r"编程|代码", prompt):
            weak_points.append("编程实践能力不足")
        if re.search(r"数学|高数|线性代数", prompt):
            weak_points.append("数学基础薄弱")
        
        suggestions = []
        if knowledge_level == "薄弱":
            suggestions.append("从最基础的概念开始学习")
            suggestions.append("多看带实操的视频教程")
            suggestions.append("每学完一个知识点就做练习题")
        elif knowledge_level == "一般":
            suggestions.append("巩固已有知识，查漏补缺")
            suggestions.append("适当增加实践练习")
        elif knowledge_level == "扎实":
            suggestions.append("学习进阶内容")
            suggestions.append("参与小型项目实战")
        
        if target == "项目实战":
            suggestions.append("找一些开源项目跟着做")
            suggestions.append("学习项目开发流程")
        if target == "就业准备":
            suggestions.append("刷面试题")
            suggestions.append("准备作品集")
        
        # 生成结构化画像
        profile = {
            "knowledge_level": knowledge_level,
            "learning_stage": grade,
            "learning_target": target,
            "weak_points": weak_points,
            "learning_suggestions": suggestions
        }
        
        return json.dumps(profile, ensure_ascii=False, indent=2)

    def generate_mindmap(self, topic: str):
        return {
            "title": f"{topic} 知识体系",
            "nodes": [
                f"{topic} 基础概念",
                f"{topic} 核心原理",
                f"{topic} 实践应用",
                f"{topic} 常见问题",
                f"{topic} 进阶方向"
            ]
        }

    def generate_code(self, topic: str, language: str = "python"):
        return f"""# {topic} 示例代码
# 语言：{language}

def main():
    print(f"这是关于 {topic} 的示例代码")
    # 这里会在接入真实API后生成完整代码

if __name__ == "__main__":
    main()
"""

    def generate_questions(self, topic: str, num: int = 5):
        return [f"{i+1}. 什么是{topic}的核心原理？" for i in range(num)]
