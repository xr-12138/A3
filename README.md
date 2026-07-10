# 个性化学习智能体（本地/远端 OpenAI 兼容后端）

这是一个高校级别的个性化学习智能体原型，基于 Python + Streamlit，结合可替换的 OpenAI 兼容客户端实现，用于快速试验多智能体调度、资源生成与交互式教学演示。

**关键点**
- 前端入口：`src/frontend/app.py`
- OpenAI 兼容客户端：`src/api/openai_client.py`
- AI 客户端抽象：`src/api/base.py`（`BaseAIClient`）
- 配置示例：`config/.env`

**核心功能**
- 学生画像构建（对话式）
- 多模态资源生成（教学文档、思维导图、题库、代码示例、拓展阅读）
- 个性化学习路径与推荐
- 基于 Streamlit 的交互式辅导界面

---

## 环境要求

- **Python 3.9 – 3.12**（推荐 3.10 / 3.11）
- **pip** 包管理器
- （可选）**Graphviz** —— 用于渲染思维导图（不安装也能运行，仅思维导图功能会降级）

---

## 快速开始（三步启动）

### 第一步：准备环境 —— 请按你的操作系统选择

---

#### 🐧 Linux（Ubuntu / Debian / Fedora / Arch 等）

```bash
# 1. 克隆并进入项目
git clone <your-repo-url>
cd A3-main

# 2. 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 4. （可选）安装 Graphviz（思维导图需要）
sudo apt-get update && sudo apt-get install -y graphviz
```

> 其他 Linux 发行版安装 Graphviz：Fedora 用 `sudo dnf install -y graphviz`；Arch 用 `sudo pacman -S graphviz`。

---

#### 🍎 macOS

```bash
# 1. 克隆并进入项目
git clone <your-repo-url>
cd A3-main

# 2. 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 3. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 4. （可选）安装 Graphviz（思维导图需要）
brew install graphviz
```

> 如果你用 MacPorts：`sudo port install graphviz`；未安装 Homebrew 请访问 https://brew.sh 。
> 如果你使用 fish/csh shell：激活命令分别用 `source .venv/bin/activate.fish` 或 `source .venv/bin/activate.csh`。

---

#### 🪟 Windows（推荐 PowerShell）

```powershell
# 1. 克隆并进入项目（PowerShell）
git clone <your-repo-url>
cd A3-main

# 2. 创建并激活虚拟环境
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 4. （可选）安装 Graphviz（思维导图需要）
#    访问 https://graphviz.org/download/ 下载 Windows 安装包
#    安装时务必勾选 "Add Graphviz to the system PATH"
#    安装完成后关闭并重新打开 PowerShell
```

> **遇到「禁止运行脚本」？** 以管理员身份打开 PowerShell，执行一次 `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`，选 `Y` 即可。
> **CMD 用户？** 激活命令改为 `.venv\Scripts\activate.bat`。

---

### 第二步：配置 API（所有系统通用）

打开 `config/.env` 文件，填入你的配置：

```
OPENAI_API_KEY="your_api_key"
OPENAI_MODEL="gpt-3.5-turbo"
OPENAI_API_URL="https://api.openai.com/v1/chat/completions"
```

> 支持任何 OpenAI 兼容的服务：OpenAI / 讯飞 / DeepSeek / 自搭模型等。
> 也可以用环境变量直接注入（如 `export OPENAI_API_KEY=xxx`）。

### 第三步：启动（所有系统通用）

```bash
streamlit run src/frontend/app.py --server.port 8501
```

浏览器会自动打开；如未自动打开，手动访问：

```
http://localhost:8501
```

> 端口被占用？换一个：`streamlit run src/frontend/app.py --server.port 8502`。

---

## 运行测试（所有系统通用）

```bash
pytest -q
```

---

## 项目结构说明（高层）

- `src/frontend/app.py` — Streamlit 前端，负责界面、会话态与运行时对象初始化。
- `src/api/openai_client.py` — OpenAI 兼容客户端实现；对外提供 `generate_text`、`generate_mindmap`、`generate_questions` 等方法。
- `src/api/base.py` — `BaseAIClient` 抽象类，定义客户端需要实现的方法。
- `src/agents/` — 多智能体调度与具体 agent 实现（画像、资源生成等）。
- `src/core/` — 核心组件（数据库、资源渲染等）。
- `config/.env` — 运行时配置（API Key / URL / MODEL 等）。
- `requirements.txt` — 项目依赖。

---

## 重点开发说明

- **AI 后端替换**：项目通过 `BaseAIClient` 为抽象接口。要接入新的后端，实现该抽象并在 `src/api/ai_client.py`（工厂 / 入口）处替换实例化逻辑。
- **错误处理**：`OpenAIClient` 保证所有调用在出错时返回带前缀或结构化错误（例如 `{"_ai_error": True, ...}` 或以 `[AI错误]` 开头的文本），前端据此呈现可理解的提示而非静默数据。

---

## 故障排查要点

| 现象                                   | 排查思路                                                                 |
|----------------------------------------|--------------------------------------------------------------------------|
| 鉴权失败（401 / 403）                  | 确认 `OPENAI_API_KEY` 与模型权限；可用 `curl` / 浏览器测试 `OPENAI_API_URL`。 |
| 前端报「网络不可达」                    | 确认能从当前主机访问 `OPENAI_API_URL`；检查代理 / 防火墙 / 公司 VPN。      |
| 依赖报错 / 模块找不到                  | 确认虚拟环境已激活；重新执行 `pip install -r requirements.txt`。          |
| `graphviz` / `dot` 相关错误            | 确认已安装 Graphviz **并已加入系统 PATH**（Windows 安装后需重启终端）。    |
| Windows 中文乱码                        | 终端使用 PowerShell 7，并确保系统区域设置使用 UTF-8；或使用 VS Code 终端。 |
| Streamlit 启动慢 / 端口被占用           | 换一个端口：`streamlit run src/frontend/app.py --server.port 8502`。     |

---

## 推荐操作

- 若只是调试 API 连接，可使用项目根脚本 `diagnose_api.py` 来快速验证 `config/.env` 中的配置并做基本诊断。
- 开发过程中建议在 `src/api/` 下新增或替换客户端实现并编写对应的单元测试以保证兼容性。