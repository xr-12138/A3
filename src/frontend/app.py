
from __future__ import annotations

# 🔥 第2行开始：路径修复代码
import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))



import json
import time
from pathlib import Path
from typing import Optional

import streamlit as st

from src.frontend.clients import MockClient, BaseAIClient
from src.core.resource_generator import ResourceGenerator

# 项目根目录（固定为要求路径）
BASE_DIR = Path("/home/hjj/桌面/A3-main")
DATA_DIR = BASE_DIR / "data"
DATASET_DIR = DATA_DIR / "dataset"
GENERATED_DIR = DATA_DIR / "generated"
for p in (DATA_DIR, DATASET_DIR, GENERATED_DIR):
    p.mkdir(parents=True, exist_ok=True)


def sidebar_nav() -> str:
    st.sidebar.title("导航")
    return st.sidebar.radio("选择页面", [
        "画像构建",
        "多模态资源生成",
        "个性化学习路径",
        "智能辅导",
    ])


def render_profile_page(ai: BaseAIClient):
    st.header("学习画像构建")
    st.write("通过对话输入学生信息，系统将自动生成 6 维度学习画像并卡片化展示。")

    if "conv" not in st.session_state:
        st.session_state.conv = []
    if "profile" not in st.session_state:
        st.session_state.profile = None

    user_input = st.text_input("与学生对话（例如：我是一名计算机专业大二学生，想学机器学习）", key="profile_input")
    if st.button("发送", key="send_profile") and user_input:
        st.session_state.conv.append({"role": "user", "text": user_input})
        with st.spinner("正在生成画像..."):
            resp = ai.generate(user_input, mode="profile")
            try:
                profile = json.loads(resp)
            except Exception:
                profile = {}
            st.session_state.profile = profile

    if st.session_state.profile:
        st.subheader("学生画像")
        cols = st.columns(3)
        items = list(st.session_state.profile.items())
        for i, (k, v) in enumerate(items):
            with cols[i % 3]:
                st.markdown(f"### {k.replace('_',' ').title()}\n{v}")


def render_resource_page(ai: BaseAIClient):
    st.header("多模态资源生成")
    st.write("选择课程、知识点和资源类型，生成并预览资源（文档/思维导图/题库/代码/视频脚本）。")

    course = st.text_input("课程", value="人工智能")
    knowledge_point = st.text_input("知识点", value="机器学习")
    rtype = st.selectbox("资源类型", ["document", "mindmap", "question_bank", "code", "video_script"], index=0)

    if st.button("生成资源"):
        progress = st.progress(0)
        placeholder = st.empty()
        for i in range(5):
            time.sleep(0.15)
            progress.progress((i + 1) * 20)

        # 调用 AI
        resp = ai.generate("generate resource", resource_type=rtype, topic=course, knowledge_point=knowledge_point)

        if rtype == "mindmap":
            # 尝试调用 ResourceGenerator 渲染 PNG（若 graphviz 可用）
            try:
                rg = ResourceGenerator(llm_client=ai, work_dir=str(GENERATED_DIR))
                # ai 需要返回 JSON 树；MockClient 返回 JSON 树 when resource_type==mindmap
                mindmap_path = rg.generate_mindmap(topic=course, course=course, output_name=f"{knowledge_point}.mindmap")
                st.success("思维导图已生成：")
                st.image(mindmap_path)
            except Exception:
                st.warning("Graphviz 不可用，展示为结构化文本。")
                try:
                    tree = json.loads(resp)
                    st.json(tree)
                except Exception:
                    st.text(resp)
        elif rtype == "document":
            # 保存并预览 Markdown
            out = GENERATED_DIR / f"{knowledge_point}.md"
            out.write_text(resp, encoding="utf-8")
            st.markdown(resp)
            st.success(f"文档已保存：{out}")
        elif rtype == "question_bank":
            # resp 为 JSON 列表
            try:
                qlist = json.loads(resp)
                st.write("题库预览：")
                for q in qlist:
                    st.markdown(f"- **{q.get('q')}**  答案：{q.get('a')}")
                out = GENERATED_DIR / f"{knowledge_point}_qbank.json"
                out.write_text(json.dumps(qlist, ensure_ascii=False, indent=2), encoding="utf-8")
                st.success(f"题库已保存：{out}")
            except Exception:
                st.text(resp)
        elif rtype == "code":
            out = GENERATED_DIR / f"{knowledge_point}_example.py"
            out.write_text(resp, encoding="utf-8")
            st.code(resp, language="python")
            st.success(f"代码示例已保存：{out}")
        elif rtype == "video_script":
            out = GENERATED_DIR / f"{knowledge_point}_script.md"
            out.write_text(resp, encoding="utf-8")
            st.markdown(resp)
            st.success(f"视频脚本已保存：{out}")


def render_path_page(ai: BaseAIClient):
    st.header("个性化学习路径")
    st.write("基于学生画像的简单学习路径规划示例。")

    profile = st.session_state.get("profile")
    if not profile:
        st.info("请先在左侧的“画像构建”页面生成或输入学生画像。")
        return

    # 简单示例：根据弱点生成三步学习路径
    weak = profile.get("weak_points", "基础")
    steps = [
        {"step": 1, "title": f"复习{weak}基础", "detail": "阅读教材 + 观看视频"},
        {"step": 2, "title": "做练习题", "detail": "完成题库中的 10 道题"},
        {"step": 3, "title": "实战项目", "detail": "实现小型模型并写报告"},
    ]

    # Markdown 表格
    md = "| 步骤 | 标题 | 说明 |\n|---|---|---|\n"
    for s in steps:
        md += f"| {s['step']} | {s['title']} | {s['detail']} |\n"

    st.markdown(md)
    st.write("详细步骤：")
    for s in steps:
        st.markdown(f"**步骤 {s['step']}：{s['title']}**\n{s['detail']}")


def render_tutor_page(ai: BaseAIClient):
    st.header("智能辅导")
    st.write("输入问题，AI 返回模拟解答（支持流式展示）。")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    q = st.text_input("提问：", key="tutor_input")
    if st.button("提问", key="ask_button") and q:
        st.session_state.chat_history.append({"role": "user", "text": q})
        placeholder = st.empty()
        with placeholder.container():
            st.markdown("**AI 正在生成回复...**")
        # 模拟流式输出
        resp = ai.generate(q, mode="answer")
        out_box = st.empty()
        text_so_far = ""
        for chunk in resp.split("\n"):
            text_so_far += chunk + "\n"
            out_box.markdown(text_so_far)
            time.sleep(0.12)

        st.session_state.chat_history.append({"role": "ai", "text": resp})

    if st.session_state.chat_history:
        st.subheader("对话历史")
        for msg in st.session_state.chat_history[::-1]:
            if msg["role"] == "user":
                st.markdown(f"**学生：** {msg['text']}")
            else:
                st.markdown(f"**AI：** {msg['text']}")


def main():
    st.set_page_config(page_title="个性化学习智能体", layout="wide")

    ai = MockClient()

    page = sidebar_nav()
    if page == "画像构建":
        render_profile_page(ai)
    elif page == "多模态资源生成":
        render_resource_page(ai)
    elif page == "个性化学习路径":
        render_path_page(ai)
    elif page == "智能辅导":
        render_tutor_page(ai)


if __name__ == "__main__":
    main()
