# 个性化学习智能体（本地 Ollama 接入）

这是一个高校个性化学习智能体原型，使用 Python + Streamlit + 本地 Ollama（LLM）进行演示。仓库包含多智能体调度骨架、资源生成器、Streamlit 前端与测试用例，方便在本地通过 Ollama 进行快速迭代。

---

**要点**
- 前端演示入口：`src/frontend/app.py`
- 本地 LLM 客户端实现：`src/api/ollama_client.py`（替换了原来的讯飞/OpenAI 兼容实现）
- 抽象接口：`src/api/base.py`（`BaseAIClient`），其子类用于绑定不同后端

**主要功能**
- 学生画像构建（对话式）
- 多模态资源生成（文档、思维导图、题库、代码示例等）
- 个性化学习路径示例
- 智能问答辅导（Streamlit 聊天式界面）

## 本地依赖与先决条件
- Python 3.10+（推荐 3.12）
- 系统安装 `graphviz`（用于思维导图渲染）
- 安装并运行 Ollama，本项目默认假定 Ollama HTTP 兼容接口监听在 `http://127.0.0.1:11434`（可通过 `config/.env` 修改）

建议（Ubuntu/Debian）：
```bash
sudo apt-get update && sudo apt-get install -y graphviz
```

关于 Ollama：请确保你的本地 Ollama 服务已安装并在本机可访问；如果你使用其他 LLM 服务或代理，请在 `config/.env` 中设置 `XF_API_URL` 和 `XF_MODEL` 指向相应地址/模型名。

## 配置
- 项目使用 `config/.env` 读取本地配置（仓库中已有示例）。关键配置项：
  - `XF_API_URL`：本地 Ollama 或兼容端点，例如 `http://127.0.0.1:11434/v1/chat/completions`
  - `XF_API_KEY`：如需要请填写（本地可能不需要）
  - `XF_MODEL`：模型标识（例如 `qwen3.5:2b` 或你本地 Ollama 已安装的模型名）

示例（config/.env）已包含示例值。

## 快速运行（开发）
在项目根目录执行：

```bash
# 建议使用虚拟环境
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install streamlit requests python-dotenv graphviz pytest
```

启动 Streamlit 前端：
```bash
streamlit run src/frontend/app.py --server.port 8501
```

访问 http://localhost:8501 使用演示界面。

运行测试：
```bash
pytest -q
```

## 开发说明
- 已将默认 AI 客户端替换为 `src/api/ollama_client.py`，它实现了 `BaseAIClient` 接口，并通过 `config/.env` 的 `XF_API_URL`/`XF_MODEL` 与本地 Ollama 通信。
- 若需接入其他后端，只需实现 `BaseAIClient` 并在 `src/frontend/app.py` 中替换实例化类。

## 后续建议
- 若用于生产，请把敏感配置迁移到安全的密钥管理系统，不要把真实密钥提交到仓库。
- 可选：为 Ollama 客户端添加更完整的流式处理、重试与速率限制支持。

---

如需我把仓库中其它以往的 AI 调用点（如 websocket 版或旧的 `xfyun_client.py`）也统一移除或迁移到 `OllamaClient`，我可以继续替换并运行相关测试。 

