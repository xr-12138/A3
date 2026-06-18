from __future__ import annotations

from typing import Any, Dict, List

from src.api.base import BaseAIClient
from src.core.knowledge_base import get_knowledge_base


def _kb_context(topic: str, max_chars: int = 1200) -> str:
    """从知识库获取与主题相关的参考内容，用于增强AI生成"""
    try:
        kb = get_knowledge_base()
        matches = kb.search_knowledge_point(topic)
        if not matches:
            return ""
        pieces = []
        for m in matches[:4]:
            name = m.get("kp_name", "")
            chapter = m.get("chapter_title", "")
            content = m.get("content", "")
            if name and content:
                pieces.append(f"[{chapter}] {name}: {content[:300]}")
        if pieces:
            return "\n\n以下是课程知识库中与「" + topic + "」相关的参考内容，请在生成时结合以下知识点：\n" + "\n---\n".join(pieces)
        return ""
    except Exception:
        return ""


class DocumentAgent:
    def __init__(self, ai_client: BaseAIClient):
        self.ai = ai_client

    def run(self, topic: str) -> str:
        kb_ref = _kb_context(topic)
        prompt = f"请为主题「{topic}」生成一份教学文档，要求结构清晰、要点分明，符合高校数据结构课程教学风格。{kb_ref}"
        return self.ai.generate_text(prompt)


class MindmapAgent:
    def __init__(self, ai_client: BaseAIClient):
        self.ai = ai_client

    def run(self, topic: str) -> Dict:
        # 规范化不同 AI 客户端可能返回的思维导图格式，最终确保返回结构为
        # {"title": "...", "children": [ {"title": "...", "children": [...]}, ... ]}
        kb_ref = _kb_context(topic)
        raw = self.ai.generate_mindmap(topic + (f"（参考课程知识：{kb_ref}）" if kb_ref else ""))

        # 如果客户端返回的是字符串，尝试解析为 JSON
        try:
            if isinstance(raw, str):
                import json
                raw = json.loads(raw)
        except Exception:
            pass

        if not isinstance(raw, dict):
            # 回退为简单结构
            return {"title": topic, "children": [{"title": "基础概念", "note": "该节点包含基本定义与关键术语"}, {"title": "应用场景", "note": "该节点包含典型应用与案例"}]}

        # 如果返回使用 'nodes' 字段，转换为 children 列表
        if "children" not in raw and "nodes" in raw:
            nodes = raw.get("nodes") or []
            children = []
            for n in nodes:
                if isinstance(n, dict):
                    title = n.get("title") or n.get("name") or str(n)
                    child = {"title": title}
                else:
                    child = {"title": str(n)}
                children.append(child)
            raw["children"] = children

        # 最终确保至少包含 title 字段
        if "title" not in raw:
            raw["title"] = topic

        # 若是连接到真实 AI（如 OllamaClient），尝试一次性补全每个一级节点的 note 与 2 个子节点
        try:
            if hasattr(self.ai, "model") and isinstance(raw.get("children"), list) and len(raw["children"]) > 0:
                top_titles = [c.get("title") if isinstance(c, dict) else str(c) for c in raw["children"]]
                # 构建一次性提示，返回 JSON 映射：{"节点名": {"note": "...", "children": [{"title":"...","note":"..."}, ...]}, ...}
                prompt = (
                    f"针对课程主题 '{topic}'，请为下面的一级知识点生成简短描述(note，不超过60字)和最多2个三级子节点，每个子节点需包含title和note。"
                    f" 一级节点列表：{top_titles}\n"
                    "请只返回严格的 JSON，格式例如：{\"节点名\": {\"note\": \"...\", \"children\": [{\"title\":\"子节点\", \"note\":\"...\"}]}, ... }"
                )
                text = self.ai.generate_text(prompt)
                import json as _json
                try:
                    # 提取 JSON 块
                    m = _json.loads(text) if isinstance(text, str) and text.strip().startswith("{") else None
                except Exception:
                    m = None
                if not m:
                    # 尝试用 regex 提取
                    import re as _re
                    mm = _re.search(r"(\{.*\})", text, flags=_re.S)
                    if mm:
                        try:
                            m = _json.loads(mm.group(1))
                        except Exception:
                            m = None

                if isinstance(m, dict):
                    # 将补全内容合并回 raw
                    for c in raw.get("children", []):
                        title = c.get("title") if isinstance(c, dict) else str(c)
                        entry = m.get(title) or m.get(str(title))
                        if entry and isinstance(entry, dict):
                            if "note" in entry and not c.get("note"):
                                c["note"] = entry.get("note")
                            if "children" in entry and (not c.get("children") or len(c.get("children")) == 0):
                                # 转换子节点为 dict 结构
                                children_list = []
                                for sub in entry.get("children", [])[:2]:
                                    if isinstance(sub, dict):
                                        children_list.append({"title": sub.get("title") or sub.get("name") or str(sub), "note": sub.get("note")})
                                    else:
                                        children_list.append({"title": str(sub)})
                                c["children"] = children_list
        except Exception:
            # 补全过程非关键，忽略错误
            pass

        return raw


class QuestionBankAgent:
    def __init__(self, ai_client: BaseAIClient):
        self.ai = ai_client

    def run(self, topic: str, num: int = 5) -> List[Dict[str, str]]:
        kb_ref = _kb_context(topic)
        return self.ai.generate_questions(topic + (f"（请结合课程知识：{kb_ref}）" if kb_ref else ""), num)


class CodeAgent:
    def __init__(self, ai_client: BaseAIClient):
        self.ai = ai_client

    def run(self, topic: str, language: str = "python") -> str:
        kb_ref = _kb_context(topic)
        enriched_topic = topic + (f"（请结合课程知识：{kb_ref}）" if kb_ref else "")
        return self.ai.generate_code(enriched_topic, language=language)


class ReadingMaterialAgent:
    """拓展阅读材料生成代理"""
    def __init__(self, ai_client: BaseAIClient):
        self.ai = ai_client

    def run(self, topic: str) -> list:
        """为指定主题生成拓展阅读材料列表

        Args:
            topic: 课程主题或知识点

        Returns:
            结构化的阅读材料列表，每项包含：title, type, summary, difficulty, order, link
        """
        kb_ref = _kb_context(topic)
        enriched_topic = topic + (f"（参考课程知识：{kb_ref}）" if kb_ref else "")
        try:
            return self.ai.generate_reading_material(enriched_topic)
        except Exception:
            # 回退为之前的文本提示（兼容旧的 AI 客户端实现）
            prompt = (
                f"请为高校课程主题'{enriched_topic}'生成一份拓展阅读材料列表，返回中文文本或 Markdown。"
                "每条推荐应包含：1) 标题；2) 资源类型（书籍/论文/博客/视频/教程）；"
                "3) 不超过120字的摘要或为何推荐该资源；4) 难度标签（初级/中级/高级）；"
                "5) 推荐顺序或学习阶段；如有可用链接或 DOI 请一并提供。"
            )
            return self.ai.generate_text(prompt)