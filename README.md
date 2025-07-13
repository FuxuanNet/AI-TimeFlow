# AI 时间管理系统

一个基于 AI 的智能时间规划助手，帮助用户高效管理时间和任务安排。

## 🌟 功能特色

- **自然语言解析**: 直接用日常语言描述任务，系统自动理解并安排
- **智能时间规划**: 基于用户偏好和作息习惯生成合理的时间安排
- **冲突检测**: 自动检测时间冲突并提供解决方案
- **思维链推理**: 使用 MCP Sequential Thinking 进行复杂的推理过程
- **个性化建议**: 根据用户习惯提供个性化的时间管理建议
- **弹性任务管理**: 区分强制任务和弹性任务，智能调整优先级

## 🏗️ 系统架构

```
AI时间管理系统/
├── time_planner/           # 核心模块
│   ├── models.py          # 数据模型定义
│   ├── services.py        # 业务逻辑服务
│   ├── agent.py           # AI Agent 核心
│   ├── mcp_client.py      # MCP 协议客户端
│   └── cli.py             # 命令行界面
├── main.py                # 主程序入口
├── test_core.py           # 核心功能测试
├── requirements.txt       # Python 依赖
├── .env                   # 环境配置
└── README.md             # 项目说明
```

## 📦 安装依赖

### 1. Python 依赖

```bash
# 安装 Python 包
pip install -r requirements.txt
```

### 2. MCP 服务器

```bash
# 安装 Sequential Thinking MCP 服务器
npm install -g @modelcontextprotocol/server-sequential-thinking
```

### 3. 环境配置

创建 `.env` 文件并配置您的 API 密钥：

```env
# DeepSeek API 配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_API_BASE=https://api.deepseek.com/v1

# MCP 服务器配置
MCP_SERVER_COMMAND=mcp-server-sequential-thinking

# 系统配置
LOG_LEVEL=INFO
DEBUG=True
```

## 🚀 快速开始

### 1. 环境检查

```bash
# 检查系统环境和依赖
python main.py --check
```

### 2. 核心功能测试

```bash
# 测试核心功能（无需完整环境）
python test_core.py
```

### 3. 启动系统

```bash
# 启动交互模式
python main.py

# 运行演示模式
python main.py --demo

# 调试模式
python main.py --debug
```

## 💬 使用示例

启动系统后，您可以用自然语言与 AI 助手交互：

```
🙋 请告诉我您的需求：明天上午学习数学2小时

🤖 AI助手：我已经为您安排了明天上午的数学学习时间。
建议时间：09:00-11:00，这样既能保证高效学习，
又不会与您的日常作息冲突。

🙋 请告诉我您的需求：这周我有个项目要完成，需要15小时

🤖 AI助手：我建议将15小时的项目工作分配到本周的工作日中：
- 周一至周五，每天安排3小时
- 优先安排在您的高效时段（9:00-17:00）
- 预留适当的休息间隔
```

## 🛠️ 主要组件

### 数据模型 (models.py)

- **TimeSlot**: 时间段基础模型
- **DaySchedule/WeekSchedule/MonthSchedule**: 多层级日程管理
- **UserPreferences**: 用户偏好和作息习惯
- **TaskType**: 任务类型（强制/弹性）
- **Priority**: 优先级管理

### 核心服务 (services.py)

- **TimeSlotService**: 时间段的增删改查
- **ScheduleService**: 日程管理和查询
- **PlanningService**: 智能规划算法

### AI Agent (agent.py)

- **TimeManagementAgent**: 核心 AI 助手
- **自然语言解析**: 任务描述理解
- **工具调用**: 集成各种规划工具
- **思维链推理**: 复杂问题的步骤化思考

### MCP 客户端 (mcp_client.py)

- **MCPClient**: MCP 协议通信
- **SequentialThinkingClient**: 思维链专用客户端  
- **MCPManager**: 统一管理 MCP 服务

## 🎯 设计思路

### 数据结构优化

系统采用了层级化的时间管理结构：
- **时间段(TimeSlot)**: 最小时间单位，支持嵌套和并行
- **日程(DaySchedule)**: 单日安排，自动排序和冲突检测
- **周程(WeekSchedule)**: 一周规划，支持跨日任务分配
- **月程(MonthSchedule)**: 长期规划，无限周概念

### 任务分类

- **强制任务**: 时间固定，不可压缩（如会议、考试）
- **弹性任务**: 可调整时间，支持并行（如学习、娱乐）

### 智能特性

- **冲突解决**: 自动检测时间冲突，智能调整弹性任务
- **个性化**: 基于用户作息和偏好进行个性化安排
- **并行支持**: 某些任务可以并行执行（如边吃饭边听音乐）
- **思维链**: 复杂规划通过多步骤推理实现

## 🔧 开发指南

### 添加新工具

在 `agent.py` 中添加新的工具函数：

```python
@self.agent.tool
def your_new_tool(param1: str, param2: int) -> Dict[str, Any]:
    """工具描述"""
    # 实现逻辑
    return {"result": "success"}
```

### 扩展数据模型

在 `models.py` 中继承基础模型：

```python
class YourCustomSlot(TimeSlot):
    custom_field: str = Field(..., description="自定义字段")
```

### 添加新服务

在 `services.py` 中创建新服务类：

```python
class YourService:
    def __init__(self, dependency_service):
        self.dependency = dependency_service
    
    def your_method(self):
        # 实现业务逻辑
        pass
```

## 📝 API 文档

### 核心 API

#### 创建时间段
```python
slot = slot_service.create_slot(
    title="学习任务",
    start_time=datetime(2025, 7, 14, 9, 0),
    end_time=datetime(2025, 7, 14, 11, 0),
    task_type=TaskType.FIXED,
    priority=Priority.HIGH
)
```

#### 生成日程计划
```python
day_schedule = planning_service.generate_daily_plan(
    target_date=date(2025, 7, 14),
    tasks=task_list,
    preferences=user_preferences
)
```

#### AI 处理请求
```python
response = await agent.process_user_request(
    user_input="明天学习数学2小时",
    user_preferences=preferences
)
```

## 🐛 故障排除

### 常见问题

1. **MCP 服务器启动失败**
   ```bash
   # 检查 Node.js 安装
   node --version
   npm --version
   
   # 重新安装 MCP 服务器
   npm uninstall -g @modelcontextprotocol/server-sequential-thinking
   npm install -g @modelcontextprotocol/server-sequential-thinking
   ```

2. **API 密钥配置错误**
   - 检查 `.env` 文件是否存在
   - 确认 API 密钥格式正确
   - 验证 API 端点可访问

3. **依赖包安装失败**
   ```bash
   # 升级 pip
   python -m pip install --upgrade pip
   
   # 清理缓存重新安装
   pip cache purge
   pip install -r requirements.txt
   ```

### 日志调试

```bash
# 开启调试模式查看详细日志
python main.py --debug

# 查看日志文件
tail -f logs/app.log
```

## 🤝 贡献指南

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [PydanticAI](https://github.com/pydantic/pydantic-ai) - AI Agent 框架
- [Model Context Protocol](https://modelcontextprotocol.io/) - 工具调用协议
- [DeepSeek](https://www.deepseek.com/) - 大语言模型服务
- [Loguru](https://github.com/Delgan/loguru) - 日志处理

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 项目 Issues: [GitHub Issues](https://github.com/your-repo/issues)
- 邮件: your-email@example.com

---

**🚀 开始您的智能时间管理之旅吧！**
