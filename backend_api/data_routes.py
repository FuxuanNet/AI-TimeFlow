"""
数据管理接口实现
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path

from .main import ai_agent, time_service

router = APIRouter(prefix="/api/data", tags=["数据管理"])


@router.get("/schedules/latest")
async def get_latest_schedule():
    """
    获取最新的 AI 生成的时间表

    Returns:
        Dict: 最新时间表数据
    """
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


@router.get("/schedules/history")
async def get_schedule_history(limit: int = Query(10, description="返回数量限制")):
    """
    获取AI生成的时间表历史

    Args:
        limit: 返回的时间表数量限制

    Returns:
        Dict: 历史时间表列表
    """
    try:
        schedules_dir = Path("ai_generated_schedules")
        if not schedules_dir.exists():
            return {"success": True, "schedules": [], "message": "暂无历史时间表"}

        # 获取所有JSON文件
        schedule_files = list(schedules_dir.glob("*.json"))

        # 按修改时间排序（最新的在前）
        schedule_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # 限制数量
        schedule_files = schedule_files[:limit]

        schedules = []
        for file in schedule_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    schedules.append(
                        {
                            "filename": file.name,
                            "timestamp": datetime.fromtimestamp(
                                file.stat().st_mtime
                            ).isoformat(),
                            "data": data,
                        }
                    )
            except Exception as e:
                print(f"读取文件 {file} 失败: {e}")
                continue

        return {"success": True, "schedules": schedules, "count": len(schedules)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取时间表历史失败: {str(e)}")


@router.post("/export/frontend")
async def export_for_frontend():
    """
    为前端导出完整数据

    Returns:
        Dict: 前端需要的完整数据
    """
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


@router.get("/current-data")
async def get_current_data():
    """
    获取当前的时间管理数据

    Returns:
        Dict: 当前数据状态
    """
    if not time_service:
        raise HTTPException(status_code=500, detail="时间管理服务未初始化")

    try:
        # 获取当前数据
        current_data = time_service.export_json()

        # 获取统计信息
        stats = time_service.get_statistics()

        return {
            "success": True,
            "current_data": current_data,
            "statistics": stats,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取当前数据失败: {str(e)}")


@router.post("/backup")
async def create_backup():
    """
    创建数据备份

    Returns:
        Dict: 备份操作结果
    """
    if not time_service:
        raise HTTPException(status_code=500, detail="时间管理服务未初始化")

    try:
        # 创建备份目录
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)

        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"backup_{timestamp}.json"

        # 导出当前数据
        current_data = time_service.export_json()

        # 保存备份
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)

        return {
            "success": True,
            "backup_file": str(backup_file),
            "timestamp": timestamp,
            "message": "数据备份创建成功",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建备份失败: {str(e)}")


@router.get("/time-info")
async def get_time_info():
    """
    获取当前时间信息

    Returns:
        Dict: 时间信息
    """
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


@router.get("/health")
async def health_check():
    """
    健康检查接口

    Returns:
        Dict: 系统健康状态
    """
    try:
        health_status = {
            "api_status": "健康",
            "ai_agent_status": "已初始化" if ai_agent else "未初始化",
            "time_service_status": "已初始化" if time_service else "未初始化",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
        }

        # 检查关键文件是否存在
        files_status = {
            "time_management_data.json": Path("time_management_data.json").exists(),
            "conversation_memory.json": Path("conversation_memory.json").exists(),
            "ai_generated_schedules_dir": Path("ai_generated_schedules").exists(),
        }

        health_status["files_status"] = files_status

        return {"success": True, "health": health_status}

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
