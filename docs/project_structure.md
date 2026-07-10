# 高等教育个性化学习智能体系统 — 项目目录说明

本文档针对 Linux 环境、技术栈为 Python + FastAPI + Streamlit + 讯飞 API + 多智能体的项目模版，说明仓库内每个目录的作用与核心文件规划，便于团队开发、测试与部署。

## 简要说明
- 目标：构建面向高校的个性化学习智能体系统，支持多智能体协同生成多模态学习资源、动态学习路径规划与效果评估。
- 受众：后端工程师、前端工程师、AI 工程师、运维与测试人员。

## 技术栈与运行前提
- 语言：Python 3.10+
- 后端：FastAPI + Uvicorn/Gunicorn
- 前端：Streamlit（演示）或单页应用（可选）
- AI 接入：讯飞 API（模型调用、语音/多模态能力）
- 其它：SQL/NoSQL 数据库（可选）、Redis（可选，任务/会话缓存）、对象存储（Media）

运行前提（Linux）：
- 建议使用虚拟环境：`python -m venv .venv` 并激活
- 必需环境变量（示例）：`XF_API_KEY`、`XF_API_SECRET`、`ENV`、`DATABASE_URL`
- 安装依赖：`pip install -r requirements.txt`

示例启动命令：
```bash
source .venv/bin/activate
pip install -r requirements.txt
export XF_API_KEY="your_key"
export XF_API_SECRET="your_secret"
# 启动 API（开发）
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
# 启动 Streamlit 前端（演示）
streamlit run src.frontend.app:main --server.port 8501
```

## 顶层目录说明
- `README.md`：项目概述、快速上手、架构图与联系方式。
- `A3.md`：赛题说明（已存在）。
- `requirements.txt`：Python 依赖清单（或使用 `pyproject.toml`/Poetry）。
- `config/`：配置示例与机密占位（`.env.example`、`xunfei.yaml`）。
- `data/`：静态资源与数据存储（`dataset/`、`user_profiles/` 等）。
- `docs/`：设计文档、架构、部署与测试计划（本文件位于此处）。
- `src/`：源码主目录（下文详细）。
- `tests/`：单元与集成测试。
- `scripts/`（可选）：运维脚本（迁移、备份、发布）。

## `src/` 目录结构与核心文件（建议）

src 是代码主目录，建议按层次分离责任。

- `src/main.py`
  - 作用：开发时入口，用于启动服务、执行初始化检查或迁移任务。
  - 建议实现：加载配置、初始化日志、注册路由和事件钩子。

- `src/api/`（FastAPI 层）
  - 作用：HTTP 接口与外部交互。所有 REST/HTTP 路由放在此处。
  - 核心文件：
    - `app.py`：创建 `FastAPI()` 实例，注册中间件、异常处理、CORS、路由前缀。
    - `routes/`：按功能分路由文件，例如 `auth.py`、`agents.py`、`resources.py`、`profiles.py`。
    - `schemas/`：Pydantic 请求/响应模型与验证规则。
    - `dependencies.py`：依赖注入（认证、DB 连接、限流等）。

- `src/frontend/`（Streamlit 演示层）
  - 作用：为展示与快速原型提供交互界面（可替换为 React/Vue 等前端）。
  - 核心文件：
    - `app.py` 或 `streamlit_app.py`：Streamlit 应用入口 `main()`。
    - `components/`：UI 组件封装（卡片、进度条、多模态展示）。

- `src/agents/`（多智能体实现）
  - 作用：定义智能体角色、交互协议、任务分配与状态管理。
  - 核心文件：
    - `agent_base.py`：`Agent` 抽象基类（生命周期、消息接口、角色声明）。
    - `manager.py`：智能体调度器，负责任务分发、重试、负载与并发控制。
    - `roles/`：具体角色实现，例如：
      - `content_generator.py`（生成讲解文档/题库/脚本）
      - `tutor_agent.py`（对话式辅导、答疑）
      - `evaluator.py`（评估与分数计算）
      - `multimodal_agent.py`（多模态资源拼装）
    - `persistence.py`：会话与上下文持久化（可接数据库/对象存储）。

- `src/core/`（核心业务逻辑与第三方 API 封装）
  - 作用：LLM/讯飞 API 封装、多智能体协同策略、资源生成流水线。
  - 核心文件：
    - `config.py`：集中配置加载（优先环境变量，fallback 配置文件）。
    - `llm_client.py`：讯飞 API 封装（鉴权、请求/响应、重试、限流）。
    - `multi_agent_orchestrator.py`：任务路由、协同策略、互检机制（防幻觉）。
    - `profile_manager.py`：画像抽取/更新（至少 6 维谱系化特征）。
    - `resource_generator.py`：资源生成流水线（PPT/Markdown/题库/脚本/多模态打包）。
    - `evaluator.py`：学习效果评估逻辑及反馈生成器。

- `src/utils/`（工具函数）
  - 作用：通用工具与基础设施封装。
  - 核心文件：
    - `logging_config.py`：统一日志格式（JSON）、轮转策略。
    - `helpers.py`：字符串、文件、时间工具函数。
    - `security.py`：签名、加解密、令牌工具（切勿将密钥提交到仓库）。
    - `storage.py`：本地/对象存储抽象（S3/MinIO 适配）。

- `src/models/`（可选）
  - 作用：持久化模型（ORM）与领域实体定义（SQLAlchemy/ Pydantic models）。

- `src/services/`（可选）
  - 作用：将复杂业务逻辑拆到服务层，便于重用与测试（如 `user_service.py`、`resource_service.py`）。

## 配置管理
- 推荐文件：`config/.env.example`、`config/xunfei.yaml`。
- 配置加载：优先读取环境变量，测试环境可使用 `.env`（`python-dotenv`）。
- 机密管理：生产使用密钥管理服务（Vault、KMS）或系统环境变量。

## 数据与媒体存储
- `data/dataset/`：课程知识库（Markdown/JSON/PDF），建议每条知识项包含元信息（id, title, tags, source）。
- `data/user_profiles/`：用户画像样例（JSON），包含至少 6 个维度：知识基础、认知风格、易错点、学习目标、学习时段偏好、资源偏好。
- 大文件与媒体建议使用对象存储并在元数据中保留索引。

## 日志、监控与异常处理
- 统一日志格式（JSON），记录 trace_id、user_id、request_id 等，便于链路追踪。
- 在 `src/api/app.py` 添加全局异常处理、慢请求记录与调用埋点（讯飞 API、资源生成）。
- 监控建议：Prometheus + Grafana；关键指标：请求时延、队列长度、模型调用失败率、生成成功率。

## 测试策略
- 单元测试：`tests/unit/test_*.py`，覆盖画像构建、资源生成核心函数。
- 集成测试：`tests/integration/test_api.py` （使用 `fastapi.testclient.TestClient`）。
- 工具：`pytest`、`pytest-cov`、`pre-commit`（格式化与 lint）

## 部署建议（Linux）
- 开发：`uvicorn --reload` 与 `streamlit run`。
- 生产：`gunicorn -k uvicorn.workers.UvicornWorker src.api.app:app -w 4`，并使用 `systemd` 管理服务。
- 可选：Docker 化、使用 `docker-compose` 编排 API、前端、Worker、Redis、数据库。

## 安全与防幻觉（重要）
- 生成链路审计：为每次模型输出记录来源、时间、输入 prompt 与置信度。
- 多智能体互校：关键输出使用另一角色复核或外部知识库验证。
- 内容过滤：整合敏感词、事实核查、来源证据链（避免学术错误）。
- 沙箱执行：对代码类实操案例使用隔离执行环境，限制资源与 I/O 权限。

## 推荐 docs/ 文件清单
- `docs/architecture.md`：总体架构图与模块交互说明。
- `docs/api.md`：API 列表与示例请求/响应。
- `docs/deployment.md`：生产部署步骤、`systemd` 示例、Dockerfile。
- `docs/security.md`：密钥管理、权限模型、审计策略。
- `docs/test_plan.md`：测试用例、集成测试场景与验收标准。

## 快速示例文件清单（供初始化）
- `src/main.py`
- `src/api/app.py`
- `src/api/routes/agents.py`
- `src/agents/agent_base.py`
- `src/core/llm_client.py`
- `src/core/multi_agent_orchestrator.py`
- `src/core/resource_generator.py`
- `src/frontend/app.py`
- `config/.env.example`


