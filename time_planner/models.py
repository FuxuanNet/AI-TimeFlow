"""
时间规划系统 - 数据模型定义

这个模块定义了时间规划系统中所有核心数据结构，包括：
- 时间段(TimeSlot)：系统中最基本的时间单位
- 任务类型：强制任务和弹性任务
- 日程安排：日程、周程、月程的层级结构
- 用户偏好：作息习惯和个人喜好配置

作者：AI Assistant
日期：2025-07-13
"""

from datetime import datetime, time, timedelta
from datetime import date as Date
from typing import List, Optional, Dict, Any, Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class TaskType(str, Enum):
    """任务类型枚举"""

    FIXED = "fixed"  # 强制任务：不可压缩，时间固定
    FLEXIBLE = "flexible"  # 弹性任务：可压缩、可并行或取消


class Priority(str, Enum):
    """优先级枚举"""

    LOW = "low"  # 低优先级
    MEDIUM = "medium"  # 中优先级
    HIGH = "high"  # 高优先级
    URGENT = "urgent"  # 紧急


class TimeSlot(BaseModel):
    """
    时间段模型 - 系统中所有安排的基础单位

    无论是强制任务还是弹性任务，都用时间段来表示。
    支持时间段的嵌套和并行执行。
    """

    id: UUID = Field(default_factory=uuid4, description="时间段唯一标识")
    title: str = Field(..., description="时间段标题/任务名称")
    description: Optional[str] = Field(None, description="详细描述")

    start_time: datetime = Field(..., description="开始时间")
    end_time: datetime = Field(..., description="结束时间")

    task_type: TaskType = Field(..., description="任务类型：强制或弹性")
    priority: Priority = Field(default=Priority.MEDIUM, description="优先级")

    # 并行和嵌套属性
    can_parallel: bool = Field(default=False, description="是否可以与其他任务并行执行")
    parent_id: Optional[UUID] = Field(None, description="父时间段ID，用于任务分解")
    sub_slots: List["TimeSlot"] = Field(
        default_factory=list, description="子时间段列表"
    )

    # 扩展属性
    location: Optional[str] = Field(None, description="地点")
    tags: List[str] = Field(default_factory=list, description="标签")
    notes: Optional[str] = Field(None, description="备注")

    # 状态
    is_completed: bool = Field(default=False, description="是否已完成")
    completion_rate: float = Field(default=0.0, description="完成进度 0-1")

    @field_validator("end_time")
    @classmethod
    def end_time_must_be_after_start_time(cls, v, info):
        """验证结束时间必须晚于开始时间"""
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("结束时间必须晚于开始时间")
        return v

    @field_validator("completion_rate")
    @classmethod
    def completion_rate_must_be_valid(cls, v):
        """验证完成进度必须在0-1之间"""
        if not 0 <= v <= 1:
            raise ValueError("完成进度必须在0-1之间")
        return v

    @property
    def duration_minutes(self) -> int:
        """获取时间段持续时间（分钟）"""
        return int((self.end_time - self.start_time).total_seconds() / 60)

    @property
    def date(self) -> Date:
        """获取时间段所在日期"""
        return self.start_time.date()

    def overlaps_with(self, other: "TimeSlot") -> bool:
        """检查是否与另一个时间段重叠"""
        return self.start_time < other.end_time and self.end_time > other.start_time

    def can_parallel_with(self, other: "TimeSlot") -> bool:
        """检查是否可以与另一个时间段并行执行"""
        return self.can_parallel and other.can_parallel


class DaySchedule(BaseModel):
    """
    日程安排模型 - 单日的时间安排

    包含某一天的所有时间段，按开始时间排序
    """

    date: Date = Field(..., description="日期")
    slots: List[TimeSlot] = Field(default_factory=list, description="时间段列表")

    # 日程统计信息
    total_duration: int = Field(default=0, description="总安排时间（分钟）")
    free_time: int = Field(default=0, description="空闲时间（分钟）")

    def add_slot(self, slot: TimeSlot) -> bool:
        """
        添加时间段到日程中

        Args:
            slot: 要添加的时间段

        Returns:
            bool: 是否成功添加
        """
        if slot.date != self.date:
            return False

        # 检查时间冲突
        for existing_slot in self.slots:
            if slot.overlaps_with(existing_slot):
                # 如果不能并行，则冲突
                if not slot.can_parallel_with(existing_slot):
                    return False

        self.slots.append(slot)
        self.sort_slots()
        self._update_statistics()
        return True

    def remove_slot(self, slot_id: UUID) -> bool:
        """移除指定时间段"""
        original_length = len(self.slots)
        self.slots = [slot for slot in self.slots if slot.id != slot_id]

        if len(self.slots) < original_length:
            self._update_statistics()
            return True
        return False

    def sort_slots(self):
        """按开始时间排序时间段"""
        self.slots.sort(key=lambda x: x.start_time)

    def get_free_periods(self, start_hour: int = 6, end_hour: int = 23) -> List[tuple]:
        """
        获取空闲时间段

        Args:
            start_hour: 一天开始的小时
            end_hour: 一天结束的小时

        Returns:
            List[tuple]: 空闲时间段列表 [(start_time, end_time), ...]
        """
        free_periods = []
        day_start = datetime.combine(self.date, time(start_hour, 0))
        day_end = datetime.combine(self.date, time(end_hour, 0))

        if not self.slots:
            return [(day_start, day_end)]

        current_time = day_start
        for slot in self.slots:
            if slot.start_time > current_time:
                free_periods.append((current_time, slot.start_time))
            current_time = max(current_time, slot.end_time)

        if current_time < day_end:
            free_periods.append((current_time, day_end))

        return free_periods

    def _update_statistics(self):
        """更新统计信息"""
        self.total_duration = sum(slot.duration_minutes for slot in self.slots)
        free_periods = self.get_free_periods()
        self.free_time = sum(
            int((end - start).total_seconds() / 60) for start, end in free_periods
        )


class WeekSchedule(BaseModel):
    """
    周程安排模型 - 一周的时间安排

    包含一周7天的日程安排
    """

    week_number: int = Field(..., description="周数（从年初开始计算）")
    year: int = Field(..., description="年份")
    start_date: Date = Field(..., description="周开始日期（周一）")

    days: List[DaySchedule] = Field(default_factory=list, description="7天的日程安排")

    # 周程统计
    total_tasks: int = Field(default=0, description="总任务数")
    completed_tasks: int = Field(default=0, description="已完成任务数")

    def __init__(self, **data):
        super().__init__(**data)
        # 初始化7天的日程
        if not self.days:
            for i in range(7):
                day_date = self.start_date + timedelta(days=i)
                self.days.append(DaySchedule(date=day_date))

    def get_day(self, weekday: int) -> DaySchedule:
        """
        获取指定星期的日程

        Args:
            weekday: 星期几 (0=周一, 6=周日)

        Returns:
            DaySchedule: 对应的日程
        """
        if 0 <= weekday <= 6:
            return self.days[weekday]
        raise ValueError("星期几必须在0-6之间")

    def add_slot_to_day(self, weekday: int, slot: TimeSlot) -> bool:
        """向指定日期添加时间段"""
        day_schedule = self.get_day(weekday)
        success = day_schedule.add_slot(slot)
        if success:
            self._update_statistics()
        return success

    def get_all_slots(self) -> List[TimeSlot]:
        """获取一周内所有时间段"""
        all_slots = []
        for day in self.days:
            all_slots.extend(day.slots)
        return all_slots

    def _update_statistics(self):
        """更新统计信息"""
        all_slots = self.get_all_slots()
        self.total_tasks = len(all_slots)
        self.completed_tasks = sum(1 for slot in all_slots if slot.is_completed)


class MonthSchedule(BaseModel):
    """
    月程安排模型 - 多周的时间安排

    实际上是无限周的概念，不局限于自然月
    """

    schedule_id: UUID = Field(default_factory=uuid4, description="月程安排唯一标识")
    title: str = Field(..., description="月程安排标题")
    start_date: Date = Field(..., description="开始日期")

    weeks: List[WeekSchedule] = Field(default_factory=list, description="周程安排列表")

    # 月程统计
    total_weeks: int = Field(default=0, description="总周数")

    def add_week(self, week: WeekSchedule):
        """添加周程安排"""
        self.weeks.append(week)
        self.total_weeks = len(self.weeks)

    def get_week(self, week_index: int) -> Optional[WeekSchedule]:
        """获取指定周的安排"""
        if 0 <= week_index < len(self.weeks):
            return self.weeks[week_index]
        return None

    def create_new_week(self, start_date: Date) -> WeekSchedule:
        """创建新的周程安排"""
        from datetime import timedelta

        # 计算周数
        week_number = (start_date - self.start_date).days // 7 + 1
        year = start_date.year

        week = WeekSchedule(week_number=week_number, year=year, start_date=start_date)

        self.add_week(week)
        return week


class UserPreferences(BaseModel):
    """
    用户偏好配置模型

    定义用户的作息习惯、时间偏好等个人配置
    """

    user_id: UUID = Field(default_factory=uuid4, description="用户ID")

    # 作息时间
    wake_up_time: time = Field(default=time(7, 0), description="起床时间")
    sleep_time: time = Field(default=time(23, 0), description="睡觉时间")

    # 用餐时间
    breakfast_time: time = Field(default=time(8, 0), description="早餐时间")
    lunch_time: time = Field(default=time(12, 0), description="午餐时间")
    dinner_time: time = Field(default=time(18, 0), description="晚餐时间")

    meal_duration: int = Field(default=45, description="用餐时长（分钟）")

    # 工作和学习偏好
    productive_hours_start: time = Field(default=time(9, 0), description="高效时段开始")
    productive_hours_end: time = Field(default=time(17, 0), description="高效时段结束")

    max_continuous_work: int = Field(
        default=120, description="最大连续工作时间（分钟）"
    )
    break_duration: int = Field(default=15, description="休息时长（分钟）")

    # 娱乐和休息
    entertainment_duration: int = Field(default=60, description="每日娱乐时长（分钟）")
    exercise_duration: int = Field(default=30, description="每日运动时长（分钟）")

    # 个人偏好
    preferred_work_days: List[int] = Field(
        default_factory=lambda: [0, 1, 2, 3, 4], description="偏好工作日"  # 周一到周五
    )

    buffer_time: int = Field(default=10, description="任务间缓冲时间（分钟）")

    # 个性化设置
    allow_parallel_tasks: bool = Field(default=True, description="是否允许并行任务")
    strict_schedule: bool = Field(default=False, description="是否严格按时间执行")

    flexible_meal_time: bool = Field(default=True, description="用餐时间是否可调整")
    flexible_sleep_time: bool = Field(default=False, description="睡眠时间是否可调整")


# 为了支持递归引用，需要更新模型
TimeSlot.model_rebuild()


# 导出所有模型
__all__ = [
    "TaskType",
    "Priority",
    "TimeSlot",
    "DaySchedule",
    "WeekSchedule",
    "MonthSchedule",
    "UserPreferences",
]
