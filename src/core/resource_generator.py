"""
资源生成器 —— 知识点思维导图（Mindmap）模块

功能：调用 LLM（如接入讯飞 API 的 llm_client），从课程主题生成分层知识点树并渲染为 PNG 思维导图。

兼容性：Python 3.12，Linux。依赖：`graphviz` Python 包与系统级 `graphviz` 二进制。

使用说明：
- 将实现的 `llm_client` 作为参数传入，`llm_client` 需提供同步方法 `generate(prompt: str) -> str`
  或异步方法 `async_generate(prompt: str) -> str`（函数名任选其一）。
- 如果没有可用 llm_client，可先提供一个 `structure`（字典）直接调用 `render_mindmap`。
"""
from __future__ import annotations

import os
import re
import json
import asyncio
import logging
from typing import Any, Dict, Optional

from graphviz import Digraph

logger = logging.getLogger(__name__)


class ResourceGenerator:
    def __init__(self, llm_client: Optional[Any] = None, work_dir: str = "data/generated") -> None:
        self.llm_client = llm_client
        self.work_dir = work_dir
        os.makedirs(self.work_dir, exist_ok=True)

    def _build_prompt(self, topic: str, course: str = "人工智能", max_depth: int = 3, max_branch: int = 4) -> str:
        prompt = (
            f"为高校课程“{course}”生成知识点树，主题为“{topic}”。"
            "输出必须为严格的 JSON 格式，形如：\n"
            "{\n  \"title\": \"根节点\",\n  \"children\": [ ... ]\n}\n"
            "每个节点包含字段：`title` (字符串)，可选 `note` (字符串)，可选 `children` (数组)。\n"
            f"请限制深度为 {max_depth} 层，每层分支不超过 {max_branch} 个，并确保 JSON 易于解析。"
        )
        return prompt

    def _extract_json(self, text: str) -> str:
        # 尝试直接解析；失败时用正则提取最外层 JSON
        try:
            json.loads(text)
            return text
        except Exception:
            pass

        # 提取第一个以 { 开始以 } 结束的 JSON 块
        m = re.search(r"(\{.*\})", text, flags=re.S)
        if m:
            return m.group(1)
        raise ValueError("LLM 返回中未找到可解析的 JSON 内容")

    def _parse_structure(self, raw: str) -> Dict[str, Any]:
        js = self._extract_json(raw)
        return json.loads(js)

    def _node_id(self, idx: int) -> str:
        return f"n{idx}"

    def render_mindmap(self, structure: Dict[str, Any], output_name: Optional[str] = None, format: str = "png") -> str:
        """根据已构建的知识点树渲染思维导图并保存为 PNG。

        structure 示例：
        {"title": "机器学习", "children": [{"title": "监督学习", "children": [...]}, ...]}

        返回生成的文件路径（PNG）。
        """
        if not isinstance(structure, dict) or "title" not in structure:
            raise ValueError("structure 必须为包含 'title' 的 dict")

        if output_name is None:
            safe_title = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "_", structure.get("title", "mindmap")).strip("_")
            output_name = f"{safe_title}.mindmap"

        out_path_base = os.path.join(self.work_dir, output_name)
        dot = Digraph(name="mindmap", format=format)
        dot.attr(rankdir="LR")
        dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightyellow', fontsize='12')

        counter = {"i": 0}

        def add_nodes(node: Dict[str, Any], parent_id: Optional[str] = None) -> str:
            counter["i"] += 1
            nid = self._node_id(counter["i"])
            label = node.get("title", "")
            note = node.get("note")
            if note:
                label = f"{label}\n{note}"
            # 防止 label 过长，做简单裁剪
            if len(label) > 120:
                label = label[:117] + "..."
            dot.node(nid, label)
            if parent_id:
                dot.edge(parent_id, nid)
            for child in node.get("children", [])[:50]:
                add_nodes(child, nid)
            return nid

        add_nodes(structure, None)

        rendered_path = dot.render(filename=out_path_base, cleanup=True)
        # graphviz.render 返回生成文件全路径（含后缀）
        logger.info("Mindmap rendered to %s", rendered_path)
        return rendered_path

    def generate_mindmap(self, topic: str, course: str = "人工智能", max_depth: int = 3, max_branch: int = 4, output_name: Optional[str] = None, timeout: int = 60) -> str:
        """同步接口：使用内置 llm_client 生成知识结构并渲染为 PNG。

        llm_client 支持两种方法之一：
        - 同步：`generate(prompt: str) -> str`
        - 异步：`async_generate(prompt: str) -> str`
        """
        if not self.llm_client:
            raise ValueError("llm_client 未配置；需要传入可用的 LLM/讯飞 客户端实例")

        prompt = self._build_prompt(topic, course, max_depth, max_branch)

        # 调用 LLM：支持 sync/async 两种方法名
        response_text = None
        # 优先检查异步方法名
        if hasattr(self.llm_client, "async_generate"):
            try:
                response_text = asyncio.run(self.llm_client.async_generate(prompt, timeout=timeout))
            except Exception as e:
                logger.exception("async_generate 调用失败: %s", e)
                raise
        elif hasattr(self.llm_client, "generate"):
            try:
                response_text = self.llm_client.generate(prompt, timeout=timeout)
            except TypeError:
                # 兼容一些 client 不接收 timeout 参数
                response_text = self.llm_client.generate(prompt)
            except Exception as e:
                logger.exception("generate 调用失败: %s", e)
                raise
        else:
            raise ValueError("llm_client 不包含 'generate' 或 'async_generate' 方法")

        struct = self._parse_structure(response_text)
        return self.render_mindmap(struct, output_name)


if __name__ == "__main__":
    # 快速本地测试（无需真实讯飞 API）
    class MockLLM:
        def generate(self, prompt: str, timeout: int = 30) -> str:
            # 返回一个简单的 JSON 树
            return json.dumps({
                "title": "人工智能",
                "children": [
                    {"title": "机器学习", "children": [
                        {"title": "监督学习"}, {"title": "无监督学习"}
                    ]},
                    {"title": "深度学习", "children": [
                        {"title": "神经网络"}, {"title": "卷积神经网络"}
                    ]}
                ]
            }, ensure_ascii=False)

    rg = ResourceGenerator(llm_client=MockLLM())
    out = rg.generate_mindmap(topic="人工智能导论", course="人工智能", max_depth=3)
    print("生成文件：", out)
