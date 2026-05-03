# 个性化学习智能体（本地 Ollama 接入）

一个高校级别的个性化学习智能体原型，使用 Python + Streamlit 与本地 Ollama（LLM）进行演示。仓库包含多智能体调度骨架、资源生成器、Streamlit 前端与一组测试用例，便于在本地快速试验和开发。

**要点**
- 前端演示入口：`src/frontend/app.py`
- 本地 LLM 客户端实现：`src/api/ollama_client.py`
- 抽象接口：`src/api/base.py`（`BaseAIClient`），可按需替换后端实现

**主要功能**
- 学生画像构建（对话式）
- 多模态资源生成（文档、思维导图、题库、代码示例等）
- 个性化学习路径生成
- 智能问答辅导（Streamlit 聊天式界面）

**快速启动（重点）**

1) 克隆并进入仓库（假设你已经在项目目录）

2) 创建并激活虚拟环境（推荐）

```bash
python -m venv .venv
source .venv/bin/activate
```

3) 安装 Python 依赖

```bash
pip install -r requirements.txt
```

（可选）若提示缺少依赖或额外工具，再安装：

```bash
pip install streamlit requests python-dotenv graphviz pytest
sudo apt-get install -y graphviz   # Ubuntu/Debian 下用于渲染思维导图
```

4) 配置本地 Ollama（或兼容的 OpenAI 接口）

- 复制或编辑 `config/.env`，设置下面至少三项：

```
XF_API_URL=http://127.0.0.1:11434/v1/chat/completions
XF_MODEL=<本地已安装的模型名，例如 qwen3.5:2b>
XF_API_KEY=<可选，若需认证则填写>
```

（仓库已包含示例 `config/.env`，通常默认配置可直接使用本地 Ollama。）

5) 启动本地 Ollama（若尚未启动）

请按照 Ollama 官方安装说明在本机安装并运行 Ollama 服务，确保监听地址与 `XF_API_URL` 一致。可用 `ollama list` 确认已安装模型。

6) 启动演示界面（Streamlit）

```bash
streamlit run src/frontend/app.py --server.port 8501
```

然后在浏览器访问 http://localhost:8501

7) 运行测试（可选）

```bash
pytest -q
```

**主要文件/入口**
- `src/frontend/app.py`：Streamlit 前端入口
- `src/api/ollama_client.py`：Ollama 客户端实现（实现 `BaseAIClient`）
- `src/api/base.py`：AI 客户端抽象接口
- `config/.env`：运行时配置示例

**常见问题与排查**
- 如果前端显示“模型未找到”：运行 `ollama list`，确认 `XF_MODEL` 与已安装模型一致。
- 如果前端无法连接：确认 `XF_API_URL` 的主机与端口可达（例如 `http://127.0.0.1:11434`）。
- 若出现依赖问题：确认在激活的虚拟环境中执行 `pip install -r requirements.txt`。

**开发说明**
- 项目通过 `BaseAIClient` 支持多后端。当前默认实现为 `OllamaClient`（见 `src/api/ollama_client.py`），若需接入其他服务，请实现该抽象并在 `src/api/ai_client.py` 或 `src/frontend/app.py` 中替换实例化逻辑。

**下一步建议**
- 若需我执行：运行测试、替换旧的 `xfyun` 调用或把 README 翻译成英文，请告诉我。我也可以把 README 中的“快速启动”写成可复制粘贴的 shell 脚本。

---

更新说明：已重写快速启动与排查部分，保留项目功能概述与开发提示。

