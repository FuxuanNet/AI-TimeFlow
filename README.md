# 🤖 AI 时间管理系统

一个基于 AI 的智能时间管理系统，集成了多种 AI 模型，通过自然语言对话来帮助用户制定和管理时间计划。

## ✨ 主要功能

- 🗣️ **自然语言交互**: 通过聊天方式与 AI 助手对话
- 📅 **智能日程安排**: AI 自动生成日计划和周计划
- 🔧 **工具调用**: AI 可以调用时间管理工具来执行具体操作
- 💾 **数据持久化**: 计划数据自动保存到本地 JSON 文件
- 🌐 **Web 界面**: 现代化的响应式前端界面
- ⚡ **实时通信**: 基于 WebSocket 的实时消息传输

## 🏗️ 系统架构

```text
AI时间管理系统/
├── frontend/                    # 前端文件
│   ├── index_ws.html           # 主页面 (WebSocket 版本) ⭐
│   ├── app_ws.js              # 前端 JavaScript (WebSocket 版本) ⭐
│   ├── styles.css             # 样式文件 ⭐
│   ├── README.md              # 前端启动指南 📖
│   └── [测试文件...]          # 调试和测试用的临时文件
├── backend_api/                # 后端 API
│   ├── main.py                # FastAPI 服务器 ⭐
│   ├── API_README.md          # 后端API文档 📖
│   └── [废弃文件...]          # 旧版路由文件和测试文件
├── time_planner/               # 核心业务逻辑
│   ├── new_agent.py           # AI Agent (新版) ⭐
│   ├── new_services.py        # 时间管理服务 (新版) ⭐
│   ├── new_models.py          # 数据模型 (新版) ⭐
│   ├── memory.py              # 对话记忆管理 ⭐
│   ├── simple_mcp_client.py   # MCP 客户端 ⭐
│   └── [旧版文件...]          # 已弃用的旧版本文件
├── logs/                       # 系统日志
├── ai_generated_schedules/     # AI 生成的计划文件
├── start_server.py            # 服务器启动脚本 ⭐
├── clean_project.py           # 项目清理脚本 🧹
├── requirements.txt           # 依赖包列表 ⭐
├── .env                       # 环境变量配置 ⭐
├── time_management_data.json  # 数据存储文件 (运行时生成)
├── conversation_memory.json   # 对话记忆文件 (运行时生成)
├── 前端界面设计.md            # 前端设计文档 📖
├── 时间表数据结构.md          # 数据结构文档 📖
└── 项目大概设计.md            # 项目设计文档 📖

注：⭐ 核心文件 | 📖 文档文件 | 🧹 工具文件 | 其他为测试或废弃文件
```

## 🚀 快速开始

### 1. 环境准备

确保您的系统已安装：

- Python 3.10+
- 现代浏览器 (Chrome, Firefox, Edge)

### 2. 创建虚拟环境

```bash
# 使用 conda
conda create -n AI-MCP python=3.10
conda activate AI-MCP

# 或使用 venv
python -m venv ai-time-env
# Windows
ai-time-env\Scripts\activate
# Linux/Mac
source ai-time-env/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

创建 `.env` 文件并配置 AI 模型 API 密钥：

```env
# DeepSeek API (推荐)
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com

# 其他支持的 AI 模型
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GROQ_API_KEY=your_groq_key
```

例如：

```txt
# DeepSeek API 配置
DEEPSEEK_API_KEY=你的密钥
DEEPSEEK_API_BASE=https://api.deepseek.com/v1

# MCP 服务器配置
MCP_SERVER_COMMAND=mcp-server-sequential-thinking

# 系统配置
LOG_LEVEL=INFO
DEBUG=True

```

### 5. 启动后端服务器

```bash
python start_server.py
```

或者手动启动：

```bash
python -m uvicorn backend_api.main:app --reload --port 8000
```

### 6. 打开前端界面

用浏览器打开：`frontend/index_ws.html`

**重要提示**: 请直接在浏览器中打开文件，而不要使用 VS Code Live Server，因为 Live Server 的自动刷新功能会干扰 WebSocket 连接。

## 📖 使用指南

### 基本操作

1. **启动系统**: 运行 `python start_server.py`
2. **打开界面**: 浏览器打开 `frontend/index_ws.html`
3. **开始对话**: 在聊天框中输入您的需求

### 示例对话

```
用户: 帮我安排明天的学习计划
AI: 我来为您安排明天的学习计划...

用户: 我需要这周的编程学习安排
AI: 为您制定这周的编程学习计划...

用户: 查看我今天的任务
AI: 以下是您今天的任务安排...
```

### 界面功能

- **💬 AI 对话**: 与 AI 助手自然语言交流
- **📅 日计划**: 查看和管理每日任务
- **📊 周计划**: 查看和管理周任务
- **🔧 工具面板**: 查看 AI 调用的工具

## 🔧 API 文档

后端服务启动后，可访问以下地址：

- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **WebSocket**: ws://localhost:8000/ws/chat

### 主要 API 端点

```
GET  /api/chat/history           # 获取聊天历史
POST /api/chat/message           # 发送聊天消息
GET  /api/tasks/daily?date=      # 获取日任务
GET  /api/tasks/weekly?week=     # 获取周任务
GET  /api/data/current           # 获取当前数据
```

## 📂 数据存储

系统会自动将数据保存到以下位置：

- **主数据文件**: `time_management_data.json`
- **对话记忆**: `conversation_memory.json`
- **AI 生成的计划**: `ai_generated_schedules/`
- **日志文件**: `logs/`

### 数据结构示例

```json
{
  "start_date": "2025-07-16",
  "daily_schedules": {
    "2025-07-16": {
      "date": "2025-07-16",
      "tasks": [...]
    }
  },
  "weekly_schedules": {
    "1": {
      "week_number": 1,
      "tasks": [...]
    }
  }
}
```

## 🛠️ 开发指南

### 项目结构说明

- **`frontend/`**: 纯前端代码，使用原生 HTML/CSS/JavaScript
- **`backend_api/`**: FastAPI 后端服务
- **`time_planner/`**: 核心业务逻辑，包含 AI Agent 和数据管理
- **`logs/`**: 系统日志文件
- **`ai_generated_schedules/`**: AI 生成的计划文件

### 添加新功能

1. **后端**: 在 `backend_api/main.py` 中添加新的 API 端点
2. **前端**: 在 `frontend/app_ws.js` 中添加相应的前端逻辑
3. **业务逻辑**: 在 `time_planner/` 中添加新的服务方法

### 代码规范

- 使用 Black 进行代码格式化：`black .`
- 使用 isort 整理导入：`isort .`
- 运行测试：`pytest`

## 🚨 常见问题

### Q: 前端页面打开后立即刷新
A: 请直接在浏览器中打开 HTML 文件，不要使用 VS Code Live Server。

### Q: WebSocket 连接失败
A: 确保后端服务器正在运行，检查端口 8000 是否被占用。

### Q: AI 无法回复
A: 检查 `.env` 文件中的 API 密钥是否正确配置。

### Q: 数据丢失
A: 检查 `time_management_data.json` 文件是否存在且有写入权限。

### Q: 端口占用
A: 使用 `netstat -an | findstr :8000` 检查端口状态，或修改端口号。

## 📋 更新日志

### v1.0.0 (2025-07-16)
- ✅ 完整的 WebSocket 实时通信
- ✅ AI 智能时间管理
- ✅ 日程和周程管理
- ✅ 数据持久化存储
- ✅ 现代化 Web 界面

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证。

---

**🎯 开始使用**: `python start_server.py` → 打开 `frontend/index_ws.html`

## 🧹 项目清理建议

为了保持项目整洁，建议删除以下文件：

### 前端废弃文件
```bash
# 可以删除的测试和调试文件
frontend/debug_refresh.html
frontend/minimal_ws_test.html
frontend/test_api.html
frontend/test_chat.html
frontend/test_websocket.html
frontend/static_server.py

# 已被WebSocket版本替代的旧版文件
frontend/app.js
frontend/index.html
```

### 后端冗余文件
```bash
# 已合并到main.py的分离路由文件
backend_api/backend_main.py
backend_api/chat_routes.py
backend_api/data_routes.py
backend_api/task_routes.py
backend_api/test_api.py
backend_api/start_server.py
backend_api/requirements.txt
```

### AI模块旧版文件
```bash
# 已被new_*版本替代的旧文件
time_planner/agent.py
time_planner/services.py
time_planner/models.py
time_planner/cli.py
time_planner/new_cli.py
time_planner/mcp_client.py
time_planner/timetable_manager.py
```

### 清理后的核心文件结构
```text
AI时间管理系统/
├── frontend/
│   ├── index_ws.html      # 主页面
│   ├── app_ws.js          # 前端逻辑
│   └── styles.css         # 样式文件
├── backend_api/
│   └── main.py            # 后端服务
├── time_planner/
│   ├── new_agent.py       # AI Agent
│   ├── new_services.py    # 时间管理服务
│   ├── new_models.py      # 数据模型
│   ├── memory.py          # 对话记忆
│   └── simple_mcp_client.py # MCP客户端
├── start_server.py        # 启动脚本
├── requirements.txt       # 依赖列表
└── .env                   # 环境配置
```
