# 个性化学习智能体（本地/远端 OpenAI 兼容后端）

这是一个高校级别的个性化学习智能体原型，基于 Python + Streamlit，结合可替换的 OpenAI 兼容客户端实现，用于快速试验多智能体调度、资源生成与交互式教学演示。

关键点
- 前端入口：`src/frontend/app.py`
- OpenAI 兼容客户端：`src/api/openai_client.py`
- AI 客户端抽象：`src/api/base.py`（`BaseAIClient`）
- 配置示例：`config/.env`

核心功能
- 学生画像构建（对话式）
- 多模态资源生成（教学文档、思维导图、题库、代码示例、拓展阅读）
- 个性化学习路径与推荐
- 基于 Streamlit 的交互式辅导界面

快速开始（本机）

1. 克隆仓库并进入项目根目录

2. 推荐：创建并激活虚拟环境

```bash
python -m venv .venv
source .venv/bin/activate
```

3. 安装依赖

```bash
pip install -r requirements.txt
```

可选的系统包（Ubuntu/Debian）：

```bash
sudo apt-get install -y graphviz
```

4. 配置 OpenAI 兼容 API（在 `config/.env` 设置）

示例内容：

```
OPENAI_API_KEY=<你的 API Key 或 Bearer Token>
OPENAI_MODEL=<模型名，例如 gpt-3.5-turbo 或 服务端支持的模型>
OPENAI_API_URL=https://api.openai.com/v1/chat/completions
```

5. 启动 Streamlit 前端

```bash
streamlit run src/frontend/app.py --server.port 8501
```

访问 http://localhost:8501 查看演示界面。

运行测试

```bash
pytest -q
```

项目结构说明（高层）
- `src/frontend/app.py` — Streamlit 前端，负责界面、会话态与运行时对象初始化。
- `src/api/openai_client.py` — OpenAI 兼容客户端实现；对外提供 `generate_text`、`generate_mindmap`、`generate_questions` 等方法。
- `src/api/base.py` — `BaseAIClient` 抽象类，定义客户端需要实现的方法。
- `src/agents/` — 多智能体调度与具体 agent 实现（画像、资源生成等）。
- `src/core/` — 核心组件（数据库、资源渲染等）。
- `config/.env` — 运行时配置（API Key / URL / MODEL 等）。
- `requirements.txt` — 项目依赖。

重点开发说明
- AI 后端替换：项目通过 `BaseAIClient` 为抽象接口。要接入新的后端，实现该抽象并在 `src/api/ai_client.py`（工厂/入口）处替换实例化逻辑。
- 错误处理：`OpenAIClient` 保证所有调用在出错时返回带前缀或结构化错误（例如 `{"_ai_error": True, ...}` 或以 `[AI错误]` 开头的文本），前端据此呈现可理解的提示而非静默数据。

故障排查要点
- 若看到鉴权失败（401/403）：确认 `OPENAI_API_KEY` 与模型权限；可用 `curl` 测试 `OPENAI_API_URL`。
- 若前端报网络不可达：确认能从当前主机访问 `OPENAI_API_URL`，并检查代理/防火墙设置。
- 若依赖报错：确认虚拟环境已激活且已运行 `pip install -r requirements.txt`。

推荐操作
- 若只是调试 API 连接，可使用项目根脚本 `diagnose_api.py` 来快速验证 `config/.env` 中的配置并做基本诊断。
- 开发过程中建议在 `src/api/` 下新增或替换客户端实现并编写对应的单元测试以保证兼容性。
