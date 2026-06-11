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
    with st.sidebar:
        st.markdown("""
            <style>
                .sidebar-title {
                    font-size: 24px;
                    font-weight: bold;
                    color: #1e88e5;
                    margin-bottom: 20px;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                .nav-button {
                    display: block;
                    width: 100%;
                    padding: 12px 16px;
                    margin: 8px 0;
                    text-align: left;
                    border-radius: 10px;
                    border: none;
                    cursor: pointer;
                    font-size: 15px;
                    transition: all 0.3s ease;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .nav-button:hover {
                    transform: translateX(5px);
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                }
            </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-title">📚 个性化学习智能体</div>', unsafe_allow_html=True)
        
        pages = ["画像构建", "多模态资源生成", "个性化学习路径", "智能辅导"]
        icons = ["👤", "📦", "🗺️", "💬"]
        
        selected_page = st.session_state.get('selected_page', pages[0])
        
        for page, icon in zip(pages, icons):
            if st.button(f"{icon} {page}", key=f"nav_{page}", use_container_width=True):
                st.session_state.selected_page = page
                st.rerun()
        
        return st.session_state.get('selected_page', pages[0])


def _is_error_payload(value: object) -> bool:
    """Return True when the agent returned the structured error dict from
    :mod:`src.api.openai_client` instead of real content.
    """
    return isinstance(value, dict) and value.get("_ai_error") is True


def get_runtime_objects():
    """从 session_state 获取或创建 ai、scheduler、db 等运行时对象。

    The AI client returned by :func:`get_ai_client` is always the real one
    backed by ``OPENAI_API_KEY`` / ``OPENAI_API_URL`` from ``config/.env``.
    If those are missing or the remote is unreachable, API calls produce
    ``[AI错误: ...]`` text or ``{"_ai_error": True, ...}`` dict payloads
    instead of silently emitting sample content.
    """
    if "ai" not in st.session_state:
        st.session_state.ai = get_ai_client()
        client = st.session_state.ai
        configured = bool(getattr(client, "api_key", "")) and bool(
            getattr(client, "api_url", "")
        )
        if configured:
            st.info(
                f"已初始化 AI 客户端: URL={getattr(client, 'api_url', '')}, "
                f"Model={getattr(client, 'model', '')}"
            )
        else:
            st.warning(
                "未检测到 OPENAI_API_KEY/OPENAI_API_URL。所有 AI 调用将返回连接错误，"
                "请编辑 config/.env 后重试。"
            )

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
    
    st.markdown("""
        <style>
            .profile-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                border-radius: 15px;
                color: white;
                margin-bottom: 20px;
            }
            .card {
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                padding: 20px;
                margin-bottom: 20px;
            }
            .btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 10px 24px;
                border-radius: 8px;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="profile-header"><h1>👤 学习画像构建</h1><p>通过对话输入学生信息，系统将调用多智能体生成个性化学习画像并保存到数据库。</p></div>', unsafe_allow_html=True)

    if "conv" not in st.session_state:
        st.session_state.conv = []
    if "profile" not in st.session_state:
        st.session_state.profile = None

    with st.container():
        user_input = st.text_input(
            "", 
            placeholder="与学生对话（例如：我是一名计算机专业大二学生，想学机器学习）", 
            key="profile_input",
            label_visibility="collapsed"
        )
        col1, col2 = st.columns([4, 1])
        with col2:
            send_btn = st.button("发送", key="send_profile", use_container_width=True)
        # 仅在点击发送且有输入时发送请求，避免初次渲染就显示错误信息
        if send_btn:
            if not user_input:
                st.warning("请输入学生信息后再发送。")
            else:
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
            st.markdown('<div class="card"><h3>📊 学生画像（结构化展示）</h3>', unsafe_allow_html=True)
            if _is_error_payload(profile_obj):
                st.error(
                    f"画像生成失败 [{profile_obj.get('error_kind', 'unknown')}]: "
                    f"{profile_obj.get('detail', profile_obj)}"
                )
                st.markdown('</div>', unsafe_allow_html=True)
                return
            try:
                if isinstance(profile_obj, dict):
                    cols = st.columns(2)
                    idx = 0
                    for k, v in profile_obj.items():
                        with cols[idx % 2]:
                            st.markdown(f"**{k}:**")
                            if isinstance(v, (dict, list)):
                                with st.expander("查看详情"):
                                    st.json(v)
                            else:
                                st.markdown(f"{v}")
                        idx += 1
                else:
                    st.json(profile_obj)
            except Exception:
                st.markdown(str(profile_obj))
            st.markdown('</div>', unsafe_allow_html=True)

        render_profile_card(profile)



def render_resource_page():
    ai, scheduler, db = get_runtime_objects()
    
    st.markdown("""
        <style>
            .resource-header {
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                padding: 20px;
                border-radius: 15px;
                color: white;
                margin-bottom: 20px;
            }
            .input-group {
                margin-bottom: 15px;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="resource-header"><h1>📦 多模态资源生成</h1><p>选择课程、知识点和资源类型，调用多智能体实时生成并预览资源。</p></div>', unsafe_allow_html=True)

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            course = st.text_input("课程名称", placeholder="例如：人工智能导论", value="")
        with col2:
            knowledge_point = st.text_input("知识点", placeholder="例如：神经网络基础", value="")
        
        rtype = st.selectbox("资源类型", ["document", "mindmap", "question_bank", "code", "reading_material"], index=0,
                             format_func=lambda x: {"document": "教学文档", "mindmap": "思维导图", "question_bank": "题库", "code": "代码示例", "reading_material": "拓展阅读"}[x])

        if st.button("🚀 生成资源", use_container_width=True):
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
                    st.error("资源生成失败或返回为空。请检查 config/.env 中的 OPENAI_API_KEY / OPENAI_API_URL 并重试。")
                elif _is_error_payload(resources):
                    st.error(
                        f"资源生成失败 [{resources.get('error_kind', 'unknown')}]: "
                        f"{resources.get('detail', resources)}"
                    )
                else:
                    st.markdown('<div class="card"><h3>🎯 生成结果</h3>', unsafe_allow_html=True)
                    content = resources.get(rtype) if isinstance(resources, dict) else None
                    if _is_error_payload(content):
                        st.error(
                            f"{rtype} 生成失败 [{content.get('error_kind', 'unknown')}]: "
                            f"{content.get('detail', content)}"
                        )
                        st.markdown('</div>', unsafe_allow_html=True)
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
                        return
                    if content is None:
                        st.info("未找到指定类型，展示完整生成结果：")
                        st.json(resources)
                    elif isinstance(content, str) and content.startswith("[AI错误]"):
                        # Plain-text error from generate_text() — surface it clearly
                        st.error(f"{rtype} 生成失败: {content}")
                    else:
                        # 专门处理 mindmap：如果是结构化 dict，则渲染为图片并预览
                        if rtype == "mindmap":
                            try:
                                rg = ResourceGenerator(work_dir=str(GENERATED_DIR))
                                # 允许用户自定义文件名（默认以知识点命名）
                                default_name = f"{knowledge_point}_mindmap.png"
                                fn_input = st.text_input("导出文件名（含 .png）：", value=default_name)

                                # 解析并渲染结构化内容，支持 JSON 字符串或 dict
                                parsed = None
                                if isinstance(content, str):
                                    import json as _json
                                    try:
                                        parsed = _json.loads(content)
                                    except Exception:
                                        parsed = None
                                elif isinstance(content, dict):
                                    parsed = content

                                if parsed and isinstance(parsed, dict):
                                    # 确保文件名以 .png 结尾
                                    out_name = fn_input if fn_input.endswith('.png') else fn_input + '.png'
                                    rendered = rg.render_mindmap(parsed, output_name=out_name, format='png', size='12,8', dpi=200)
                                    # 展示更大的图片（宽度翻倍）
                                    try:
                                        st.image(rendered, width=1200)
                                    except Exception:
                                        st.image(rendered)

                                    # 添加下载按钮：读取文件二进制并提供下载
                                    try:
                                        with open(rendered, 'rb') as _f:
                                            data = _f.read()
                                        st.download_button("⬇️ 下载 PNG", data=data, file_name=os.path.basename(out_name), mime="image/png")
                                    except Exception as e:
                                        st.warning(f"无法提供下载：{e}")
                                else:
                                    # 非结构化内容回退为文本/JSON 展示
                                    if isinstance(content, (dict, list)):
                                        st.json(content)
                                    else:
                                        st.markdown(str(content))
                            except Exception as e:
                                st.error(f"思维导图渲染失败: {e}")
                                if isinstance(content, (dict, list)):
                                    st.json(content)
                                else:
                                    st.markdown(str(content))
                        else:
                            # 专门处理题库：支持结构化列表，每题包含 q、a、explanation；答案默认隐藏，点击查看
                            if rtype == "question_bank":
                                parsed = None
                                if isinstance(content, str):
                                    try:
                                        parsed = json.loads(content)
                                    except Exception:
                                        parsed = None
                                elif isinstance(content, list):
                                    parsed = content

                                if isinstance(parsed, list):
                                    for idx, item in enumerate(parsed):
                                        try:
                                            qtext = item.get("q") if isinstance(item, dict) else str(item)
                                        except Exception:
                                            qtext = str(item)
                                        st.markdown(f"**{idx+1}. {qtext}**")
                                        with st.expander("查看答案与解析"):
                                            if isinstance(item, dict):
                                                ans = item.get("a") or item.get("answer") or "（未提供答案）"
                                                expl = item.get("explanation") or item.get("解析") or item.get("explain") or "（未提供详细解析）"
                                                # 使用 Markdown 渲染答案与详解，确保可读性
                                                st.markdown(f"**答案：**\n\n{ans}")
                                                st.markdown(f"**详解：**\n\n{expl}")
                                            else:
                                                st.markdown(str(item))
                                else:
                                    # 非结构化回退为文本展示，保持答案隐藏提示
                                    st.markdown("无法解析为结构化题库，显示原始内容：")
                                    st.markdown(str(content))
                            elif rtype == "reading_material":
                                parsed = None
                                if isinstance(content, str):
                                    try:
                                        parsed = json.loads(content)
                                    except Exception:
                                        parsed = None
                                elif isinstance(content, list):
                                    parsed = content

                                if isinstance(parsed, list):
                                    # 按 order 排序，缺失 order 的放后面
                                    try:
                                        parsed_sorted = sorted(parsed, key=lambda x: (x.get("order") if isinstance(x, dict) and x.get("order") is not None else 9999))
                                    except Exception:
                                        parsed_sorted = parsed

                                    for item in parsed_sorted:
                                        if isinstance(item, dict):
                                            title = item.get("title", "未命名资源")
                                            rtype_txt = item.get("type", "")
                                            summary = item.get("summary", "")
                                            difficulty = item.get("difficulty", "")
                                            link = item.get("link", "")
                                            order = item.get("order", None)
                                            recommended_for = item.get("recommended_for", "")
                                            why = item.get("why_recommend", "")
                                            est = item.get("estimated_time", "")

                                            # 卡片式渲染，突出标题与关键字段
                                            header = f"**{order}. {title}**" if order else f"**{title}**"
                                            st.markdown(header)
                                            meta = []
                                            if rtype_txt:
                                                meta.append(f"类型：{rtype_txt}")
                                            if difficulty:
                                                meta.append(f"难度：{difficulty}")
                                            if est:
                                                meta.append(f"预计耗时：{est}")
                                            if meta:
                                                st.markdown("- " + "  |  ".join(meta))

                                            if recommended_for:
                                                st.markdown(f"- **适合人群：** {recommended_for}")
                                            if why:
                                                st.markdown(f"- **推荐理由：** {why}")
                                            if summary:
                                                st.markdown(f"- **摘要：** {summary}")
                                            if link:
                                                st.markdown(f"- **链接/DOI：** {link}")
                                            st.markdown('---')
                                        else:
                                            st.markdown(str(item))

                                    # 提供下载按钮导出 JSON
                                    try:
                                        data = json.dumps(parsed_sorted, ensure_ascii=False, indent=2)
                                        st.download_button("⬇️ 下载拓展阅读（JSON）", data=data, file_name=f"{knowledge_point}_reading_material.json", mime="application/json")
                                    except Exception:
                                        pass
                                else:
                                    st.markdown("无法解析为结构化拓展阅读，显示原始内容：")
                                    st.markdown(str(content))
                            else:
                                if isinstance(content, (dict, list)):
                                    st.json(content)
                                else:
                                    st.markdown(content)
                    st.markdown('</div>', unsafe_allow_html=True)

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
    
    st.markdown("""
        <style>
            .path-header {
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                padding: 20px;
                border-radius: 15px;
                color: white;
                margin-bottom: 20px;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="path-header"><h1>🗺️ 个性化学习路径</h1><p>基于学生画像调用 PathAgent 生成个性化学习路径。</p></div>', unsafe_allow_html=True)

    profile = st.session_state.get("profile")
    if not profile:
        st.markdown('<div class="card"><p style="color: #ff9800; font-weight: 500;">⚠️ 请先在左侧的“画像构建”页面生成或输入学生画像。</p></div>', unsafe_allow_html=True)
        return

    if st.button("🚀 生成学习路径", use_container_width=True):
        with st.spinner("正在生成学习路径..."):
            try:
                plan = scheduler.execute_task("path", profile)
                if not plan:
                    st.error("学习路径生成失败或返回为空。请检查 config/.env 中的 API 配置。")
                elif _is_error_payload(plan):
                    st.error(
                        f"学习路径生成失败 [{plan.get('error_kind', 'unknown')}]: "
                        f"{plan.get('detail', plan)}"
                    )
                else:
                    st.markdown('<div class="card"><h3>📝 生成的学习路径</h3>', unsafe_allow_html=True)
                    # 动态生成学习路径文本
                    if isinstance(plan, dict):
                        plan_text = plan.get("plan_text", str(plan))
                    else:
                        plan_text = str(plan)
                    st.markdown(plan_text)
                    st.markdown('</div>', unsafe_allow_html=True)
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
    
    st.markdown("""
        <style>
            .tutor-header {
                background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
                padding: 20px;
                border-radius: 15px;
                color: white;
                margin-bottom: 20px;
            }
            .chat-container {
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.08);
                padding: 12px 16px;
                /* 缩小初始占位，避免无用的大白块 */
                min-height: 40px;
                margin-top: 8px;
                max-height: calc(100vh - 220px);
                overflow-y: auto;
            }
            .user-message {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 20px;
                border-radius: 15px 15px 5px 15px;
                margin-bottom: 15px;
                max-width: 70%;
                margin-left: auto;
                box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
                font-size: 15px;
                line-height: 1.6;
            }
            .ai-message {
                background: #f8f9fa;
                color: #333;
                padding: 15px 20px;
                border-radius: 15px 15px 15px 5px;
                margin-bottom: 15px;
                max-width: 70%;
                border: 1px solid #e9ecef;
                font-size: 15px;
                line-height: 1.6;
                white-space: normal;
            }
            .ai-message .ai-content {
                margin-top: 8px;
                color: #333;
                font-size: 15px;
                line-height: 1.6;
                word-break: break-word;
                overflow-wrap: anywhere;
            }
            /* 统一AI回复中的所有元素字体大小，避免标题过大 */
            .ai-message .ai-content h1,
            .ai-message .ai-content h2,
            .ai-message .ai-content h3,
            .ai-message .ai-content h4,
            .ai-message .ai-content h5,
            .ai-message .ai-content h6 {
                font-size: 15px !important;
                font-weight: 600;
                margin: 8px 0;
                color: #333;
            }
            .ai-message .ai-content p {
                font-size: 15px;
                margin: 6px 0;
            }
            .ai-message .ai-content ul,
            .ai-message .ai-content ol {
                font-size: 15px;
                padding-left: 20px;
                margin: 6px 0;
            }
            .ai-message .ai-content li {
                font-size: 15px;
                margin: 4px 0;
            }
            .ai-message .ai-content pre {
                background: #2d2d2d;
                color: #f8f8f2;
                padding: 10px;
                border-radius: 8px;
                overflow: auto;
                font-size: 13px;
            }
            .ai-message .ai-content code {
                background: #f5f5f5;
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 13px;
            }
            .ai-message .ai-content blockquote {
                border-left: 4px solid #eee;
                padding-left: 12px;
                color: #666;
                margin: 8px 0;
                font-size: 15px;
            }
            .ai-message, .user-message { display: inline-block; }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="tutor-header"><h1>💬 智能辅导</h1><p>输入问题，使用 TutoringAgent 进行实时问答。</p></div>', unsafe_allow_html=True)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 使用表单实现按回车键发送
    with st.form(key="tutor_form"):
        col1, col2 = st.columns([4, 1])
        with col1:
            q = st.text_input("", placeholder="输入你的问题...", key="tutor_input", label_visibility="collapsed")
        with col2:
            submit_button = st.form_submit_button(label="发送", use_container_width=True)

    if submit_button and q:
        st.session_state.chat_history.append({"role": "user", "text": q})
        with st.spinner("🤖 AI 正在生成回复..."):
            try:
                resp = scheduler.execute_task("tutoring", q)
                # Structured error payload from the real API client → red banner
                if isinstance(resp, dict) and resp.get("_ai_error") is True:
                    st.error(
                        f"AI 调用失败 [{resp.get('error_kind', 'unknown')}]: "
                        f"{resp.get('detail', resp)}"
                    )
                    st.rerun()
                # 如果是 dict 且包含 answer 字段，提取并作为 Markdown 文本渲染；否则按字符串处理
                if isinstance(resp, dict) and "answer" in resp:
                    text = resp.get("answer")
                else:
                    text = resp if isinstance(resp, str) else json.dumps(resp, ensure_ascii=False)
            except Exception as e:
                text = f"回答生成失败: {str(e)}"
            st.session_state.chat_history.append({"role": "ai", "text": text})
        st.rerun()

    # 仅在有历史消息时渲染白色聊天容器，避免空白占位
    if st.session_state.chat_history:
        st.markdown('<div class="chat-container" id="chat-container">', unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="user-message"><strong>👤 学生：</strong> {msg["text"]}</div>', unsafe_allow_html=True)
            else:
                # 将 AI 的 Markdown 文本转换为 HTML 并整体放入消息气泡内，保证样式一致且支持代码/列表
                try:
                    import markdown as _md
                    html = _md.markdown(msg["text"], extensions=["fenced_code", "codehilite", "tables"]) if isinstance(msg["text"], str) else str(msg["text"])
                    st.markdown(f'<div class="ai-message"><strong>🤖 AI：</strong><div class="ai-content">{html}</div></div>', unsafe_allow_html=True)
                except Exception:
                    st.markdown(f'<div class="ai-message"><strong>🤖 AI：</strong> {msg["text"]}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)



def main():
    st.set_page_config(page_title="个性化学习智能体", layout="wide", initial_sidebar_state="expanded")
    
    # 添加全局样式
    st.markdown("""
        <style>
            * {
                font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
            }
            .stApp {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                min-height: 100vh;
            }
            .stSidebar {
                background: white;
                box-shadow: 2px 0 20px rgba(0,0,0,0.05);
            }
            .stButton>button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            .stButton>button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }
            .stTextInput>div>div>input {
                border-radius: 10px;
                padding: 12px 16px;
                border: 2px solid #e9ecef;
                transition: all 0.3s ease;
            }
            .stTextInput>div>div>input:focus {
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            .stSelectbox>div>div>select {
                border-radius: 10px;
                padding: 12px 16px;
                border: 2px solid #e9ecef;
            }
        </style>
    """, unsafe_allow_html=True)
    
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