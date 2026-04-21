# 高等教育个性化学习智能体系统

一个面向高校的个性化学习智能体原型框架（Python + FastAPI + Streamlit + 讯飞 API + 多智能体）。本仓库包含：多智能体资源生成骨架、思维导图生成器、Streamlit 演示前端、配置管理与测试用例，便于快速搭建与扩展。

项目根目录：`/home/hjj/桌面/A3-main`

---

## 主要功能
- 学生画像自动构建（对话式、卡片化展示）
- 多模态资源自动生成（文档、思维导图、题库、代码示例、视频脚本）
- 个性化学习路径规划示例
- 智能辅导（聊天式答疑模拟）
- 思维导图（Mindmap）渲染（基于 Graphviz）

## 技术栈
- Python 3.10+（兼容 3.12）
- FastAPI（后端，可扩展）
- Streamlit（前端演示）
- graphviz（思维导图渲染，需系统安装二进制）
- 讯飞 API（LLM/多模态接入，抽象为 `xfyun_config` 与 `llm_client`）

## 仓库结构（要点）
- `config/`：环境配置模板与加载器
	- `config/.env.example`：环境变量模板
	- `config/.env`：本地示例（勿提交真实密钥）
	- `config/xfyun_config.py`：从 `.env` / 环境变量加载配置
- `src/core/`：核心业务逻辑
	- `src/core/resource_generator.py`：思维导图与资源生成器（Graphviz 集成，支持 LLM 客户端）
- `src/frontend/`：Streamlit 前端
	- `src/frontend/clients.py`：`BaseAIClient` 抽象类与 `MockClient` 实现
	- `src/frontend/app.py`：Streamlit 应用入口（侧边栏导航：画像/资源/路径/辅导）
- `docs/`：项目说明文档（`project_structure.md`）
- `tests/`：测试用例
	- `tests/test_config.py`：验证配置加载
	- `tests/test_resource_generator.py`：资源生成与文件输出示例

## 先决条件（Linux）
- Python 3.10+（推荐 3.12）
- 系统安装 `graphviz`（用于生成 PNG）
	- Debian/Ubuntu: `sudo apt-get update && sudo apt-get install -y graphviz`
- 推荐使用虚拟环境

## 快速开始（开发）
在项目根目录下执行：

```bash
# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装 Python 依赖（requirements.txt 可能需要补充真实依赖）
pip install -r requirements.txt
pip install streamlit python-dotenv graphviz pytest
```

运行 Streamlit 前端（演示）：
```bash
streamlit run src/frontend/app.py --server.port 8501
```

运行测试：
```bash
pytest -q
```

运行资源生成功能的示例（无需 Streamlit）：
```bash
python -c "from src.core.resource_generator import ResourceGenerator; from src.core.resource_generator import MockLLM; rg=ResourceGenerator(llm_client=MockLLM()); print(rg.generate_mindmap('人工智能导论'))"
```

## 配置说明
- 请复制 `config/.env.example` 为 `config/.env` 并填写真实值（讯飞 APP_ID/API_KEY/API_SECRET、数据库 URL 等）。
- `config/xfyun_config.py` 会优先读取系统环境变量，若不存在则读取 `config/.env`。

## 注意事项与扩展点
- 目前前端使用 `MockClient` 做演示；将真实 AI 能力接入时，请实现 `BaseAIClient` 并在 `src/frontend/app.py` 中替换实例。
- `src/core/resource_generator.py` 支持同步/异步 LLM client；真实接入时请实现 `generate` 或 `async_generate` 方法。
- 生产环境请使用密钥管理服务（不要把 `config/.env` 或真实密钥提交到仓库）。
- 若要在生产以 API 服务方式运行，请实现 `src/api/app.py`（FastAPI）并使用 Gunicorn/Uvicorn 部署。

## 常见问题
- Q: 图无法生成或报错 `dot not found`？
	- A: 请确保系统已安装 `graphviz` 二进制（apt/yum/brew 安装）。
- Q: 测试失败与依赖缺失？
	- A: 确认在虚拟环境中安装 `python-dotenv`、`pytest` 和 `graphviz`。

## 下一步推荐工作
1. 实现 `src/api/` 的 FastAPI 接口并添加认证（OAuth2/JWT）
2. 将 `MockClient` 替换为对接讯飞的 `llm_client` 实现
3. 添加 CI（GitHub Actions）以跑 lint、tests、build
4. 将大文件与媒体迁移到对象存储（S3/MinIO），并在 `storage.py` 中实现适配

---
如果你希望，我可以：
- 把 `MockClient` 替换为对接讯飞 API 的示例实现（需要你提供讯飞凭证或允许我把示例放在 `config/.env.example` 中）；
- 为 `src/api/app.py` 生成 FastAPI 最小样板并添加基本路由。 

