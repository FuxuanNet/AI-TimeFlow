"""
AI 时间管理系统 - 后端 API 服务（简化版）

基于 FastAPI 的后端 API，为前端提供完整的时间管理功能接口。
不修改现有 AI 代码，通过接口方式提供服务。

安装依赖：
pip install fastapi uvicorn pydantic

启动服务：
uvicorn backend_main:app --host 0.0.0.0 --port 8000 --reload

作者：Fuxuan
日期：2025-07-16
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
import json
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
    import uvicorn

    FASTAPI_AVAILABLE = True
except ImportError:
    print("❌ FastAPI 未安装，请运行: pip install fastapi uvicorn pydantic")
    FASTAPI_AVAILABLE = False
    sys.exit(1)

# 导入项目模块
from time_planner.new_agent import NewTimeManagementAgent
from time_planner.new_services import TimeManagementService
from time_planner.new_models import Priority

# 创建 FastAPI 应用
app = FastAPI(
    title="AI 时间管理系统 API",
    description="为前端提供完整的时间管理功能接口",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置 CORS - 解决跨域问题
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 全局变量：AI Agent 实例
ai_agent: Optional[NewTimeManagementAgent] = None
time_service: Optional[TimeManagementService] = None


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化 AI Agent"""
    global ai_agent, time_service
    try:
        ai_agent = NewTimeManagementAgent()
        time_service = ai_agent.time_service
        print("✅ AI Agent 初始化成功")
    except Exception as e:
        print(f"❌ AI Agent 初始化失败: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    global ai_agent
    if ai_agent:
        try:
            # AI Agent 没有 shutdown 方法，直接设为 None
            ai_agent = None
            print("✅ AI Agent 已关闭")
        except:
            pass


# ==================== 数据模型定义 ====================


class ChatMessage(BaseModel):
    """聊天消息模型"""

    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    """聊天响应模型"""

    success: bool
    message: str
    response: str
    tools_used: List[str] = []
    timestamp: str
    session_id: str


class TaskBase(BaseModel):
    """任务基础模型"""

    task_name: str
    description: str = ""


class DailyTaskCreate(TaskBase):
    """创建日任务模型"""

    date_str: str
    start_time: str
    end_time: str
    can_reschedule: bool = True
    can_compress: bool = True
    can_parallel: bool = False
    parent_task: Optional[str] = None


class WeeklyTaskCreate(TaskBase):
    """创建周任务模型"""

    week_number: int
    parent_project: Optional[str] = None
    priority: str = "medium"


class TaskUpdate(BaseModel):
    """任务更新模型"""

    task_name: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    can_reschedule: Optional[bool] = None
    can_compress: Optional[bool] = None
    can_parallel: Optional[bool] = None
    parent_task: Optional[str] = None
    parent_project: Optional[str] = None
    priority: Optional[str] = None


# ==================== 基础端点 ====================


@app.get("/")
async def root():
    """根端点 - API 欢迎信息"""
    return {
        "message": "AI 时间管理系统 API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "运行中",
        "endpoints": {"chat": "/api/chat", "tasks": "/api/tasks", "data": "/api/data"},
    }


@app.get("/health")
async def health():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ai_agent_status": ai_agent is not None,
        "time_service_status": time_service is not None,
    }


# ==================== AI 聊天接口 ====================


@app.post("/api/chat/message", response_model=ChatResponse)
async def send_message(chat_message: ChatMessage):
    """向 AI 发送消息并获取响应"""
    if not ai_agent:
        raise HTTPException(status_code=500, detail="AI Agent 未初始化")

    try:
        # 调用 AI Agent 处理用户请求
        response = await asyncio.create_task(
            asyncio.to_thread(ai_agent.process_user_request, chat_message.message)
        )

        # 获取使用的工具列表（从 AI Agent 状态中获取）
        tools_used = getattr(ai_agent, "last_tools_used", [])

        return ChatResponse(
            success=True,
            message=chat_message.message,
            response=response,
            tools_used=tools_used,
            timestamp=datetime.now().isoformat(),
            session_id=chat_message.session_id,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 处理失败: {str(e)}")


@app.get("/api/chat/history")
async def get_chat_history(session_id: str = "default", limit: int = 50):
    """获取聊天历史记录"""
    if not ai_agent:
        raise HTTPException(status_code=500, detail="AI Agent 未初始化")

    try:
        # 从 AI Agent 的内存中获取历史记录
        memory = ai_agent.memory
        if hasattr(memory, "get_conversation_history"):
            history = memory.get_conversation_history(session_id, limit)
            return {"success": True, "history": history}
        else:
            # 如果没有实现历史记录功能，返回空列表
            return {"success": True, "history": []}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}")


# ==================== 任务管理接口 ====================


@app.post("/api/tasks/daily")
async def create_daily_task(task_data: DailyTaskCreate):
    """创建日任务"""
    if not time_service:
        raise HTTPException(status_code=500, detail="时间管理服务未初始化")

    try:
        success = time_service.add_daily_task(
            date_str=task_data.date_str,
            task_name=task_data.task_name,
            start_time=task_data.start_time,
            end_time=task_data.end_time,
            description=task_data.description,
            can_reschedule=task_data.can_reschedule,
            can_compress=task_data.can_compress,
            can_parallel=task_data.can_parallel,
            parent_task=task_data.parent_task,
        )

        if success:
            return {
                "success": True,
                "message": f"日任务 '{task_data.task_name}' 创建成功",
                "task_data": task_data.dict(),
            }
        else:
            raise HTTPException(status_code=400, detail="日任务创建失败")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建日任务失败: {str(e)}")


@app.get("/api/tasks/daily")
async def get_daily_tasks(
    date_str: str = Query(..., description="日期字符串 (YYYY-MM-DD)")
):
    """获取指定日期的日任务"""
    if not time_service:
        raise HTTPException(status_code=500, detail="时间管理服务未初始化")

    try:
        tasks = time_service.get_daily_tasks(date_str)
        return {
            "success": True,
            "date": date_str,
            "tasks": [task.dict() for task in tasks],
            "count": len(tasks),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取日任务失败: {str(e)}")


@app.post("/api/tasks/weekly")
async def create_weekly_task(task_data: WeeklyTaskCreate):
    """创建周任务"""
    if not time_service:
        raise HTTPException(status_code=500, detail="时间管理服务未初始化")

    try:
        # 转换 priority 字符串为 Priority 枚举
        priority_map = {
            "low": Priority.LOW,
            "medium": Priority.MEDIUM,
            "high": Priority.HIGH,
        }
        priority_enum = priority_map.get(task_data.priority.lower(), Priority.MEDIUM)

        success = time_service.add_weekly_task(
            week_number=task_data.week_number,
            task_name=task_data.task_name,
            description=task_data.description,
            parent_project=task_data.parent_project,
            priority=priority_enum,
        )

        if success:
            return {
                "success": True,
                "message": f"周任务 '{task_data.task_name}' 创建成功",
                "task_data": task_data.dict(),
            }
        else:
            raise HTTPException(status_code=400, detail="周任务创建失败")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建周任务失败: {str(e)}")


@app.get("/api/tasks/weekly")
async def get_weekly_tasks(week_number: int = Query(..., description="周数")):
    """获取指定周的周任务"""
    if not time_service:
        raise HTTPException(status_code=500, detail="时间管理服务未初始化")

    try:
        tasks = time_service.get_weekly_tasks(week_number)
        return {
            "success": True,
            "week_number": week_number,
            "tasks": [task.dict() for task in tasks],
            "count": len(tasks),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取周任务失败: {str(e)}")


@app.get("/api/tasks/statistics")
async def get_task_statistics():
    """获取任务统计信息"""
    if not time_service:
        raise HTTPException(status_code=500, detail="时间管理服务未初始化")

    try:
        stats = time_service.get_statistics()
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


# ==================== 数据管理接口 ====================


@app.get("/api/data/schedules/latest")
async def get_latest_schedule():
    """获取最新的 AI 生成的时间表"""
    try:
        # 检查 latest_schedule.json 文件
        latest_file = Path("latest_schedule.json")
        if latest_file.exists():
            with open(latest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {"success": True, "schedule": data, "source": "latest_schedule.json"}

        # 如果没有最新文件，检查 ai_generated_schedules 目录
        schedules_dir = Path("ai_generated_schedules")
        if schedules_dir.exists():
            schedule_files = list(schedules_dir.glob("*.json"))
            if schedule_files:
                # 获取最新的文件
                latest_file = max(schedule_files, key=lambda f: f.stat().st_mtime)
                with open(latest_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return {
                    "success": True,
                    "schedule": data,
                    "source": str(latest_file.name),
                }

        # 如果都没有，返回空
        return {"success": True, "schedule": None, "message": "暂无AI生成的时间表"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最新时间表失败: {str(e)}")


@app.post("/api/data/export/frontend")
async def export_for_frontend():
    """为前端导出完整数据"""
    if not ai_agent:
        raise HTTPException(status_code=500, detail="AI Agent 未初始化")

    try:
        # 使用 AI Agent 的前端导出功能
        export_data = ai_agent.export_schedule_for_frontend()

        return {
            "success": True,
            "data": export_data,
            "export_time": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"前端数据导出失败: {str(e)}")


@app.get("/api/data/time-info")
async def get_time_info():
    """获取当前时间信息"""
    try:
        from time_planner.new_models import TimeUtils

        # 获取详细时间信息
        time_info = {
            "current_time": TimeUtils.get_current_time_info(),
            "detailed_time": TimeUtils.get_detailed_time_info(),
            "week_progress": TimeUtils.get_week_progress(),
            "timestamp": datetime.now().isoformat(),
        }

        return {"success": True, "time_info": time_info}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取时间信息失败: {str(e)}")


if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        print("🚀 启动 AI 时间管理系统 API 服务...")
        print("📖 API 文档: http://localhost:8000/docs")
        print("🔍 ReDoc 文档: http://localhost:8000/redoc")

        uvicorn.run(
            "backend_main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
        )
    else:
        print("❌ FastAPI 未安装，无法启动服务")
