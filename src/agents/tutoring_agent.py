from __future__ import annotations

from typing import Dict, Any

from src.api.base import BaseAIClient


class TutoringAgent:
    """辅导智能体：根据用户进度提供分步辅导或答疑。"""

    def __init__(self, ai_client: BaseAIClient):
        self.ai = ai_client

    def run(self, question: str) -> Dict[str, Any]:
        # 构造指令，要求返回简洁美观的中文 Markdown 格式回复，包含：简要回答、分步解答、示例（如适用）、参考/拓展
        instruction = (
            "请作为专业的中文教学助理回答下面的问题，要求：\n"
            "1) 全程使用中文回答，不要使用英文或其他语言。\n"
            "2) 以 Markdown 格式组织答案，结构清晰，层次分明。\n"
            "3) 包含以下可选小节（若无对应内容可省略）：\n"
            "   - **简要回答**：用一句话总结答案，简洁明了。\n"
            "   - **分步解答**：按步骤列出解决方法或推导过程，使用有序列表。\n"
            "   - **示例**：如有示例代码或计算步骤，请用代码块或示例块展示。\n"
            "   - **参考/拓展**：给出1-3条参考方向或关键词。\n"
            "4) 不要包含任何奇怪的符号、重复的字符或与问题无关的内容。\n"
            "5) 回复要简洁美观，避免冗长的说明和不必要的修饰。\n"
            "6) 确保答案的逻辑性和连贯性，便于学生理解。\n\n"
            "问题：\n" + question
        )

        raw = self.ai.generate_text(instruction)

        # 后处理：去除控制字符、重复长符号，规范空行
        import re

        text = raw
        # 移除零宽字符
        text = re.sub(r"[\u200B-\u200F\uFEFF]", "", text)
        # 移除不可见字符
        text = re.sub(r"[\x00-\x1F\x7F]", "", text)
        # 把连续超过3个相同符号缩短为3个
        text = re.sub(r"([=~`\-\*_#])\1{3,}", r"\1\1\1", text)
        # 把超过2个空行压缩为2个（保留段落分隔），并保留行首空格以兼容代码块的缩进
        text = re.sub(r"\n{3,}", "\n\n", text)
        lines = text.split('\n')
        # 仅去除行尾空白，保留行首缩进
        cleaned_lines = [line.rstrip() for line in lines]
        # 压缩连续空行为最多两个，保留段落分隔
        collapsed = []
        empty_count = 0
        for line in cleaned_lines:
            if line.strip() == "":
                empty_count += 1
                if empty_count <= 2:
                    collapsed.append("")
            else:
                empty_count = 0
                collapsed.append(line)
        text = '\n'.join(collapsed).strip()

        # 如果返回中不包含中文，添加提示（但仍返回原文）
        if not re.search(r"[\u4e00-\u9fff]", text):
            text = "（注意：模型回复似乎不是中文，以下为原始回复）\n\n" + text
        
        # 确保返回的是Markdown格式
        if not text.startswith('#') and not text.startswith('**'):
            # 添加标题
            text = f"# 问题解答\n\n" + text

        return {"answer": text}