"""
AI 聊天接口实现
"""

from fastapi import APIRouter, HTTPException
from typing import List
import asyncio
from datetime import datetime

from .main import ChatMessage, ChatResponse, ai_agent

router = APIRouter(prefix="/api/chat", tags=["AI 聊天"])


@router.post("/message", response_model=ChatResponse)
async def send_message(chat_message: ChatMessage):
    """
    向 AI 发送消息并获取响应

    Args:
        chat_message: 包含用户消息和会话ID的对象

    Returns:
        ChatResponse: AI 的响应信息

    Raises:
        HTTPException: 当 AI Agent 未初始化或处理失败时
    """
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


@router.get("/history")
async def get_chat_history(session_id: str = "default", limit: int = 50):
    """
    获取聊天历史记录

    Args:
        session_id: 会话ID
        limit: 返回的消息数量限制

    Returns:
        List[Dict]: 聊天历史记录
    """
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


@router.delete("/history")
async def clear_chat_history(session_id: str = "default"):
    """
    清空指定会话的聊天历史

    Args:
        session_id: 要清空的会话ID

    Returns:
        Dict: 操作结果
    """
    if not ai_agent:
        raise HTTPException(status_code=500, detail="AI Agent 未初始化")

    try:
        memory = ai_agent.memory
        if hasattr(memory, "clear_session"):
            memory.clear_session(session_id)
            return {"success": True, "message": f"会话 {session_id} 历史记录已清空"}
        else:
            return {"success": True, "message": "历史记录功能未实现"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空历史记录失败: {str(e)}")


@router.post("/system-info")
async def get_system_info():
    """
    获取 AI 系统信息和状态

    Returns:
        Dict: 系统状态信息
    """
    if not ai_agent:
        raise HTTPException(status_code=500, detail="AI Agent 未初始化")

    try:
        # 获取系统信息
        info = {
            "ai_model": "DeepSeek V3",
            "status": "运行中",
            "features": [
                "时间管理任务增删改查",
                "AI 智能日程安排",
                "JSON 格式输出",
                "记忆对话上下文",
                "多工具集成",
            ],
            "available_tools": [
                "时间查询工具",
                "任务管理工具",
                "日程安排工具",
                "数据导出工具",
            ],
            "mcp_status": "可选功能",
            "timestamp": datetime.now().isoformat(),
        }

        return {"success": True, "system_info": info}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统信息失败: {str(e)}")
