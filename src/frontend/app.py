from __future__ import annotations

# 路径修复：确保从仓库根目录导入 src 包
import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

import json
from typing import Any, Optional

import streamlit as st

from src.api.ai_client import get_ai_client

from src.agents.multi_agent_scheduler import MultiAgentScheduler
from src.core.database import Database
from src.core.resource_generator import ResourceGenerator

# 数据目录（用于保存生成文件）
BASE_DIR = root_dir
DATA_DIR = BASE_DIR / "data"
GENERATED_DIR = DATA_DIR / "generated"
DATA_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def sidebar_nav() -> str:
    st.sidebar.title("导航")
    return st.sidebar.radio("选择页面", [
        "画像构建",
        "多模态资源生成",
        "个性化学习路径",
        "智能辅导",
    ])


def get_runtime_objects():
    """从 session_state 获取或创建 ai、scheduler、db 等运行时对象"""
    if "ai" not in st.session_state:
        st.session_state.ai = get_ai_client()

    if "scheduler" not in st.session_state:
        st.session_state.scheduler = MultiAgentScheduler(st.session_state.ai)
    if "db" not in st.session_state:
        db = Database()
        db.create_tables()
        # 兼容：确保存在 save_profile 方法（前端按要求调用 db.save_profile）
        if not hasattr(db, "save_profile"):
            def _save_profile(user_id: str, features: list, extra: dict = None):
                return db.add_student_profile(user_id=user_id, features=features, extra=extra)
            db.save_profile = _save_profile
        st.session_state.db = db
    return st.session_state.ai, st.session_state.scheduler, st.session_state.db



def render_profile_page():
    ai, scheduler, db = get_runtime_objects()
    st.header("学习画像构建")
    st.write("通过对话输入学生信息，系统将调用多智能体生成个性化学习画像并保存到数据库。")

    if "conv" not in st.session_state:
        st.session_state.conv = []
    if "profile" not in st.session_state:
        st.session_state.profile = None

    user_input = st.text_input("与学生对话（例如：我是一名计算机专业大二学生，想学机器学习）", value="", key="profile_input")
    if st.button("发送", key="send_profile") and user_input:
        st.session_state.conv.append({"role": "user", "text": user_input})
        with st.spinner("正在生成画像..."):
            try:
                # 通过统一接口调用多智能体生成画像（动态，不使用硬编码）
                profile = scheduler.execute_task("profile", user_input)
            except Exception as e:
                profile = {"error": f"画像生成失败: {str(e)}"}
            st.session_state.profile = profile

            # 画像生成后保存到数据库：优先调用 db.save_profile
            try:
                user_id = f"user_{abs(hash(user_input)) % 100000}"
                features: Optional[list] = []
                # 尝试从画像字段中提取特征
                if isinstance(profile, dict):
                    # 为了演示，我们将知识水平转换为数值特征
                    if profile.get("knowledge_level") == "基础薄弱":
                        features.append(0)
                    elif profile.get("knowledge_level") == "中等":
                        features.append(1)
                    elif profile.get("knowledge_level") == "基础扎实":
                        features.append(2)
                    # 添加其他特征
                    features.append(len(profile.get("weak_points", [])))
                    features.append(len(profile.get("learning_suggestions", [])))
                try:
                    db.save_profile(user_id=user_id, features=features, extra=profile)
                except Exception:
                    if hasattr(db, "add_student_profile"):
                        db.add_student_profile(user_id=user_id, features=features, extra=profile)
            except Exception:
                pass

    if st.session_state.profile:
        profile = st.session_state.profile
        def render_profile_card(profile_obj):
            st.subheader("学生画像（结构化展示）")
            # 如果是字典，展示为表格 + 可展开详情
            try:
                if isinstance(profile_obj, dict):
                    # 构建表格数据：字段 + 值（字符串化）
                    rows = []
                    for k, v in profile_obj.items():
                        try:
                            # 尝试更友好地展示列表/字典
                            if isinstance(v, (dict, list)):
                                val = f"(complex) {type(v).__name__}"
                            else:
                                val = str(v)
                        except Exception:
                            val = str(v)
                        rows.append({"field": k, "value": val})

                    st.table(rows)

                    # 对复杂字段提供可展开查看
                    for k, v in profile_obj.items():
                        if isinstance(v, (dict, list)):
                            with st.expander(f"{k} 详情"):
                                st.json(v)
                else:
                    # 列表或其他类型，直接显示
                    st.json(profile_obj)
            except Exception:
                st.markdown(str(profile_obj))

        render_profile_card(profile)



def render_resource_page():
    ai, scheduler, db = get_runtime_objects()
    st.header("多模态资源生成")
    st.write("选择课程、知识点和资源类型，调用多智能体实时生成并预览资源。")

    course = st.text_input("课程", value="")
    knowledge_point = st.text_input("知识点", value="")
    rtype = st.selectbox("资源类型", ["document", "mindmap", "question_bank", "code", "video_script"], index=0)

    if st.button("生成资源"):
        if not course or not knowledge_point:
            st.warning("请填写课程和知识点以生成资源。")
        else:
            with st.spinner("正在生成资源..."):
                try:
                    payload = {"course": course, "kp": knowledge_point, "rtype": rtype}
                    # 动态调用多智能体生成资源（禁止硬编码）
                    resources = scheduler.execute_task("resource", payload)
                except Exception as e:
                    resources = {"error": f"资源生成失败: {str(e)}"}

            if not resources:
                st.error("资源生成失败或返回为空")
            else:
                content = resources.get(rtype) if isinstance(resources, dict) else None
                if content is None:
                    st.info("未找到指定类型，展示完整生成结果：")
                    st.json(resources)
                else:
                    if isinstance(content, (dict, list)):
                        st.json(content)
                    else:
                        st.markdown(content)

                # 持久化生成的资源到 DB
                try:
                    user_id = f"user_{abs(hash(course + knowledge_point)) % 100000}"
                    if isinstance(resources, dict):
                        for k, v in resources.items():
                            rid = f"{knowledge_point}_{k}"
                            content_text = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
                            if hasattr(db, "add_resource"):
                                db.add_resource(user_id=user_id, resource_id=rid, resource_type=k, content=content_text, metadata={"course": course, "kp": knowledge_point})
                except Exception:
                    pass



def render_path_page():
    ai, scheduler, db = get_runtime_objects()
    st.header("个性化学习路径")
    st.write("基于学生画像调用 PathAgent 生成个性化学习路径。")

    profile = st.session_state.get("profile")
    if not profile:
        st.info("请先在左侧的“画像构建”页面生成或输入学生画像。")
        return

    if st.button("生成学习路径"):
        with st.spinner("正在生成学习路径..."):
            try:
                plan = scheduler.execute_task("path", profile)
                if not plan:
                    st.error("学习路径生成失败或返回为空")
                else:
                    # 动态生成学习路径文本
                    if isinstance(plan, dict):
                        plan_text = plan.get("plan_text", str(plan))
                    else:
                        plan_text = str(plan)
                    st.markdown("**生成的学习路径**")
                    st.markdown(plan_text)
                    try:
                        user_id = f"user_{abs(hash(json.dumps(profile, ensure_ascii=False))) % 100000}"
                        if hasattr(db, "add_learning_step"):
                            db.add_learning_step(user_id=user_id, step=1, progress=0.0, details=plan_text)
                    except Exception:
                        pass
            except Exception as e:
                st.error(f"生成学习路径失败: {str(e)}")



def render_tutor_page():
    ai, scheduler, db = get_runtime_objects()
    st.header("智能辅导")
    st.write("输入问题，使用 TutoringAgent 进行实时问答。")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 使用表单实现按回车键发送
    with st.form(key="tutor_form"):
        q = st.text_input("提问：", key="tutor_input")
        submit_button = st.form_submit_button(label="提问")

    if submit_button and q:
        st.session_state.chat_history.append({"role": "user", "text": q})
        with st.spinner("AI 正在生成回复..."):
            try:
                resp = scheduler.execute_task("tutoring", q)
                text = resp if isinstance(resp, str) else json.dumps(resp, ensure_ascii=False)
            except Exception as e:
                text = f"回答生成失败: {str(e)}"
            st.session_state.chat_history.append({"role": "ai", "text": text})

    if st.session_state.chat_history:
        st.subheader("对话历史")
        # 使用容器和卡片样式显示对话历史
        for msg in st.session_state.chat_history[::-1]:
            if msg["role"] == "user":
                with st.container():
                    st.markdown("""<div style="background-color: #f0f8ff; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                        <p style="font-weight: bold; margin-bottom: 5px;">学生：</p>
                        <p style="margin-left: 20px;">{}</p>
                    </div>""".format(msg['text']), unsafe_allow_html=True)
            else:
                with st.container():
                    st.markdown("""<div style="background-color: #f8f9fa; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                        <p style="font-weight: bold; margin-bottom: 5px;">AI：</p>
                        <div style="margin-left: 20px;">{}</div>
                    </div>""".format(msg['text']), unsafe_allow_html=True)



def main():
    st.set_page_config(page_title="个性化学习智能体", layout="wide")
    page = sidebar_nav()
    if page == "画像构建":
        render_profile_page()
    elif page == "多模态资源生成":
        render_resource_page()
    elif page == "个性化学习路径":
        render_path_page()
    elif page == "智能辅导":
        render_tutor_page()


if __name__ == "__main__":
    main()