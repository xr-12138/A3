from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# 知识库目录
BASE_DIR = Path(__file__).resolve().parent.parent.parent
KB_DIR = BASE_DIR / "data" / "course_kb"

class KnowledgeBase:
    """课程知识库管理：读取结构化课程数据，为AI生成提供上下文"""

    def __init__(self, kb_path: Optional[str] = None):
        self.kb_path = Path(kb_path) if kb_path else KB_DIR
        self._manifest: Optional[Dict[str, Any]] = None
        self._chapters: Dict[str, Dict[str, Any]] = {}
        self._load_all()

    def _load_all(self) -> None:
        # 加载课程清单
        manifest_file = self.kb_path / "course_manifest.json"
        if manifest_file.exists():
            with open(manifest_file, "r", encoding="utf-8") as f:
                self._manifest = json.load(f)
        else:
            self._manifest = {
                "course_name": "数据结构",
                "chapters": []
            }
        # 加载所有章节
        for ch in self._manifest.get("chapters", []):
            fname = ch.get("file")
            if fname:
                fpath = self.kb_path / fname
                if fpath.exists():
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            self._chapters[fname] = json.load(f)
                    except Exception:
                        pass

    @property
    def manifest(self) -> Dict[str, Any]:
        """返回课程清单"""
        return self._manifest or {"course_name": "数据结构", "chapters": []}

    @property
    def course_name(self) -> str:
        return self.manifest.get("course_name", "数据结构")

    def list_chapters(self) -> List[Dict[str, Any]]:
        """返回所有章节的简要信息列表"""
        result = []
        for ch in self.manifest.get("chapters", []):
            result.append({
                "id": ch.get("id", ""),
                "title": ch.get("title", ""),
                "hours": ch.get("hours", 0),
                "file": ch.get("file", ""),
                "knowledge_points": ch.get("knowledge_points", [])
            })
        return result

    def get_chapter(self, chapter_id_or_file: str) -> Optional[Dict[str, Any]]:
        """根据ID或文件名获取完整章节内容"""
        # 先尝试以文件名查找
        if chapter_id_or_file in self._chapters:
            return self._chapters[chapter_id_or_file]
        # 再尝试以ID映射查找
        for ch in self.manifest.get("chapters", []):
            if ch.get("id") == chapter_id_or_file:
                fname = ch.get("file", "")
                if fname and fname in self._chapters:
                    return self._chapters[fname]
        return None

    def search_knowledge_point(self, keyword: str) -> List[Dict[str, Any]]:
        """根据关键词搜索知识点，返回匹配的知识点列表"""
        matches = []
        keyword_low = keyword.lower()
        for ch_id, chapter in self._chapters.items():
            summary = chapter.get("summary", "")
            if keyword_low in summary.lower():
                matches.append({
                    "chapter_id": chapter.get("chapter_id", ch_id),
                    "chapter_title": chapter.get("title", ""),
                    "type": "summary",
                    "content": summary
                })
            for kp in chapter.get("key_points", []):
                name = kp.get("name", "")
                content = kp.get("content", "")
                hit = False
                if keyword_low in name.lower():
                    hit = True
                elif keyword_low in content.lower():
                    hit = True
                if hit:
                    matches.append({
                        "chapter_id": chapter.get("chapter_id", ch_id),
                        "chapter_title": chapter.get("title", ""),
                        "kp_name": name,
                        "difficulty": kp.get("difficulty", ""),
                        "content": content[:800] + ("..." if len(content) > 800 else ""),
                        "type": "knowledge_point"
                    })
        return matches

    def get_questions(self, chapter_id_or_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取章节的练习题，不指定则获取所有章节"""
        qs = []
        target_files = set()
        if chapter_id_or_file:
            if chapter_id_or_file in self._chapters:
                target_files.add(chapter_id_or_file)
            else:
                for ch in self.manifest.get("chapters", []):
                    if ch.get("id") == chapter_id_or_file:
                        if ch.get("file"):
                            target_files.add(ch["file"])
        else:
            for ch in self.manifest.get("chapters", []):
                if ch.get("file"):
                    target_files.add(ch["file"])
        for fname in target_files:
            if fname in self._chapters:
                chapter = self._chapters[fname]
                for q in chapter.get("questions", []):
                    q_with_chapter = dict(q)
                    q_with_chapter["chapter"] = chapter.get("title", fname)
                    qs.append(q_with_chapter)
        return qs

    def get_code_examples(self, chapter_id_or_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取章节的代码示例"""
        codes = []
        target_files = set()
        if chapter_id_or_file:
            if chapter_id_or_file in self._chapters:
                target_files.add(chapter_id_or_file)
            else:
                for ch in self.manifest.get("chapters", []):
                    if ch.get("id") == chapter_id_or_file:
                        if ch.get("file"):
                            target_files.add(ch["file"])
        else:
            for ch in self.manifest.get("chapters", []):
                if ch.get("file"):
                    target_files.add(ch["file"])
        for fname in target_files:
            if fname in self._chapters:
                chapter = self._chapters[fname]
                for code in chapter.get("code_examples", []):
                    item = dict(code)
                    item["chapter"] = chapter.get("title", fname)
                    codes.append(item)
        return codes

    def get_reading_materials(self, chapter_id_or_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取章节的拓展阅读材料"""
        materials = []
        target_files = set()
        if chapter_id_or_file:
            if chapter_id_or_file in self._chapters:
                target_files.add(chapter_id_or_file)
            else:
                for ch in self.manifest.get("chapters", []):
                    if ch.get("id") == chapter_id_or_file:
                        if ch.get("file"):
                            target_files.add(ch["file"])
        else:
            for ch in self.manifest.get("chapters", []):
                if ch.get("file"):
                    target_files.add(ch["file"])
        for fname in target_files:
            if fname in self._chapters:
                chapter = self._chapters[fname]
                for m in chapter.get("reading_materials", []):
                    item = dict(m)
                    item["chapter"] = chapter.get("title", fname)
                    materials.append(item)
        return materials

    def get_course_overview(self) -> str:
        """生成课程概览文本"""
        manifest = self.manifest
        chapters = manifest.get("chapters", [])
        lines = []
        lines.append(f"课程：{manifest.get('course_name', '')}")
        if manifest.get("course_name_en"):
            lines.append(f"英文名称：{manifest.get('course_name_en', '')}")
        if manifest.get("target_major"):
            lines.append(f"目标专业：{manifest.get('target_major', '')}")
        if manifest.get("semester"):
            lines.append(f"学期：{manifest.get('semester', '')}")
        total_h = manifest.get("total_hours", 0)
        lines.append(f"总学时：{total_h}")
        lines.append("")
        lines.append("章节结构：")
        for i, ch in enumerate(chapters, 1):
            kp = ", ".join(ch.get("knowledge_points", []))
            lines.append(f"第{i}章 {ch.get('title', '')}（{ch.get('hours', 0)}学时）")
            if kp:
                lines.append(f"   知识点：{kp}")
        return "\n".join(lines)

    def build_prompt_context(self, topic: str, max_chars: int = 2000) -> str:
        """为给定主题构建参考知识库的prompt上下文"""
        lines = []
        lines.append("【知识库参考内容】")
        lines.append(f"课程：{self.course_name}")
        lines.append("")
        # 搜索相关知识点
        matches = self.search_knowledge_point(topic)
        if matches:
            lines.append(f"找到 {len(matches)} 个相关知识点：")
            lines.append("-" * 40)
            for m in matches[:5]:  # 最多取5个
                if m.get("type") == "knowledge_point":
                    lines.append(f"知识点：{m.get('kp_name', '')}（{m.get('chapter_title', '')}，难度：{m.get('difficulty', '')}）")
                    lines.append(f"内容：{m.get('content', '')}")
                else:
                    lines.append(f"章节摘要：{m.get('chapter_title', '')}")
                    lines.append(f"内容：{m.get('content', '')}")
                lines.append("-" * 40)
        else:
            # 没有精确匹配时，给整体课程概述
            lines.append(f"课程《{self.course_name}》包含以下章节：")
            for i, ch in enumerate(self.manifest.get("chapters", []), 1):
                lines.append(f"  {i}. {ch.get('title', '')}")
        text = "\n".join(lines)
        if len(text) > max_chars:
            text = text[:max_chars] + "\n...（已截断）"
        return text


# 全局单例
_instance: Optional[KnowledgeBase] = None


def get_knowledge_base() -> KnowledgeBase:
    """获取知识库单例"""
    global _instance
    if _instance is None:
        _instance = KnowledgeBase()
    return _instance


if __name__ == "__main__":
    # 快速测试
    kb = get_knowledge_base()
    print("课程名称:", kb.course_name)
    print("章节数:", len(kb.list_chapters()))
    # 搜索测试
    results = kb.search_knowledge_point("二叉树")
    print(f"搜索'二叉树'，找到 {len(results)} 个结果")
    for r in results[:2]:
        print(" -", r.get("kp_name", r.get("chapter_title", "")))
    # 生成prompt
    ctx = kb.build_prompt_context("二叉树遍历")
    print("\n=== Prompt Context ===")
    print(ctx)