"""
任务管理接口实现
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime

from .main import DailyTaskCreate, WeeklyTaskCreate, TaskUpdate, time_service

router = APIRouter(prefix="/api/tasks", tags=["任务管理"])


# ==================== 日任务相关接口 ====================


@router.post("/daily")
async def create_daily_task(task_data: DailyTaskCreate):
    """
    创建日任务

    Args:
        task_data: 日任务创建数据

    Returns:
        Dict: 操作结果
    """
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


@router.get("/daily")
async def get_daily_tasks(
    date_str: str = Query(..., description="日期字符串 (YYYY-MM-DD)")
):
    """
    获取指定日期的日任务

    Args:
        date_str: 日期字符串

    Returns:
        Dict: 日任务列表
    """
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


@router.put("/daily/{task_name}")
async def update_daily_task(task_name: str, date_str: str, task_update: TaskUpdate):
    """
    更新日任务

    Args:
        task_name: 任务名称
        date_str: 日期字符串
        task_update: 更新数据

    Returns:
        Dict: 操作结果
    """
    if not time_service:
        raise HTTPException(status_code=500, detail="时间管理服务未初始化")

    try:
        # 获取现有任务
        tasks = time_service.get_daily_tasks(date_str)
        target_task = None
        for task in tasks:
            if task.task_name == task_name:
                target_task = task
                break

        if not target_task:
            raise HTTPException(status_code=404, detail=f"未找到任务: {task_name}")

        # 删除旧任务
        time_service.delete_daily_task(date_str, task_name)

        # 创建更新后的任务
        updated_data = target_task.dict()
        update_dict = task_update.dict(exclude_unset=True)
        updated_data.update(update_dict)

        success = time_service.add_daily_task(**updated_data)

        if success:
            return {
                "success": True,
                "message": f"日任务 '{task_name}' 更新成功",
                "updated_data": updated_data,
            }
        else:
            raise HTTPException(status_code=400, detail="日任务更新失败")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新日任务失败: {str(e)}")


@router.delete("/daily/{task_name}")
async def delete_daily_task(
    task_name: str, date_str: str = Query(..., description="日期字符串")
):
    """
    删除日任务

    Args:
        task_name: 任务名称
        date_str: 日期字符串

    Returns:
        Dict: 操作结果
    """
    if not time_service:
        raise HTTPException(status_code=500, detail="时间管理服务未初始化")

    try:
        success = time_service.delete_daily_task(date_str, task_name)

        if success:
            return {"success": True, "message": f"日任务 '{task_name}' 删除成功"}
        else:
            raise HTTPException(status_code=404, detail=f"未找到任务: {task_name}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除日任务失败: {str(e)}")


# ==================== 周任务相关接口 ====================


@router.post("/weekly")
async def create_weekly_task(task_data: WeeklyTaskCreate):
    """
    创建周任务

    Args:
        task_data: 周任务创建数据

    Returns:
        Dict: 操作结果
    """
    if not time_service:
        raise HTTPException(status_code=500, detail="时间管理服务未初始化")

    try:
        # 转换 priority 字符串为 Priority 枚举
        from time_planner.new_models import Priority

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


@router.get("/weekly")
async def get_weekly_tasks(week_number: int = Query(..., description="周数")):
    """
    获取指定周的周任务

    Args:
        week_number: 周数

    Returns:
        Dict: 周任务列表
    """
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


@router.delete("/weekly/{task_name}")
async def delete_weekly_task(
    task_name: str, week_number: int = Query(..., description="周数")
):
    """
    删除周任务

    Args:
        task_name: 任务名称
        week_number: 周数

    Returns:
        Dict: 操作结果
    """
    if not time_service:
        raise HTTPException(status_code=500, detail="时间管理服务未初始化")

    try:
        success = time_service.delete_weekly_task(week_number, task_name)

        if success:
            return {"success": True, "message": f"周任务 '{task_name}' 删除成功"}
        else:
            raise HTTPException(status_code=404, detail=f"未找到任务: {task_name}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除周任务失败: {str(e)}")


# ==================== 通用查询接口 ====================


@router.get("/statistics")
async def get_task_statistics():
    """
    获取任务统计信息

    Returns:
        Dict: 统计信息
    """
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


@router.get("/export")
async def export_all_data():
    """
    导出所有任务数据

    Returns:
        Dict: 完整的任务数据
    """
    if not time_service:
        raise HTTPException(status_code=500, detail="时间管理服务未初始化")

    try:
        data = time_service.export_json()
        return {
            "success": True,
            "data": data,
            "export_time": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出数据失败: {str(e)}")
