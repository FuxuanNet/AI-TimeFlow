"""
时间管理系统 - 新的数据模型

根据用户需求重新设计的数据结构：
1. 按天为单位的时间管理表 - 用于短期、紧急任务
2. 按周为单位的时间管理表 - 用于长期、学习任务

作者：AI Assistant
日期：2025-07-13
"""

from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum
import json


class Priority(str, Enum):
    """优先级枚举"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DailyTask(BaseModel):
    """按天管理的任务模型"""

    task_name: str = Field(..., description="任务名称")
    belong_to_day: str = Field(..., description="属于哪一天的任务（YYYY-MM-DD格式）")
    start_time: str = Field(..., description="开始时间（HH:MM格式）")
    end_time: str = Field(..., description="结束时间（HH:MM格式）")
    description: str = Field(default="", description="任务描述及注意事项")
    can_reschedule: bool = Field(default=True, description="是否可以更换时间")
    can_compress: bool = Field(default=True, description="是否可以压缩完所耗时间")
    can_parallel: bool = Field(default=False, description="是否可以和其他任务并行")
    parent_task: Optional[str] = Field(
        default=None, description="属于哪个大的时间段任务里分解出来的"
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_name": self.task_name,
            "belong_to_day": self.belong_to_day,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "description": self.description,
            "can_reschedule": self.can_reschedule,
            "can_compress": self.can_compress,
            "can_parallel": self.can_parallel,
            "parent_task": self.parent_task,
        }


class DailySchedule(BaseModel):
    """单日日程模型"""

    date: str = Field(..., description="日期（YYYY-MM-DD格式）")
    week_number: int = Field(..., description="第几周（从用户第一次使用开始算）")
    tasks: List[DailyTask] = Field(default_factory=list, description="任务对象列表")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "date": self.date,
            "week_number": self.week_number,
            "tasks": [task.to_dict() for task in self.tasks],
        }


class WeeklyTask(BaseModel):
    """按周管理的任务模型"""

    task_name: str = Field(..., description="任务名称")
    belong_to_week: int = Field(..., description="属于哪周的任务")
    description: str = Field(default="", description="任务描述及注意事项")
    parent_project: Optional[str] = Field(
        default=None, description="属于哪个大的复杂而笼统的任务里分解出来的"
    )
    priority: Priority = Field(default=Priority.MEDIUM, description="优先级")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_name": self.task_name,
            "belong_to_week": self.belong_to_week,
            "description": self.description,
            "parent_project": self.parent_project,
            "priority": self.priority.value,
        }


class WeeklySchedule(BaseModel):
    """周计划模型"""

    week_number: int = Field(..., description="周数（从用户第一次使用开始算）")
    date_range: str = Field(..., description="日期范围（YYYY-MM-DD - YYYY-MM-DD格式）")
    tasks: List[WeeklyTask] = Field(default_factory=list, description="任务列表")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "week_number": self.week_number,
            "date_range": self.date_range,
            "tasks": [task.to_dict() for task in self.tasks],
        }


class TimeManagementData(BaseModel):
    """时间管理系统的完整数据模型"""

    start_date: str = Field(
        ..., description="用户第一次使用系统的日期（YYYY-MM-DD格式）"
    )
    daily_schedules: Dict[str, DailySchedule] = Field(
        default_factory=dict, description="按天的时间管理表"
    )
    weekly_schedules: Dict[int, WeeklySchedule] = Field(
        default_factory=dict, description="按周的时间管理表"
    )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "start_date": self.start_date,
            "daily_schedules": {
                date_str: schedule.to_dict()
                for date_str, schedule in self.daily_schedules.items()
            },
            "weekly_schedules": {
                week_num: schedule.to_dict()
                for week_num, schedule in self.weekly_schedules.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimeManagementData":
        """从字典创建实例"""
        instance = cls(start_date=data["start_date"])

        # 恢复日程安排
        for date_str, schedule_data in data.get("daily_schedules", {}).items():
            tasks = [DailyTask(**task_data) for task_data in schedule_data["tasks"]]
            instance.daily_schedules[date_str] = DailySchedule(
                date=schedule_data["date"],
                week_number=schedule_data["week_number"],
                tasks=tasks,
            )

        # 恢复周计划
        for week_num, schedule_data in data.get("weekly_schedules", {}).items():
            tasks = [WeeklyTask(**task_data) for task_data in schedule_data["tasks"]]
            instance.weekly_schedules[int(week_num)] = WeeklySchedule(
                week_number=schedule_data["week_number"],
                date_range=schedule_data["date_range"],
                tasks=tasks,
            )

        return instance


class TimeUtils:
    """时间工具类"""

    @staticmethod
    def calculate_week_number(start_date_str: str, target_date_str: str) -> int:
        """计算目标日期是第几周（从开始日期算起）"""
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
            days_diff = (target_date - start_date).days
            week_number = (days_diff // 7) + 1
            return max(1, week_number)
        except ValueError:
            return 1

    @staticmethod
    def get_week_date_range(start_date_str: str, week_number: int) -> str:
        """获取指定周的日期范围"""
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()

            # 计算目标周的开始日期
            week_start = start_date + timedelta(days=(week_number - 1) * 7)
            week_end = week_start + timedelta(days=6)

            return (
                f"{week_start.strftime('%Y-%m-%d')} - {week_end.strftime('%Y-%m-%d')}"
            )
        except ValueError:
            return "Invalid date range"

    @staticmethod
    def get_current_datetime() -> Dict[str, Any]:
        """获取当前时间信息"""
        now = datetime.now()
        return {
            "current_date": now.strftime("%Y-%m-%d"),
            "current_time": now.strftime("%H:%M"),
            "current_datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "weekday": now.strftime("%A"),
            "weekday_chinese": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][
                now.weekday()
            ],
            "is_weekend": now.weekday() >= 5,
        }

    @staticmethod
    def get_detailed_time_info() -> Dict[str, Any]:
        """获取详细的当前时间信息"""
        now = datetime.now()

        # 获取时间段描述
        hour = now.hour
        if 5 <= hour < 12:
            time_period = "上午"
        elif 12 <= hour < 18:
            time_period = "下午"
        elif 18 <= hour < 22:
            time_period = "晚上"
        else:
            time_period = "深夜"

        return {
            "current_date": now.strftime("%Y-%m-%d"),
            "current_time": now.strftime("%H:%M:%S"),
            "current_datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "formatted_time": now.strftime("%Y年%m月%d日 %H:%M:%S"),
            "weekday": now.strftime("%A"),
            "weekday_chinese": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][
                now.weekday()
            ],
            "is_weekend": now.weekday() >= 5,
            "time_period": time_period,
            "hour_24": now.hour,
            "minute": now.minute,
            "second": now.second,
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "day_of_year": now.timetuple().tm_yday,
            "week_of_year": now.isocalendar()[1],
            "timestamp": int(now.timestamp()),
        }

    @staticmethod
    def get_date_info(date_str: str) -> Dict[str, Any]:
        """获取指定日期的信息"""
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            return {
                "date": date_str,
                "weekday": target_date.strftime("%A"),
                "weekday_chinese": [
                    "周一",
                    "周二",
                    "周三",
                    "周四",
                    "周五",
                    "周六",
                    "周日",
                ][target_date.weekday()],
                "is_weekend": target_date.weekday() >= 5,
                "day_of_year": target_date.timetuple().tm_yday,
            }
        except ValueError:
            return {"error": f"Invalid date format: {date_str}"}

    @staticmethod
    def get_time_until_next_period() -> Dict[str, Any]:
        """获取距离下一个时间段的剩余时间"""
        now = datetime.now()

        # 定义时间段
        periods = [
            (6, 0, "早晨"),  # 6:00
            (12, 0, "中午"),  # 12:00
            (18, 0, "傍晚"),  # 18:00
            (22, 0, "夜晚"),  # 22:00
        ]

        current_minutes = now.hour * 60 + now.minute

        for hour, minute, period_name in periods:
            period_minutes = hour * 60 + minute
            if current_minutes < period_minutes:
                remaining_minutes = period_minutes - current_minutes
                remaining_hours = remaining_minutes // 60
                remaining_mins = remaining_minutes % 60

                return {
                    "next_period": period_name,
                    "next_period_time": f"{hour:02d}:{minute:02d}",
                    "remaining_hours": remaining_hours,
                    "remaining_minutes": remaining_mins,
                    "total_remaining_minutes": remaining_minutes,
                    "message": f"距离{period_name}还有 {remaining_hours}小时{remaining_mins}分钟",
                }

        # 如果当前时间晚于最后一个时间段，计算到明天早晨的时间
        tomorrow_morning = now.replace(
            hour=6, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
        remaining_time = tomorrow_morning - now
        remaining_hours = remaining_time.seconds // 3600
        remaining_mins = (remaining_time.seconds % 3600) // 60

        return {
            "next_period": "早晨",
            "next_period_time": "06:00",
            "remaining_hours": remaining_hours,
            "remaining_minutes": remaining_mins,
            "total_remaining_minutes": remaining_time.seconds // 60,
            "message": f"距离明天早晨还有 {remaining_hours}小时{remaining_mins}分钟",
        }

    @staticmethod
    def get_week_progress() -> Dict[str, Any]:
        """获取本周进度信息"""
        now = datetime.now()

        # 获取本周的开始和结束
        days_since_monday = now.weekday()
        week_start = now - timedelta(days=days_since_monday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

        # 计算进度
        total_seconds = (week_end - week_start).total_seconds()
        elapsed_seconds = (now - week_start).total_seconds()
        progress_percentage = (elapsed_seconds / total_seconds) * 100

        return {
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end": week_end.strftime("%Y-%m-%d"),
            "current_day": now.weekday() + 1,  # 1-7
            "days_passed": days_since_monday + 1,
            "days_remaining": 7 - (days_since_monday + 1),
            "progress_percentage": round(progress_percentage, 2),
            "hours_elapsed": round(elapsed_seconds / 3600, 1),
            "hours_remaining": round((total_seconds - elapsed_seconds) / 3600, 1),
        }

    @staticmethod
    def get_current_millisecond() -> int:
        """获取当前时间的毫秒数（自1970年1月1日以来的毫秒数）"""
        return int(datetime.now().timestamp() * 1000)

    @staticmethod
    def format_duration(seconds: int) -> str:
        """格式化持续时间（秒数）为易读的字符串"""
        if seconds < 0:
            return "已结束"

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        parts = []
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        if secs > 0:
            parts.append(f"{secs}秒")

        return " ".join(parts) if parts else "0秒"

    @staticmethod
    def get_time_difference(start_time_str: str, end_time_str: str) -> Dict[str, Any]:
        """计算两个时间点之间的差异"""
        try:
            # 解析时间字符串
            start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
            end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")

            # 计算差异
            delta = end_time - start_time
            total_seconds = int(delta.total_seconds())

            return {
                "days": total_seconds // 86400,
                "hours": (total_seconds % 86400) // 3600,
                "minutes": (total_seconds % 3600) // 60,
                "seconds": total_seconds % 60,
                "total_seconds": total_seconds,
                "formatted": TimeUtils.format_duration(total_seconds),
            }
        except ValueError:
            return {"error": "时间格式应为YYYY-MM-DD HH:MM:SS"}

    @staticmethod
    def add_time_duration(base_time_str: str, duration_str: str) -> str:
        """在基准时间上增加持续时间"""
        try:
            base_time = datetime.strptime(base_time_str, "%Y-%m-%d %H:%M:%S")

            # 解析持续时间
            time_parts = duration_str.split(":")
            hours = int(time_parts[0])
            minutes = int(time_parts[1]) if len(time_parts) > 1 else 0
            seconds = int(time_parts[2]) if len(time_parts) > 2 else 0

            # 计算新时间
            new_time = base_time + timedelta(
                hours=hours, minutes=minutes, seconds=seconds
            )
            return new_time.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            return f"错误：{str(e)}"

    @staticmethod
    def subtract_time_duration(base_time_str: str, duration_str: str) -> str:
        """从基准时间中减去持续时间"""
        try:
            base_time = datetime.strptime(base_time_str, "%Y-%m-%d %H:%M:%S")

            # 解析持续时间
            time_parts = duration_str.split(":")
            hours = int(time_parts[0])
            minutes = int(time_parts[1]) if len(time_parts) > 1 else 0
            seconds = int(time_parts[2]) if len(time_parts) > 2 else 0

            # 计算新时间
            new_time = base_time - timedelta(
                hours=hours, minutes=minutes, seconds=seconds
            )
            return new_time.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            return f"错误：{str(e)}"

    @staticmethod
    def get_day_start_end(date_str: str) -> Dict[str, str]:
        """获取一天的开始和结束时间"""
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            start_of_day = target_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_of_day = target_date.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )

            return {
                "start_of_day": start_of_day.strftime("%Y-%m-%d %H:%M:%S"),
                "end_of_day": end_of_day.strftime("%Y-%m-%d %H:%M:%S"),
            }
        except ValueError:
            return {"error": f"Invalid date format: {date_str}"}

    @staticmethod
    def is_time_overlap(
        start_time1: str, end_time1: str, start_time2: str, end_time2: str
    ) -> bool:
        """判断两个时间段是否重叠"""
        try:
            fmt = "%Y-%m-%d %H:%M:%S"
            start1 = datetime.strptime(start_time1, fmt)
            end1 = datetime.strptime(end_time1, fmt)
            start2 = datetime.strptime(start_time2, fmt)
            end2 = datetime.strptime(end_time2, fmt)

            return max(start1, start2) < min(end1, end2)
        except ValueError:
            return False

    @staticmethod
    def get_next_weekday(date_str: str, weekday: int) -> str:
        """获取下一个指定星期几的日期"""
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")

            # 计算下一个指定星期几的日期
            days_ahead = (weekday - target_date.weekday() + 7) % 7
            if days_ahead == 0:
                days_ahead = 7  # 如果是今天，则获取下周的同一天

            next_date = target_date + timedelta(days=days_ahead)
            return next_date.strftime("%Y-%m-%d")
        except ValueError:
            return "Invalid date"

    @staticmethod
    def get_weekday_name(date_str: str) -> str:
        """获取指定日期是星期几的名称"""
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
            return target_date.strftime("%A")
        except ValueError:
            return "Invalid date"

    @staticmethod
    def get_chinese_zodiac(year: int) -> str:
        """根据年份获取对应的生肖"""
        zodiac_animals = [
            "鼠",
            "牛",
            "虎",
            "兔",
            "龙",
            "蛇",
            "马",
            "羊",
            "猴",
            "鸡",
            "狗",
            "猪",
        ]
        return zodiac_animals[year % 12]

    @staticmethod
    def get_constellation(month: int, day: int) -> str:
        """根据出生月份和日期获取星座"""
        constellations = [
            (1, 20, 2, 18, "水瓶座"),
            (2, 19, 3, 20, "双鱼座"),
            (3, 21, 4, 19, "白羊座"),
            (4, 20, 5, 20, "金牛座"),
            (5, 21, 6, 21, "双子座"),
            (6, 22, 7, 22, "巨蟹座"),
            (7, 23, 8, 22, "狮子座"),
            (8, 23, 9, 22, "处女座"),
            (9, 23, 10, 23, "天秤座"),
            (10, 24, 11, 22, "天蝎座"),
            (11, 23, 12, 21, "射手座"),
            (12, 22, 1, 19, "摩羯座"),
        ]

        for start_month, start_day, end_month, end_day, constellation in constellations:
            start_date = datetime(datetime.now().year, start_month, start_day)
            end_date = datetime(datetime.now().year, end_month, end_day)
            birth_date = datetime(datetime.now().year, month, day)

            if start_date <= birth_date <= end_date:
                return constellation

        return "未知星座"

    @staticmethod
    def calculate_age(birth_date_str: str) -> int:
        """计算年龄"""
        try:
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
            today = datetime.now()

            age = today.year - birth_date.year
            if today.month < birth_date.month or (
                today.month == birth_date.month and today.day < birth_date.day
            ):
                age -= 1

            return age
        except ValueError:
            return 0

    @staticmethod
    def parse_relative_date(relative_term: str, base_date: Optional[str] = None) -> str:
        """解析相对日期词汇（今天、明天、昨天等）"""
        if base_date:
            base = datetime.strptime(base_date, "%Y-%m-%d").date()
        else:
            base = datetime.now().date()

        relative_term = relative_term.lower().strip()

        if relative_term in ["今天", "today"]:
            return base.strftime("%Y-%m-%d")
        elif relative_term in ["明天", "tomorrow"]:
            return (base + timedelta(days=1)).strftime("%Y-%m-%d")
        elif relative_term in ["昨天", "yesterday"]:
            return (base - timedelta(days=1)).strftime("%Y-%m-%d")
        elif relative_term in ["后天"]:
            return (base + timedelta(days=2)).strftime("%Y-%m-%d")
        elif relative_term in ["前天"]:
            return (base - timedelta(days=2)).strftime("%Y-%m-%d")
        else:
            # 如果不是相对日期，直接返回原值
            return relative_term
