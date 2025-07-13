"""
时间规划系统 - 工具服务模块

这个模块提供所有与时间规划表操作相关的工具和接口，包括：
- 时间段的增删改查
- 日程、周程、月程的管理
- 冲突检测和自动调整
- 时间规划生成算法

作者：AI Assistant  
日期：2025-07-13
"""

from datetime import datetime, timedelta
from datetime import date as Date
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import json
import os
from pathlib import Path
from loguru import logger

from .models import (
    TimeSlot,
    DaySchedule,
    WeekSchedule,
    MonthSchedule,
    UserPreferences,
    TaskType,
    Priority,
)


class TimeSlotService:
    """时间段服务类 - 管理单个时间段的操作"""

    def __init__(self, data_file: str = "time_slots.json"):
        self.data_file = data_file
        self.slots: Dict[UUID, TimeSlot] = {}
        self._load_from_file()
        logger.info("时间段服务初始化完成")

    def _load_from_file(self):
        """从文件加载时间段数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for slot_id, slot_data in data.items():
                    # 将字符串转换回 UUID
                    uuid_key = UUID(slot_id)

                    # 重建 TimeSlot 对象
                    slot = TimeSlot(
                        title=slot_data["title"],
                        start_time=datetime.fromisoformat(slot_data["start_time"]),
                        end_time=datetime.fromisoformat(slot_data["end_time"]),
                        task_type=TaskType(slot_data["task_type"]),
                        priority=Priority(slot_data["priority"]),
                        description=slot_data.get("description"),
                        can_parallel=slot_data.get("can_parallel", False),
                        location=slot_data.get("location"),
                        tags=slot_data.get("tags", []),
                    )
                    # 恢复原始 ID
                    slot.id = uuid_key
                    self.slots[uuid_key] = slot

                logger.info(f"从 {self.data_file} 加载了 {len(self.slots)} 个时间段")
            except Exception as e:
                logger.error(f"加载时间段数据失败: {e}")
                self.slots = {}
        else:
            logger.info(f"时间段数据文件 {self.data_file} 不存在，将创建新文件")

    def _save_to_file(self):
        """保存时间段数据到文件"""
        try:
            data = {}
            for slot_id, slot in self.slots.items():
                data[str(slot_id)] = {
                    "title": slot.title,
                    "start_time": slot.start_time.isoformat(),
                    "end_time": slot.end_time.isoformat(),
                    "task_type": slot.task_type.value,
                    "priority": slot.priority.value,
                    "description": slot.description,
                    "can_parallel": slot.can_parallel,
                    "location": slot.location,
                    "tags": slot.tags,
                }

            # 确保目录存在
            os.makedirs(
                (
                    os.path.dirname(self.data_file)
                    if os.path.dirname(self.data_file)
                    else "."
                ),
                exist_ok=True,
            )

            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"保存了 {len(self.slots)} 个时间段到 {self.data_file}")
        except Exception as e:
            logger.error(f"保存时间段数据失败: {e}")

    def create_slot(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        task_type: TaskType = TaskType.FLEXIBLE,
        priority: Priority = Priority.MEDIUM,
        description: Optional[str] = None,
        can_parallel: bool = False,
        location: Optional[str] = None,
        tags: List[str] = None,
    ) -> TimeSlot:
        """
        创建新的时间段

        Args:
            title: 时间段标题
            start_time: 开始时间
            end_time: 结束时间
            task_type: 任务类型
            priority: 优先级
            description: 详细描述
            can_parallel: 是否可以并行
            location: 地点
            tags: 标签列表

        Returns:
            TimeSlot: 创建的时间段对象
        """
        slot = TimeSlot(
            title=title,
            start_time=start_time,
            end_time=end_time,
            task_type=task_type,
            priority=priority,
            description=description,
            can_parallel=can_parallel,
            location=location,
            tags=tags or [],
        )

        self.slots[slot.id] = slot
        logger.info(f"创建时间段: {title} ({start_time} - {end_time})")
        self._save_to_file()  # 创建后立即保存
        return slot

    def get_slot(self, slot_id: UUID) -> Optional[TimeSlot]:
        """获取指定时间段"""
        return self.slots.get(slot_id)

    def update_slot(self, slot_id: UUID, **updates) -> Optional[TimeSlot]:
        """
        更新时间段信息

        Args:
            slot_id: 时间段ID
            **updates: 要更新的字段

        Returns:
            Optional[TimeSlot]: 更新后的时间段对象，如果不存在则返回None
        """
        slot = self.slots.get(slot_id)
        if not slot:
            logger.warning(f"时间段不存在: {slot_id}")
            return None

        for field, value in updates.items():
            if hasattr(slot, field):
                setattr(slot, field, value)

        logger.info(f"更新时间段: {slot.title}")
        self._save_to_file()  # 更新后保存
        return slot

    def delete_slot(self, slot_id: UUID) -> bool:
        """删除时间段"""
        if slot_id in self.slots:
            slot = self.slots.pop(slot_id)
            logger.info(f"删除时间段: {slot.title}")
            self._save_to_file()  # 删除后保存
            return True
        return False

    def find_slots_by_date_range(
        self, start_date: Date, end_date: Date
    ) -> List[TimeSlot]:
        """根据日期范围查找时间段"""
        result = []
        for slot in self.slots.values():
            slot_date = slot.date
            if start_date <= slot_date <= end_date:
                result.append(slot)

        # 按开始时间排序
        result.sort(key=lambda x: x.start_time)
        return result

    def detect_conflicts(
        self, slots: List[TimeSlot]
    ) -> List[Tuple[TimeSlot, TimeSlot]]:
        """
        检测时间段冲突

        Args:
            slots: 要检测的时间段列表

        Returns:
            List[Tuple[TimeSlot, TimeSlot]]: 冲突的时间段对列表
        """
        conflicts = []
        for i in range(len(slots)):
            for j in range(i + 1, len(slots)):
                slot1, slot2 = slots[i], slots[j]
                if slot1.overlaps_with(slot2) and not slot1.can_parallel_with(slot2):
                    conflicts.append((slot1, slot2))

        logger.info(f"检测到 {len(conflicts)} 个时间冲突")
        return conflicts


class ScheduleService:
    """日程服务类 - 管理日程、周程、月程的操作"""

    def __init__(self, slot_service: TimeSlotService):
        self.slot_service = slot_service
        self.day_schedules: Dict[Date, DaySchedule] = {}
        self.week_schedules: Dict[int, WeekSchedule] = {}
        self.month_schedules: Dict[UUID, MonthSchedule] = {}
        logger.info("日程服务初始化完成")

    def get_or_create_day_schedule(self, date: Date) -> DaySchedule:
        """获取或创建指定日期的日程"""
        if date not in self.day_schedules:
            self.day_schedules[date] = DaySchedule(date=date)
            logger.info(f"创建日程: {date}")
        return self.day_schedules[date]

    def add_slot_to_day(self, date: Date, slot: TimeSlot) -> bool:
        """向指定日期添加时间段"""
        day_schedule = self.get_or_create_day_schedule(date)
        success = day_schedule.add_slot(slot)
        if success:
            logger.info(f"时间段已添加到日程 {date}: {slot.title}")
        else:
            logger.warning(f"时间段添加失败，可能存在冲突: {slot.title}")
        return success

    def remove_slot_from_day(self, date: Date, slot_id: UUID) -> bool:
        """从指定日期移除时间段"""
        if date in self.day_schedules:
            success = self.day_schedules[date].remove_slot(slot_id)
            if success:
                logger.info(f"时间段已从日程 {date} 移除: {slot_id}")
            return success
        return False

    def get_week_schedule(self, week_number: int, year: int) -> Optional[WeekSchedule]:
        """获取指定周的周程"""
        week_key = week_number * 10000 + year  # 简单的复合键
        return self.week_schedules.get(week_key)

    def create_week_schedule(self, start_date: Date) -> WeekSchedule:
        """创建周程安排"""
        # 计算周数
        year = start_date.year
        week_number = start_date.isocalendar()[1]

        week_schedule = WeekSchedule(
            week_number=week_number, year=year, start_date=start_date
        )

        week_key = week_number * 10000 + year
        self.week_schedules[week_key] = week_schedule

        logger.info(f"创建周程: 第{week_number}周, {start_date}")
        return week_schedule

    def create_month_schedule(self, title: str, start_date: Date) -> MonthSchedule:
        """创建月程安排"""
        month_schedule = MonthSchedule(title=title, start_date=start_date)

        self.month_schedules[month_schedule.schedule_id] = month_schedule
        logger.info(f"创建月程: {title}, 开始日期: {start_date}")
        return month_schedule

    def query_slots_by_range(
        self, start_datetime: datetime, end_datetime: datetime
    ) -> List[TimeSlot]:
        """
        根据时间范围查询时间段

        Args:
            start_datetime: 开始时间
            end_datetime: 结束时间

        Returns:
            List[TimeSlot]: 符合条件的时间段列表
        """
        start_date = start_datetime.date()
        end_date = end_datetime.date()

        all_slots = []
        current_date = start_date

        while current_date <= end_date:
            if current_date in self.day_schedules:
                day_schedule = self.day_schedules[current_date]
                for slot in day_schedule.slots:
                    # 检查时间段是否在查询范围内
                    if (
                        slot.start_time < end_datetime
                        and slot.end_time > start_datetime
                    ):
                        all_slots.append(slot)
            current_date += timedelta(days=1)

        all_slots.sort(key=lambda x: x.start_time)
        logger.info(f"查询到 {len(all_slots)} 个时间段")
        return all_slots


class PlanningService:
    """时间规划服务类 - 智能时间规划算法"""

    def __init__(self, schedule_service: ScheduleService):
        self.schedule_service = schedule_service
        logger.info("时间规划服务初始化完成")

    def generate_daily_plan(
        self, target_date: Date, tasks: List[TimeSlot], preferences: UserPreferences
    ) -> DaySchedule:
        """
        为指定日期生成日程计划

        Args:
            target_date: 目标日期
            tasks: 要安排的任务列表
            preferences: 用户偏好

        Returns:
            DaySchedule: 生成的日程
        """
        logger.info(f"开始为 {target_date} 生成日程计划")

        # 获取或创建日程
        day_schedule = self.schedule_service.get_or_create_day_schedule(target_date)

        # 1. 首先安排固定的作息时间
        self._schedule_routine_tasks(day_schedule, target_date, preferences)

        # 2. 按优先级排序任务
        sorted_tasks = self._sort_tasks_by_priority(tasks)

        # 3. 安排任务到空闲时间段
        for task in sorted_tasks:
            self._try_schedule_task(day_schedule, task, preferences)

        logger.info(f"日程计划生成完成: {target_date}")
        return day_schedule

    def generate_weekly_plan(
        self, start_date: Date, tasks: List[TimeSlot], preferences: UserPreferences
    ) -> WeekSchedule:
        """
        生成周程计划

        Args:
            start_date: 周开始日期（周一）
            tasks: 要安排的任务列表
            preferences: 用户偏好

        Returns:
            WeekSchedule: 生成的周程
        """
        logger.info(f"开始生成周程计划: {start_date}")

        week_schedule = self.schedule_service.create_week_schedule(start_date)

        # 按优先级和截止时间排序任务
        sorted_tasks = self._sort_tasks_for_week(tasks)

        # 逐个安排任务到合适的日期
        for task in sorted_tasks:
            best_day = self._find_best_day_for_task(week_schedule, task, preferences)
            if best_day is not None:
                success = week_schedule.add_slot_to_day(best_day, task)
                if not success:
                    logger.warning(f"任务安排失败: {task.title}")

        logger.info(f"周程计划生成完成: 共安排 {len(sorted_tasks)} 个任务")
        return week_schedule

    def optimize_schedule(
        self, day_schedule: DaySchedule, preferences: UserPreferences
    ) -> DaySchedule:
        """
        优化现有日程安排

        Args:
            day_schedule: 要优化的日程
            preferences: 用户偏好

        Returns:
            DaySchedule: 优化后的日程
        """
        logger.info(f"开始优化日程: {day_schedule.date}")

        # 检测冲突
        conflicts = self.schedule_service.slot_service.detect_conflicts(
            day_schedule.slots
        )

        # 解决冲突
        for conflict_pair in conflicts:
            self._resolve_conflict(day_schedule, conflict_pair, preferences)

        # 调整任务顺序以提高效率
        self._optimize_task_order(day_schedule, preferences)

        logger.info(f"日程优化完成: {day_schedule.date}")
        return day_schedule

    def _schedule_routine_tasks(
        self, day_schedule: DaySchedule, target_date: Date, preferences: UserPreferences
    ):
        """安排日常作息任务"""
        base_datetime = datetime.combine(target_date, preferences.wake_up_time)

        # 安排用餐时间
        meals = [
            ("早餐", preferences.breakfast_time),
            ("午餐", preferences.lunch_time),
            ("晚餐", preferences.dinner_time),
        ]

        for meal_name, meal_time in meals:
            start_time = datetime.combine(target_date, meal_time)
            end_time = start_time + timedelta(minutes=preferences.meal_duration)

            meal_slot = TimeSlot(
                title=meal_name,
                start_time=start_time,
                end_time=end_time,
                task_type=(
                    TaskType.FLEXIBLE
                    if preferences.flexible_meal_time
                    else TaskType.FIXED
                ),
                can_parallel=False,
            )

            day_schedule.add_slot(meal_slot)

    def _sort_tasks_by_priority(self, tasks: List[TimeSlot]) -> List[TimeSlot]:
        """按优先级排序任务"""
        priority_order = {
            Priority.URGENT: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3,
        }

        return sorted(tasks, key=lambda x: (priority_order[x.priority], x.start_time))

    def _sort_tasks_for_week(self, tasks: List[TimeSlot]) -> List[TimeSlot]:
        """为周程规划排序任务"""

        # 按优先级、任务类型和持续时间排序
        def sort_key(task):
            priority_weight = {
                Priority.URGENT: 0,
                Priority.HIGH: 1,
                Priority.MEDIUM: 2,
                Priority.LOW: 3,
            }
            type_weight = 0 if task.task_type == TaskType.FIXED else 1
            return (priority_weight[task.priority], type_weight, -task.duration_minutes)

        return sorted(tasks, key=sort_key)

    def _try_schedule_task(
        self, day_schedule: DaySchedule, task: TimeSlot, preferences: UserPreferences
    ) -> bool:
        """尝试将任务安排到日程中"""
        # 获取空闲时间段
        free_periods = day_schedule.get_free_periods()

        for start_time, end_time in free_periods:
            # 检查空闲时间段是否足够
            available_duration = (end_time - start_time).total_seconds() / 60
            required_duration = task.duration_minutes + preferences.buffer_time

            if available_duration >= required_duration:
                # 调整任务时间到空闲时间段
                new_start = start_time
                new_end = new_start + timedelta(minutes=task.duration_minutes)

                # 更新任务时间
                task.start_time = new_start
                task.end_time = new_end

                # 添加到日程
                return day_schedule.add_slot(task)

        return False

    def _find_best_day_for_task(
        self, week_schedule: WeekSchedule, task: TimeSlot, preferences: UserPreferences
    ) -> Optional[int]:
        """为任务找到最佳的安排日期"""
        # 评估每一天的适合度
        best_day = None
        best_score = -1

        for day_index in range(7):
            day_schedule = week_schedule.get_day(day_index)
            score = self._evaluate_day_for_task(day_schedule, task, preferences)

            if score > best_score:
                best_score = score
                best_day = day_index

        return best_day if best_score > 0 else None

    def _evaluate_day_for_task(
        self, day_schedule: DaySchedule, task: TimeSlot, preferences: UserPreferences
    ) -> float:
        """评估某一天对任务的适合度"""
        # 基础分数
        score = 1.0

        # 检查是否是偏好工作日
        weekday = day_schedule.date.weekday()
        if weekday in preferences.preferred_work_days:
            score += 0.5

        # 检查空闲时间是否充足
        free_periods = day_schedule.get_free_periods()
        max_free_duration = (
            max((end - start).total_seconds() / 60 for start, end in free_periods)
            if free_periods
            else 0
        )

        if max_free_duration >= task.duration_minutes + preferences.buffer_time:
            score += 0.3
        else:
            score -= 0.5

        # 检查当天任务密度
        if day_schedule.total_duration > 8 * 60:  # 超过8小时
            score -= 0.2

        return max(0, score)

    def _resolve_conflict(
        self,
        day_schedule: DaySchedule,
        conflict_pair: Tuple[TimeSlot, TimeSlot],
        preferences: UserPreferences,
    ):
        """解决时间冲突"""
        slot1, slot2 = conflict_pair

        # 如果一个是弹性任务，一个是固定任务，调整弹性任务
        if slot1.task_type == TaskType.FLEXIBLE and slot2.task_type == TaskType.FIXED:
            self._reschedule_flexible_task(day_schedule, slot1, preferences)
        elif slot2.task_type == TaskType.FLEXIBLE and slot1.task_type == TaskType.FIXED:
            self._reschedule_flexible_task(day_schedule, slot2, preferences)
        else:
            # 两个都是同类型，按优先级调整
            if slot1.priority.value < slot2.priority.value:  # 优先级更高
                self._reschedule_flexible_task(day_schedule, slot2, preferences)
            else:
                self._reschedule_flexible_task(day_schedule, slot1, preferences)

    def _reschedule_flexible_task(
        self, day_schedule: DaySchedule, task: TimeSlot, preferences: UserPreferences
    ):
        """重新安排弹性任务"""
        # 从当前位置移除
        day_schedule.remove_slot(task.id)

        # 尝试重新安排
        if not self._try_schedule_task(day_schedule, task, preferences):
            logger.warning(f"无法重新安排任务: {task.title}")

    def _optimize_task_order(
        self, day_schedule: DaySchedule, preferences: UserPreferences
    ):
        """优化任务顺序"""
        # 按效率优化任务顺序（这里是简化版）
        day_schedule.sort_slots()

        # 确保高效时段安排重要任务
        productive_start = datetime.combine(
            day_schedule.date, preferences.productive_hours_start
        )
        productive_end = datetime.combine(
            day_schedule.date, preferences.productive_hours_end
        )

        # 将高优先级任务移到高效时段（简化实现）
        high_priority_tasks = [
            slot
            for slot in day_schedule.slots
            if slot.priority in [Priority.HIGH, Priority.URGENT]
        ]

        for task in high_priority_tasks:
            if task.start_time < productive_start or task.end_time > productive_end:
                # 尝试移动到高效时段
                pass  # 实际实现会更复杂


# 导出服务类
__all__ = ["TimeSlotService", "ScheduleService", "PlanningService"]
