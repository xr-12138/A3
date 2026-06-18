from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# 知识库根目录（每门课程一个子目录）
BASE_DIR = Path(__file__).resolve().parent.parent.parent
KB_DIR = BASE_DIR / "data" / "course_kb"


def _safe_load_json(path: Path) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file, returning None on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def list_courses(kb_path: Optional[Path] = None) -> List[Dict[str, str]]:
    """扫描知识库目录，返回所有可用课程列表（每门课程对应一个子目录，
    子目录下需要存在 course_manifest.json）。

    返回列表元素形如:
        {"id": "<subdir_name>", "course_name": "...", "course_name_en": "..."}
    """
    root = Path(kb_path) if kb_path else KB_DIR
    courses: List[Dict[str, str]] = []
    if not root.exists():
        return courses
    for entry in sorted(root.iterdir()):
        if entry.is_dir():
            manifest_file = entry / "course_manifest.json"
            if manifest_file.exists():
                data = _safe_load_json(manifest_file)
                if data:
                    courses.append({
                        "id": entry.name,
                        "course_name": data.get("course_name", entry.name),
                        "course_name_en": data.get("course_name_en", ""),
                    })
    return courses


class KnowledgeBase:
    """课程知识库管理：读取结构化课程数据，为AI生成提供上下文。

    支持多课程：通过 ``course_id`` 指定课程子目录（子目录下需要包含
    ``course_manifest.json`` 以及对应的章节 JSON 文件）。
    """

    def __init__(self, course_id: str = "data_structures", kb_path: Optional[str] = None):
        self.course_id = course_id
        self.root_path = Path(kb_path) if kb_path else KB_DIR
        self.course_dir = self.root_path / course_id
        self._manifest: Optional[Dict[str, Any]] = None
        self._chapters: Dict[str, Dict[str, Any]] = {}
        self._load_all()

    def _load_all(self) -> None:
        manifest_file = self.course_dir / "course_manifest.json"
        if manifest_file.exists():
            with open(manifest_file, "r", encoding="utf-8") as f:
                self._manifest = json.load(f)
        else:
            # 尝试使用旧的扁平化结构（向前兼容）
            fallback = self.root_path / "course_manifest.json"
            if fallback.exists():
                self.course_dir = self.root_path
                with open(fallback, "r", encoding="utf-8") as f:
                    self._manifest = json.load(f)
            else:
                self._manifest = {
                    "course_name": "数据结构",
                    "chapters": []
                }

        for ch in self._manifest.get("chapters", []):
            fname = ch.get("file")
            if fname:
                fpath = self.course_dir / fname
                if fpath.exists():
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            self._chapters[fname] = json.load(f)
                    except Exception:
                        pass

    @property
    def manifest(self) -> Dict[str, Any]:
        return self._manifest or {"course_name": "数据结构", "chapters": []}

    @property
    def course_name(self) -> str:
        return self.manifest.get("course_name", self.course_id)

    def list_chapters(self) -> List[Dict[str, Any]]:
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
        if chapter_id_or_file in self._chapters:
            return self._chapters[chapter_id_or_file]
        for ch in self.manifest.get("chapters", []):
            if ch.get("id") == chapter_id_or_file:
                fname = ch.get("file", "")
                if fname and fname in self._chapters:
                    return self._chapters[fname]
        return None

    def search_knowledge_point(self, keyword: str) -> List[Dict[str, Any]]:
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
        lines = []
        lines.append("【知识库参考内容】")
        lines.append(f"课程：{self.course_name}")
        lines.append("")
        matches = self.search_knowledge_point(topic)
        if matches:
            lines.append(f"找到 {len(matches)} 个相关知识点：")
            lines.append("-" * 40)
            for m in matches[:5]:
                if m.get("type") == "knowledge_point":
                    lines.append(f"知识点：{m.get('kp_name', '')}（{m.get('chapter_title', '')}，难度：{m.get('difficulty', '')}）")
                    lines.append(f"内容：{m.get('content', '')}")
                else:
                    lines.append(f"章节摘要：{m.get('chapter_title', '')}")
                    lines.append(f"内容：{m.get('content', '')}")
                lines.append("-" * 40)
        else:
            lines.append(f"课程《{self.course_name}》包含以下章节：")
            for i, ch in enumerate(self.manifest.get("chapters", []), 1):
                lines.append(f"  {i}. {ch.get('title', '')}")
        text = "\n".join(lines)
        if len(text) > max_chars:
            text = text[:max_chars] + "\n...（已截断）"
        return text


# 按课程 id 缓存实例，避免反复读取磁盘
_course_cache: Dict[str, KnowledgeBase] = {}


def get_knowledge_base(course_id: Optional[str] = None) -> KnowledgeBase:
    """获取指定课程的知识库实例；未指定时默认使用第一门可用课程。"""
    courses = list_courses()
    if not course_id:
        if courses:
            course_id = courses[0]["id"]
        else:
            course_id = "data_structures"
    if course_id not in _course_cache:
        _course_cache[course_id] = KnowledgeBase(course_id=course_id)
    return _course_cache[course_id]


def reset_cache() -> None:
    _course_cache.clear()


if __name__ == "__main__":
    courses = list_courses()
    print(f"共发现 {len(courses)} 门课程：")
    for c in courses:
        print(f"  - {c['id']}: {c['course_name']} ({c['course_name_en']})")
        kb = get_knowledge_base(c["id"])
        print(f"    章节数: {len(kb.list_chapters())}")
        results = kb.search_knowledge_point("函数")
        print(f"    搜索'函数'，找到 {len(results)} 个结果")