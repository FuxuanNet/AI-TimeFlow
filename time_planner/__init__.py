"""
AI 时间管理系统

这是一个智能的时间规划和管理系统，帮助用户：
- 自动解析自然语言任务描述
- 生成合理的时间安排
- 检测和解决时间冲突  
- 提供个性化的时间管理建议

主要模块：
- models: 数据模型定义
- services: 核心业务逻辑
- agent: AI Agent 智能助手
- mcp_client: MCP 协议客户端
- cli: 命令行界面

使用方法：
```python
from time_planner.cli import main
import asyncio

# 启动命令行界面
asyncio.run(main())
```

作者：AI Assistant
日期：2025-07-13
版本：1.0.0
"""

from .models import (
    TimeSlot,
    DaySchedule,
    WeekSchedule,
    MonthSchedule,
    UserPreferences,
    TaskType,
    Priority,
)

from .services import TimeSlotService, ScheduleService, PlanningService

from .agent import TimeManagementAgent, get_agent, initialize_agent, shutdown_agent

from .mcp_client import MCPClient, SequentialThinkingClient, MCPManager

__version__ = "1.0.0"
__author__ = "AI Assistant"

__all__ = [
    # 数据模型
    "TimeSlot",
    "DaySchedule",
    "WeekSchedule",
    "MonthSchedule",
    "UserPreferences",
    "TaskType",
    "Priority",
    # 服务类
    "TimeSlotService",
    "ScheduleService",
    "PlanningService",
    # AI Agent
    "TimeManagementAgent",
    "get_agent",
    "initialize_agent",
    "shutdown_agent",
    # MCP 客户端
    "MCPClient",
    "SequentialThinkingClient",
    "MCPManager",
]
