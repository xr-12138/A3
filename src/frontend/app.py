from __future__ import annotations

import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(root_dir))

import json, os, time
from typing import Any, Optional

import streamlit as st

from src.api.ai_client import get_ai_client
from src.agents.multi_agent_scheduler import MultiAgentScheduler
from src.core.database import Database
from src.core.resource_generator import ResourceGenerator
from src.core.knowledge_base import get_knowledge_base, list_courses

BASE_DIR = root_dir
DATA_DIR = BASE_DIR / "data"
GENERATED_DIR = DATA_DIR / "generated"
DATA_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
ENV_PATH = root_dir / "config" / ".env"

# ── env ──

def _read_env() -> dict:
    c = {}
    if not ENV_PATH.exists(): return c
    try:
        with open(ENV_PATH,'r',encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line: continue
                k,_,v = line.partition('=')
                k,v = k.strip(), v.strip().strip('"').strip("'")
                if k: c[k]=v
    except: pass
    return c

def _write_env(cfg: dict) -> None:
    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "", "# API Key", f'OPENAI_API_KEY="{cfg.get("OPENAI_API_KEY","")}"',
        "", "# Model", f'OPENAI_MODEL="{cfg.get("OPENAI_MODEL","")}"',
        "", "# API URL", f'OPENAI_API_URL="{cfg.get("OPENAI_API_URL","")}"', "",
    ]
    with open(ENV_PATH,'w',encoding='utf-8') as f: f.write("\n".join(lines))

# ── CSS ──

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

* { font-family: -apple-system,BlinkMacSystemFont,'Inter','Segoe UI','PingFang SC',sans-serif; }

/* === GLOBAL === */
.stApp { background: #ffffff; }

/* === SIDEBAR (ChatGPT dark sidebar) === */
section[data-testid="stSidebar"] {
    background: #171717 !important;
}
section[data-testid="stSidebar"] * {
    color: #ececec !important;
}
section[data-testid="stSidebar"] .st-emotion-cache-1cypcdb,
section[data-testid="stSidebar"] .st-emotion-cache-6qob1r,
section[data-testid="stSidebar"] .st-emotion-cache-1v0mbdj {
    background: #171717 !important;
}

/* sidebar labels / headings */
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4 {
    color: #9b9b9b !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 12px 8px 4px 8px !important;
    margin: 0 !important;
}

/* sidebar buttons — MUST override global button styles */
section[data-testid="stSidebar"] button[kind="secondary"],
section[data-testid="stSidebar"] .stButton button[kind="secondary"],
section[data-testid="stSidebar"] button {
    background: transparent !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 400 !important;
    padding: 10px 12px !important;
    text-align: left !important;
    margin: 1px 0 !important;
    width: 100% !important;
    color: #ececec !important;
    transition: background 0.1s !important;
}
section[data-testid="stSidebar"] button[kind="secondary"]:hover,
section[data-testid="stSidebar"] button:hover {
    background: #2a2a2a !important;
}
section[data-testid="stSidebar"] button[kind="secondary"] *,
section[data-testid="stSidebar"] button * {
    color: #ececec !important;
}
/* active nav item */
section[data-testid="stSidebar"] button[kind="primary"],
section[data-testid="stSidebar"] .stButton button[kind="primary"] {
    background: #2a2a2a !important;
}
section[data-testid="stSidebar"] button[kind="primary"] * {
    color: #ffffff !important;
    font-weight: 500 !important;
}

/* sidebar inputs */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea {
    background: #2a2a2a !important;
    border: 1px solid #3e3e3e !important;
    border-radius: 6px !important;
    color: #ececec !important;
    padding: 8px 12px !important;
    font-size: 13px !important;
}
section[data-testid="stSidebar"] input:focus {
    border-color: #555 !important;
}

/* sidebar divider */
section[data-testid="stSidebar"] hr {
    border-color: #2e2e2e !important;
    margin: 12px 0 !important;
}

/* hide deploy banner and decoration only — keep toolbar (contains sidebar toggle) */
[data-testid="stDeployButton"], .stAppDeployButton,
[data-testid="stDecoration"] {
    display: none !important;
}

/* hide toolbar action buttons but keep the sidebar toggle */
[data-testid="stToolbarActions"] {
    display: none !important;
}

/* sidebar collapse/expand arrow & collapsed-state toggle — always visible */
section[data-testid="stSidebar"] button[kind="headerNoPadding"],
button[data-testid="baseButton-headerNoPadding"],
[data-testid="collapsedControl"] {
    display: inline-flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    color: #9b9b9b !important;
}

/* === MAIN CONTENT === */
.block-container {
    max-width: 768px !important;
    padding: 48px 24px 0 24px !important;
}
.main {
    background: #ffffff !important;
}

/* Headings */
h2 {
    font-size: 20px !important;
    font-weight: 600 !important;
    color: #1a1a1a !important;
    margin-bottom: 4px !important;
}
h3 {
    font-size: 16px !important;
    font-weight: 600 !important;
    color: #1a1a1a !important;
}
p, .stCaption, [data-testid="stCaptionContainer"] {
    color: #6b6b6b !important;
    font-size: 14px !important;
}

/* === BUTTONS (main area) === */
button[kind="secondary"], .stButton > button[kind="secondary"] {
    background: #f4f4f4 !important;
    color: #1b1b1b !important;
    border: 1px solid #e5e5e5 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 20px !important;
}
button[kind="secondary"]:hover {
    background: #e8e8e8 !important;
}
button[kind="primary"], .stButton > button[kind="primary"] {
    background: #1b1b1b !important;
    color: #ffffff !important;
    border: 1px solid #1b1b1b !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 20px !important;
}
button[kind="primary"]:hover {
    background: #333333 !important;
}

/* === INPUTS (main area) === */
input, textarea {
    background: #f4f4f4 !important;
    border: 1px solid #e5e5e5 !important;
    border-radius: 26px !important;
    padding: 14px 20px !important;
    font-size: 15px !important;
    color: #1b1b1b !important;
    box-shadow: none !important;
}
input:focus, textarea:focus {
    background: #ffffff !important;
    border-color: #d1d1d1 !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
    outline: none !important;
}

/* === CHAT === */
.stChatMessage {
    border-radius: 0 !important;
    padding: 16px 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
    background: transparent !important;
}
[data-testid="stChatMessage"][aria-label*="user"] {
    background: #f7f7f8 !important;
    padding: 20px 24px !important;
    margin: 0 -24px !important;
    border-bottom: 1px solid #ececf1;
    border-top: 1px solid #ececf1;
}
[data-testid="stChatMessage"][aria-label*="assistant"] {
    background: #ffffff !important;
    padding: 20px 0 !important;
    border-bottom: 1px solid #f0f0f0;
}

/* === GREETING (ChatGPT style centered) === */
.greeting {
    text-align: center;
    padding: 60px 20px 20px 20px;
}
.greeting h1 {
    font-size: 28px !important;
    font-weight: 600 !important;
    color: #1b1b1b !important;
    margin-bottom: 8px !important;
}

/* === CARDS === */
.card {
    background: #f7f7f8;
    border: 1px solid #ececf1;
    border-radius: 12px;
    padding: 20px;
    margin: 12px 0;
}
.card h3 { font-size: 16px; font-weight: 600; color: #1b1b1b; margin: 0 0 8px 0; }

/* expander */
[data-testid="stExpander"] {
    border: 1px solid #ececf1 !important;
    border-radius: 8px !important;
    background: #fff !important;
}
[data-testid="stExpander"] summary {
    color: #1b1b1b !important;
    font-size: 14px !important;
}

/* tabs */
.stTabs [data-baseweb="tab"] { font-size: 14px; font-weight: 500; color: #6b6b6b; }
.stTabs [data-baseweb="tab"][aria-selected="true"] { color: #1b1b1b; }

/* select */
.stSelectbox [data-baseweb="select"] > div {
    background: #f4f4f4 !important;
    border: 1px solid #e5e5e5 !important;
    border-radius: 8px !important;
}

/* metrics */
[data-testid="stMetric"] {
    background: #f7f7f8;
    border-radius: 10px;
    padding: 12px;
}
[data-testid="stMetric"] label { color: #6b6b6b !important; font-size: 12px !important; }
[data-testid="stMetricValue"] { color: #1b1b1b !important; font-size: 24px !important; }

/* status row */
.status-row {
    font-size: 12px;
    color: #9b9b9b;
    padding: 4px 0;
}
.status-dot {
    width: 6px; height: 6px; border-radius: 50%; display: inline-block;
    margin-right: 4px;
}
.status-on { background: #10a37f; }
.status-off { background: #ef4444; }

/* settings panel */
.settings-panel {
    background: #f7f7f8;
    border: 1px solid #ececf1;
    border-radius: 12px;
    padding: 24px;
    margin: 12px 0;
}
.settings-panel h3 { font-size: 16px; font-weight: 600; margin: 0 0 16px 0; }

/* divider */
hr { border-color: #ececf1; margin: 16px 0; }

/* spinner text color */
.stSpinner { color: #6b6b6b !important; }
</style>
"""

# ── session management ──

def _init_sessions():
    if "conversations" not in st.session_state:
        st.session_state.conversations = []
    if "active_conversation_id" not in st.session_state:
        st.session_state.active_conversation_id = None

def _gen_cid():
    return f"conv_{int(time.time()*1000000)}"

def _save_current_session():
    history = st.session_state.get("chat_history", [])
    if not history:
        return
    active_id = st.session_state.get("active_conversation_id")
    convs = st.session_state.get("conversations", [])
    if active_id:
        for c in convs:
            if c["id"] == active_id:
                c["messages"] = list(history)
                c["title"] = _session_title(history)
                c["updated_at"] = time.time()
                st.session_state.conversations = convs
                return
    title = _session_title(history)
    new_conv = {
        "id": _gen_cid(),
        "title": title,
        "messages": list(history),
        "created_at": time.time(),
        "updated_at": time.time(),
    }
    convs.insert(0, new_conv)
    st.session_state.active_conversation_id = new_conv["id"]
    st.session_state.conversations = convs

def _session_title(messages):
    for m in messages:
        if m.get("role") == "user":
            t = str(m.get("text", ""))[:40]
            return t if t else "新对话"
    return "新对话"

def _load_session(conv):
    st.session_state.chat_history = list(conv.get("messages", []))
    st.session_state.active_conversation_id = conv["id"]
    st.session_state.selected_page = "智能辅导"
    st.session_state.show_settings = False

def _delete_session(conv_id):
    st.session_state.conversations = [
        c for c in st.session_state.get("conversations", []) if c["id"] != conv_id
    ]
    if st.session_state.get("active_conversation_id") == conv_id:
        st.session_state.active_conversation_id = None
        st.session_state.chat_history = []

def _time_label(ts):
    now = time.time()
    diff = now - ts
    if diff < 86400:
        return "今天"
    elif diff < 172800:
        return "昨天"
    elif diff < 604800:
        return "过去 7 天"
    elif diff < 2592000:
        return "过去 30 天"
    else:
        return "更早"

# ── sidebar ──

def render_sidebar() -> str:
    _init_sessions()

    with st.sidebar:
        if st.button("+ 新建对话", key="new_chat_btn", use_container_width=True):
            _save_current_session()
            st.session_state.chat_history = []
            st.session_state.active_conversation_id = None
            st.session_state.selected_page = "智能辅导"
            st.session_state.show_settings = False
            st.rerun()

        st.markdown('<h4 style="margin-top:20px;">历史</h4>', unsafe_allow_html=True)

        convs = st.session_state.get("conversations", [])
        active_id = st.session_state.get("active_conversation_id")

        # Group conversations by time period (ChatGPT style)
        groups: dict = {}
        for c in convs:
            label = _time_label(c.get("created_at", 0))
            groups.setdefault(label, []).append(c)

        for label in ["今天", "昨天", "过去 7 天", "过去 30 天", "更早"]:
            if label not in groups:
                continue
            st.markdown(
                f'<div style="font-size:11px;color:#9b9b9b;font-weight:600;text-transform:uppercase;'
                f'padding:8px 8px 4px 8px;letter-spacing:0.5px;">{label}</div>',
                unsafe_allow_html=True,
            )
            for c in groups[label]:
                is_active = (c["id"] == active_id)
                title = c.get("title", "新对话")[:30]

                if st.button(
                    title,
                    key=f"conv_{c['id']}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                ):
                    _save_current_session()
                    _load_session(c)
                    st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)

        nav_items = [
            ("nav_profile", "画像构建", "画像构建"),
            ("nav_resource", "资源生成", "多模态资源生成"),
            ("nav_path", "学习路径", "个性化学习路径"),
            ("nav_tutor", "智能辅导", "智能辅导"),
            ("nav_kb", "课程知识库", "课程知识库"),
        ]

        for key, label, full in nav_items:
            is_active = (st.session_state.get("selected_page", nav_items[0][2]) == full)
            if st.button(label, key=key, use_container_width=True,
                         type="primary" if is_active else "secondary"):
                st.session_state.selected_page = full
                st.session_state.show_settings = False
                st.rerun()

        selected = st.session_state.get("selected_page", nav_items[0][2])

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<h4>设置</h4>', unsafe_allow_html=True)

        cfg = _read_env()
        if cfg.get("OPENAI_API_KEY") and cfg.get("OPENAI_API_URL"):
            st.markdown(
                f'<div style="font-size:12px;color:#10a37f;padding:4px 8px;">'
                f'API 已连接 · {cfg.get("OPENAI_MODEL","")}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="font-size:12px;color:#ef4444;padding:4px 8px;">'
                'API 未配置</div>',
                unsafe_allow_html=True,
            )

        # Settings toggle at bottom of sidebar
        show_s = st.session_state.get("show_settings", False)
        if st.button("关闭设置" if show_s else "API 设置", key="sidebar_settings_btn",
                     use_container_width=True):
            st.session_state.show_settings = not show_s
            st.rerun()

        return selected

# ── settings ──

def render_settings():
    st.session_state.show_settings = True
    cfg = _read_env()
    st.markdown('<div class="settings-panel">', unsafe_allow_html=True)
    st.markdown("### 设置")
    col1, col2 = st.columns(2)
    with col1:
        url = st.text_input("API 地址", value=cfg.get("OPENAI_API_URL",""),
                           placeholder="https://api.openai.com/v1/chat/completions", key="u")
    with col2:
        model = st.text_input("模型", value=cfg.get("OPENAI_MODEL",""),
                             placeholder="gpt-3.5-turbo", key="m")
    key = st.text_input("API Key", value=cfg.get("OPENAI_API_KEY",""),
                        type="password", placeholder="sk-...", key="k")
    c1, c2, _ = st.columns([1,1,3])
    with c1:
        if st.button("保存", use_container_width=True, key="save", type="primary"):
            nc = {"OPENAI_API_URL":url,"OPENAI_API_KEY":key,"OPENAI_MODEL":model}
            _write_env(nc)
            for kk,vv in nc.items(): os.environ[kk]=vv
            st.session_state.pop("ai",None); st.session_state.pop("scheduler",None)
            st.session_state.show_settings = False
            st.rerun()
    with c2:
        if st.button("取消", use_container_width=True, key="cancel"):
            st.session_state.show_settings = False
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ── shared ──

def get_cid(): return st.session_state.get("current_course_id")
def get_kb(): return get_knowledge_base(get_cid())
def _err(v): return isinstance(v,dict) and v.get("_ai_error")

def get_runtime():
    if "ai" not in st.session_state: st.session_state.ai = get_ai_client()
    if "scheduler" not in st.session_state: st.session_state.scheduler = MultiAgentScheduler(st.session_state.ai)
    if "db" not in st.session_state:
        db = Database(); db.create_tables()
        if not hasattr(db,"save_profile"):
            db.save_profile = lambda u,fs,e=None: db.add_student_profile(u,fs,e)
        st.session_state.db = db
    return st.session_state.ai, st.session_state.scheduler, st.session_state.db

def top_bar(title: str):
    """ChatGPT-style top bar."""
    show = st.session_state.get("show_settings",False)
    c1, c2 = st.columns([8,1])
    with c1:
        st.markdown(f'<div class="status-row">LearnKit / {title}</div>', unsafe_allow_html=True)
    with c2:
        if st.button("设置" if not show else "关闭", key="ts", use_container_width=False):
            st.session_state.show_settings = not show; st.rerun()

# ── pages ──

def render_profile():
    ai, scheduler, db = get_runtime()

    st.markdown("## 学习画像构建")
    st.caption("描述学生背景，AI 自动生成结构化学习画像。")
    st.markdown("<hr>", unsafe_allow_html=True)

    if "prof_conv" not in st.session_state: st.session_state.prof_conv = []
    if "profile" not in st.session_state: st.session_state.profile = None

    user_input = st.text_area(
        "学生信息",
        placeholder="描述学生背景，例如：计算机专业大二学生，已修 Python 和数据结构，想系统学习机器学习...",
        key="pi", height=100, label_visibility="collapsed",
    )

    c1, c2 = st.columns([1,6])
    with c1:
        if st.button("生成", key="pg", use_container_width=True, type="primary"):
            if not user_input.strip():
                st.warning("请输入信息")
            else:
                st.session_state.prof_conv.append({"role":"user","text":user_input})
                with st.spinner("分析中..."):
                    try:
                        p = scheduler.execute_task("profile", user_input)
                    except Exception as e:
                        p = {"error":str(e)}
                    st.session_state.profile = p
                try:
                    uid = f"u{abs(hash(user_input))%100000}"
                    fs: list = []
                    if isinstance(p,dict):
                        kl = str(p.get("knowledge_level",""))
                        fs.append(0 if "薄弱" in kl else 1 if "中等" in kl else 2)
                        fs.append(len(p.get("weak_points",[])))
                        fs.append(len(p.get("learning_suggestions",[])))
                    db.save_profile(uid,fs,p)
                except: pass

    if st.session_state.profile:
        p = st.session_state.profile
        if _err(p):
            st.error(f"失败: {p.get('detail',p)}")
        elif isinstance(p, dict):
            st.markdown('<div class="card"><h3>分析结果</h3>', unsafe_allow_html=True)
            for title, keys in [
                ("概况",["major","grade","knowledge_level","target_direction"]),
                ("能力",["programming_ability","math_foundation","english_level","learning_style"]),
                ("建议",["weak_points","strength_points","learning_suggestions","recommended_courses"]),
            ]:
                present = [k for k in keys if k in p]
                if present:
                    st.markdown(f"**{title}**")
                    cols = st.columns(min(len(present),3))
                    for i,k in enumerate(present):
                        v = p[k]
                        with cols[i%3]:
                            vs = ", ".join(map(str,v[:5])) if isinstance(v,list) else str(v)
                            st.caption(f"{k}: {vs[:80]}")
                    st.markdown("")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.json(p)


def render_resource():
    ai, scheduler, db = get_runtime()

    st.markdown("## 资源生成")
    st.caption("基于知识库，生成文档、导图、题库、代码等。")
    st.markdown("<hr>", unsafe_allow_html=True)

    kb = get_kb()
    chapters = kb.manifest.get("chapters",[])
    all_kp = [kp for ch in chapters for kp in ch.get("knowledge_points",[])]

    c1, c2, c3 = st.columns([2,2,1])
    with c1:
        course = st.text_input("课程", value=kb.course_name, key="rc", label_visibility="collapsed", placeholder="课程名称")
    with c2:
        kp = st.text_input("知识点", placeholder="例如：二叉树遍历", key="rk", label_visibility="collapsed")
    with c3:
        rtype = st.selectbox("类型", ["document","mindmap","question_bank","code","reading_material"],
                            format_func=lambda x:{"document":"文档","mindmap":"导图","question_bank":"题库",
                                                  "code":"代码","reading_material":"阅读"}[x],
                            key="rt", label_visibility="collapsed")

    if st.button("生成资源", use_container_width=True, key="rg"):
        if not course or not kp:
            st.warning("请填写课程和知识点")
        else:
            with st.spinner("生成中..."):
                try:
                    res = scheduler.execute_task("resource",{"course":course,"kp":kp,"rtype":rtype})
                except Exception as e:
                    res = {"error":str(e)}
            if not res or _err(res):
                st.error(f"失败: {res.get('detail',res) if isinstance(res,dict) else res}")
            else:
                ct = res.get(rtype) if isinstance(res,dict) else None
                st.markdown('<div class="card"><h3>结果</h3>', unsafe_allow_html=True)
                if ct is None:
                    st.json(res)
                elif isinstance(ct,str) and "[AI错误]" in ct:
                    st.error(ct)
                elif rtype == "mindmap":
                    try:
                        rg = ResourceGenerator(work_dir=str(GENERATED_DIR))
                        fn = st.text_input("文件名", value=f"{kp}_mindmap.png", key="mf")
                        parsed = None
                        if isinstance(ct,str):
                            try: parsed = json.loads(ct)
                            except: pass
                        elif isinstance(ct,dict): parsed = ct
                        if parsed and isinstance(parsed,dict):
                            out = fn if fn.endswith('.png') else fn+'.png'
                            rendered = rg.render_mindmap(parsed, output_name=out, format='png', size='12,8', dpi=200)
                            st.image(rendered, width=700)
                            with open(rendered,'rb') as f:
                                st.download_button("下载", data=f.read(), file_name=os.path.basename(out), mime="image/png")
                        else:
                            st.markdown(str(ct))
                    except Exception as e:
                        st.error(f"渲染失败: {e}")
                elif rtype == "question_bank":
                    parsed = None
                    if isinstance(ct,str):
                        try: parsed = json.loads(ct)
                        except: pass
                    elif isinstance(ct,list): parsed = ct
                    if isinstance(parsed,list):
                        for i,item in enumerate(parsed):
                            qt = item.get("q") if isinstance(item,dict) else str(item)
                            st.markdown(f"**{i+1}. {qt}**")
                            with st.expander("答案"):
                                if isinstance(item,dict):
                                    st.markdown(f"**答案**\n\n{item.get('a') or item.get('answer') or '-'}")
                                    st.markdown(f"**解析**\n\n{item.get('explanation') or '-'}")
                    else:
                        st.markdown(str(ct))
                elif rtype == "reading_material":
                    parsed = None
                    if isinstance(ct,str):
                        try: parsed = json.loads(ct)
                        except: pass
                    elif isinstance(ct,list): parsed = ct
                    if isinstance(parsed,list):
                        try: parsed = sorted(parsed, key=lambda x: x.get("order",9999) if isinstance(x,dict) else 9999)
                        except: pass
                        for item in parsed:
                            if isinstance(item,dict):
                                st.markdown(f"**{item.get('title','')}**")
                                st.caption(f"{item.get('type','')} | {item.get('difficulty','')}")
                                if item.get("summary"): st.caption(item["summary"])
                                st.markdown("---")
                        st.download_button("导出 JSON", data=json.dumps(parsed,ensure_ascii=False,indent=2),
                                         file_name=f"{kp}_reading.json", mime="application/json")
                    else:
                        st.markdown(str(ct))
                else:
                    if isinstance(ct,(dict,list)): st.json(ct)
                    else: st.markdown(ct)
                st.markdown("</div>", unsafe_allow_html=True)


def render_path():
    ai, scheduler, db = get_runtime()

    st.markdown("## 学习路径")
    st.caption("基于学生画像，规划个性化路径。")
    st.markdown("<hr>", unsafe_allow_html=True)

    profile = st.session_state.get("profile")
    if not profile:
        st.info("请先在「画像构建」中生成画像。")
        return

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 当前画像")
    if isinstance(profile,dict):
        c1,c2,c3 = st.columns(3)
        c1.metric("知识水平", profile.get("knowledge_level","-"))
        c2.metric("编程能力", profile.get("programming_ability","-"))
        c3.metric("学习风格", profile.get("learning_style","-"))
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("生成学习路径", use_container_width=True, key="pl", type="primary"):
        with st.spinner("分析中..."):
            try:
                plan = scheduler.execute_task("path", profile)
                if not plan or _err(plan):
                    st.error(f"失败: {plan.get('detail',plan) if isinstance(plan,dict) else plan}")
                else:
                    st.markdown('<div class="card"><h3>推荐路径</h3>', unsafe_allow_html=True)
                    pt = plan.get("plan_text",str(plan)) if isinstance(plan,dict) else str(plan)
                    st.markdown(pt)
                    st.markdown("</div>", unsafe_allow_html=True)
                    try:
                        uid = f"u{abs(hash(json.dumps(profile,ensure_ascii=False)))%100000}"
                        if hasattr(db,"add_learning_step"): db.add_learning_step(uid,1,0.0,pt)
                    except: pass
            except Exception as e:
                st.error(f"失败: {e}")


def render_tutor():
    ai, scheduler, db = get_runtime()
    _init_sessions()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Greeting when no messages
    if not st.session_state.chat_history:
        st.markdown(
            '<div class="greeting">'
            '<h1>有什么可以帮助你的？</h1>'
            '<p style="color:#6b6b6b;font-size:15px;">向 AI 辅导助手提问，获取学习建议与知识解答。</p>'
            '</div>',
            unsafe_allow_html=True,
        )

    # Chat messages
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["text"])
        else:
            st.chat_message("assistant").write(msg["text"])

    # Input form
    st.markdown("<br>", unsafe_allow_html=True)
    with st.form(key="tf", clear_on_submit=True):
        col1, col2 = st.columns([10,1])
        with col1:
            q = st.text_input("", placeholder="输入你的问题...", key="ti", label_visibility="collapsed")
        with col2:
            submit = st.form_submit_button("发送", use_container_width=True, type="primary")

    # Disclaimer
    st.caption("LearnKit 可能产生不准确的信息，请以实际教材为准。")

    if submit and q.strip():
        st.session_state.chat_history.append({"role":"user","text":q})
        st.session_state.pending_q = q
        _save_current_session()
        st.rerun()

    if "pending_q" in st.session_state:
        pq = st.session_state.pop("pending_q")
        with st.spinner(""):
            try:
                resp = scheduler.execute_task("tutoring", pq)
                if isinstance(resp,dict) and resp.get("_ai_error"):
                    txt = f"调用失败: {resp.get('detail',resp)}"
                else:
                    txt = resp.get("answer") if isinstance(resp,dict) and "answer" in resp else (
                        resp if isinstance(resp,str) else json.dumps(resp,ensure_ascii=False))
            except Exception as e:
                txt = f"出错: {e}"
            st.session_state.chat_history.append({"role":"ai","text":txt})
            _save_current_session()
        st.rerun()


def render_kb():

    courses = list_courses()
    if not courses:
        st.warning("未发现课程知识库。")
        return

    opts = [(c["id"], f"{c['course_name']} ({c['course_name_en']})") for c in courses]
    di = 0
    if st.session_state.get("current_course_id"):
        for i,c in enumerate(courses):
            if c["id"]==st.session_state["current_course_id"]: di=i; break

    selected = st.selectbox("选择课程", range(len(opts)),
                           format_func=lambda i: opts[i][1], index=di, key="ks")
    st.session_state["current_course_id"] = opts[selected][0]
    kb = get_kb()
    m = kb.manifest

    st.markdown(f"## {m.get('course_name','')}")
    st.caption(f"{m.get('target_major','')}  |  {m.get('total_hours','')} 学时")

    chapters = m.get("chapters",[])
    tkp=tcd=tqs=0
    for ch in chapters:
        d=kb.get_chapter(ch.get("id",""))
        if d: tkp+=len(d.get("key_points",[])); tcd+=len(d.get("code_examples",[])); tqs+=len(d.get("questions",[]))

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("章节", len(chapters))
    c2.metric("知识点", tkp)
    c3.metric("代码", tcd)
    c4.metric("习题", tqs)

    st.markdown("<hr>", unsafe_allow_html=True)

    search = st.text_input("搜索知识点", placeholder="输入关键词检索...", key="kq")
    if search:
        hits = kb.search_knowledge_point(search)
        if hits:
            st.caption(f"找到 {len(hits)} 条结果")
            for h in hits[:15]:
                st.markdown(f"**{h.get('kp_name','')}** — {h.get('chapter_title','')} ({h.get('difficulty','')})")
                st.caption(str(h.get("content",""))[:500])
                st.markdown("---")
        else:
            st.info("未找到相关内容。")
        return

    st.markdown("### 章节详情")
    ch_sel = st.selectbox("选择章节", [(c.get("id",""),c.get("title","")) for c in chapters],
                         format_func=lambda x: f"{x[0]}  {x[1]}", key="kc")
    if ch_sel:
        ch_id, ch_title = ch_sel
        cd = kb.get_chapter(ch_id)
        if not cd: st.info("内容准备中..."); return

        st.markdown(f"**{ch_id}  {ch_title}**")
        st.caption(cd.get("summary",""))

        t1,t2,t3,t4 = st.tabs([
            f"知识点 ({len(cd.get('key_points',[]))})",
            f"代码 ({len(cd.get('code_examples',[]))})",
            f"习题 ({len(cd.get('questions',[]))})",
            f"阅读 ({len(cd.get('reading_materials',[]))})",
        ])
        with t1:
            for kp in cd.get("key_points",[]):
                st.markdown(f"**{kp.get('name','')}** ({kp.get('difficulty','')})")
                st.markdown(kp.get("content","")); st.markdown("---")
        with t2:
            for ex in cd.get("code_examples",[]):
                st.markdown(f"**{ex.get('title','')}** ({ex.get('language','python')})")
                if ex.get("description"): st.caption(ex["description"])
                st.code(ex.get("code",""), language=ex.get("language","python"))
        with t3:
            for i,q in enumerate(cd.get("questions",[]),1):
                qt = q.get("question", q.get("q",""))
                with st.expander(f"Q{i}. {str(qt)[:100]}"):
                    st.markdown(f"**题目**\n\n{qt}")
                    st.markdown(f"**答案**\n\n{q.get('answer',q.get('a',''))}")
        with t4:
            for rm in cd.get("reading_materials",[]):
                st.markdown(f"**{rm.get('title',rm.get('name',''))}** ({rm.get('type','')})")
                st.caption(rm.get("summary",rm.get("desc","")))
                if rm.get("link"): st.caption(rm["link"]); st.markdown("---")

    with st.expander(f"全部 {len(chapters)} 章总览", expanded=False):
        for i,c in enumerate(chapters,1):
            st.markdown(f"**第{i}章  {c.get('title','')}** ({c.get('hours',0)} 学时)")
            st.caption("、".join(c.get("knowledge_points",[])[:6]))
            st.markdown("---")

# ── main ──

def main():
    st.set_page_config(page_title="LearnKit", layout="wide", initial_sidebar_state="expanded")

    page = render_sidebar()

    if st.session_state.get("show_settings"):
        render_settings()
    else:
        pages = {
            "课程知识库": render_kb,
            "画像构建": render_profile,
            "多模态资源生成": render_resource,
            "个性化学习路径": render_path,
            "智能辅导": render_tutor,
        }
        pages.get(page, render_profile)()

    # CSS injected LAST to override Streamlit defaults
    st.markdown(CSS, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
