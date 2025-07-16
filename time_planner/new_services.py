"""
时间管理系统 - 新的服务层

提供对时间管理数据的CRUD操作和JSON存储功能

作者：AI Assistant
日期：2025-07-13
"""

import json
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from loguru import logger

from .new_models import (
    TimeManagementData,
    DailySchedule,
    WeeklySchedule,
    DailyTask,
    WeeklyTask,
    Priority,
    TimeUtils,
)


class TimeManagementService:
    """时间管理服务类"""

    def __init__(self, data_file: str = "time_management_data.json"):
        """初始化服务"""
        self.data_file = data_file
        self.data: TimeManagementData = self._load_data()
        logger.info(f"时间管理服务初始化完成，数据文件：{data_file}")

    def _load_data(self) -> TimeManagementData:
        """从JSON文件加载数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data_dict = json.load(f)
                logger.info(
                    f"成功加载时间管理数据，包含 {len(data_dict.get('daily_schedules', {}))} 天和 {len(data_dict.get('weekly_schedules', {}))} 周的计划"
                )
                return TimeManagementData.from_dict(data_dict)
            except Exception as e:
                logger.error(f"加载数据文件失败：{e}，将创建新的数据结构")

        # 如果文件不存在或加载失败，创建新的数据结构
        current_date = datetime.now().strftime("%Y-%m-%d")
        new_data = TimeManagementData(start_date=current_date)
        self._save_data(new_data)
        logger.info(f"创建新的时间管理数据，开始日期：{current_date}")
        return new_data

    def _save_data(self, data: Optional[TimeManagementData] = None):
        """保存数据到JSON文件"""
        save_data = data or self.data
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(save_data.to_dict(), f, ensure_ascii=False, indent=2)
            logger.debug("时间管理数据已保存")
        except Exception as e:
            logger.error(f"保存数据失败：{e}")

    # ================== 时间工具方法 ==================

    def get_current_time_info(self) -> Dict[str, Any]:
        """获取当前时间信息"""
        return TimeUtils.get_current_datetime()

    def get_detailed_time_info(self) -> Dict[str, Any]:
        """获取详细的当前时间信息"""
        return TimeUtils.get_detailed_time_info()

    def get_time_until_next_period(self) -> Dict[str, Any]:
        """获取距离下一个时间段的剩余时间"""
        return TimeUtils.get_time_until_next_period()

    def get_week_progress(self) -> Dict[str, Any]:
        """获取本周进度信息"""
        return TimeUtils.get_week_progress()

    def get_date_info(self, date_str: str) -> Dict[str, Any]:
        """获取指定日期信息"""
        return TimeUtils.get_date_info(date_str)

    def parse_relative_date(self, relative_term: str) -> str:
        """解析相对日期"""
        return TimeUtils.parse_relative_date(relative_term)

    def get_week_number(self, target_date: str) -> int:
        """获取指定日期是第几周"""
        return TimeUtils.calculate_week_number(self.data.start_date, target_date)

    # ================== 日程管理方法 ==================

    def add_daily_task(
        self,
        task_name: str,
        date_str: str,
        start_time: str,
        end_time: str,
        description: str = "",
        can_reschedule: bool = True,
        can_compress: bool = True,
        can_parallel: bool = False,
        parent_task: Optional[str] = None,
    ) -> bool:
        """添加日任务"""
        try:
            # 解析相对日期
            parsed_date = self.parse_relative_date(date_str)

            # 计算周数
            week_number = self.get_week_number(parsed_date)

            # 创建任务
            task = DailyTask(
                task_name=task_name,
                belong_to_day=parsed_date,
                start_time=start_time,
                end_time=end_time,
                description=description,
                can_reschedule=can_reschedule,
                can_compress=can_compress,
                can_parallel=can_parallel,
                parent_task=parent_task,
            )

            # 确保日程存在
            if parsed_date not in self.data.daily_schedules:
                self.data.daily_schedules[parsed_date] = DailySchedule(
                    date=parsed_date, week_number=week_number, tasks=[]
                )

            # 添加任务
            self.data.daily_schedules[parsed_date].tasks.append(task)

            # 保存数据
            self._save_data()

            logger.info(
                f"成功添加日任务：{task_name} ({parsed_date} {start_time}-{end_time})"
            )
            return True

        except Exception as e:
            logger.error(f"添加日任务失败：{e}")
            return False

    def add_weekly_task(
        self,
        task_name: str,
        week_number: Union[int, str],  # 允许字符串输入
        description: str = "",
        parent_project: Optional[str] = None,
        priority: Union[Priority, str] = Priority.MEDIUM,
    ) -> bool:
        """添加周任务"""
        try:
            # 处理周数参数 - 确保是整数
            if isinstance(week_number, str):
                # 处理特殊字符串
                if week_number.lower() in ["current", "本周", "this_week"]:
                    current_time = self.get_current_time_info()
                    week_number = self.get_week_number(current_time["current_date"])
                else:
                    try:
                        week_number = int(week_number)
                    except ValueError:
                        logger.warning(f"无法解析周数 '{week_number}'，使用当前周")
                        current_time = self.get_current_time_info()
                        week_number = self.get_week_number(current_time["current_date"])

            # 处理优先级参数
            if isinstance(priority, str):
                priority = Priority(priority)

            # 创建任务
            task = WeeklyTask(
                task_name=task_name,
                belong_to_week=week_number,
                description=description,
                parent_project=parent_project,
                priority=priority,
            )

            # 确保周计划存在
            if week_number not in self.data.weekly_schedules:
                date_range = TimeUtils.get_week_date_range(
                    self.data.start_date, week_number
                )
                self.data.weekly_schedules[week_number] = WeeklySchedule(
                    week_number=week_number, date_range=date_range, tasks=[]
                )

            # 添加任务
            self.data.weekly_schedules[week_number].tasks.append(task)

            # 按优先级排序
            self.data.weekly_schedules[week_number].tasks.sort(
                key=lambda t: ["critical", "high", "medium", "low"].index(
                    t.priority.value
                )
            )

            # 保存数据
            self._save_data()

            logger.info(
                f"成功添加周任务：{task_name} (第{week_number}周，优先级：{priority.value})"
            )
            return True

        except Exception as e:
            logger.error(f"添加周任务失败：{e}")
            return False

    def get_daily_schedule(self, date_str: str) -> Optional[DailySchedule]:
        """获取指定日期的日程"""
        parsed_date = self.parse_relative_date(date_str)
        return self.data.daily_schedules.get(parsed_date)

    def get_weekly_schedule(self, week_number: int) -> Optional[WeeklySchedule]:
        """获取指定周的计划"""
        return self.data.weekly_schedules.get(week_number)

    def get_date_range_schedules(
        self, start_date: str, end_date: str
    ) -> Dict[str, DailySchedule]:
        """获取日期范围内的日程"""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()

            result = {}
            current = start
            while current <= end:
                date_str = current.strftime("%Y-%m-%d")
                if date_str in self.data.daily_schedules:
                    result[date_str] = self.data.daily_schedules[date_str]
                current += timedelta(days=1)

            return result
        except Exception as e:
            logger.error(f"获取日期范围日程失败：{e}")
            return {}

    def remove_daily_task(self, date_str: str, task_name: str) -> bool:
        """删除日任务"""
        try:
            parsed_date = self.parse_relative_date(date_str)
            if parsed_date in self.data.daily_schedules:
                schedule = self.data.daily_schedules[parsed_date]
                original_count = len(schedule.tasks)
                schedule.tasks = [t for t in schedule.tasks if t.task_name != task_name]

                if len(schedule.tasks) < original_count:
                    self._save_data()
                    logger.info(f"成功删除日任务：{task_name} ({parsed_date})")
                    return True

            logger.warning(f"未找到要删除的日任务：{task_name} ({parsed_date})")
            return False

        except Exception as e:
            logger.error(f"删除日任务失败：{e}")
            return False

    def remove_weekly_task(self, week_number: int, task_name: str) -> bool:
        """删除周任务"""
        try:
            if week_number in self.data.weekly_schedules:
                schedule = self.data.weekly_schedules[week_number]
                original_count = len(schedule.tasks)
                schedule.tasks = [t for t in schedule.tasks if t.task_name != task_name]

                if len(schedule.tasks) < original_count:
                    self._save_data()
                    logger.info(f"成功删除周任务：{task_name} (第{week_number}周)")
                    return True

            logger.warning(f"未找到要删除的周任务：{task_name} (第{week_number}周)")
            return False

        except Exception as e:
            logger.error(f"删除周任务失败：{e}")
            return False

    def update_daily_task(
        self, date_str: str, task_name: str, updates: Dict[str, Any]
    ) -> bool:
        """更新日任务"""
        try:
            parsed_date = self.parse_relative_date(date_str)
            if parsed_date in self.data.daily_schedules:
                schedule = self.data.daily_schedules[parsed_date]

                for task in schedule.tasks:
                    if task.task_name == task_name:
                        # 更新任务属性
                        for key, value in updates.items():
                            if hasattr(task, key):
                                setattr(task, key, value)

                        self._save_data()
                        logger.info(f"成功更新日任务：{task_name} ({parsed_date})")
                        return True

            logger.warning(f"未找到要更新的日任务：{task_name} ({parsed_date})")
            return False

        except Exception as e:
            logger.error(f"更新日任务失败：{e}")
            return False

    def update_weekly_task(
        self, week_number: int, task_name: str, updates: Dict[str, Any]
    ) -> bool:
        """更新周任务"""
        try:
            if week_number in self.data.weekly_schedules:
                schedule = self.data.weekly_schedules[week_number]

                for task in schedule.tasks:
                    if task.task_name == task_name:
                        # 更新任务属性
                        for key, value in updates.items():
                            if hasattr(task, key):
                                if key == "priority" and isinstance(value, str):
                                    setattr(task, key, Priority(value))
                                else:
                                    setattr(task, key, value)

                        # 重新排序
                        schedule.tasks.sort(
                            key=lambda t: ["critical", "high", "medium", "low"].index(
                                t.priority.value
                            )
                        )

                        self._save_data()
                        logger.info(f"成功更新周任务：{task_name} (第{week_number}周)")
                        return True

            logger.warning(f"未找到要更新的周任务：{task_name} (第{week_number}周)")
            return False

        except Exception as e:
            logger.error(f"更新周任务失败：{e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_daily_tasks = sum(
            len(schedule.tasks) for schedule in self.data.daily_schedules.values()
        )
        total_weekly_tasks = sum(
            len(schedule.tasks) for schedule in self.data.weekly_schedules.values()
        )

        return {
            "start_date": self.data.start_date,
            "total_daily_schedules": len(self.data.daily_schedules),
            "total_weekly_schedules": len(self.data.weekly_schedules),
            "total_daily_tasks": total_daily_tasks,
            "total_weekly_tasks": total_weekly_tasks,
            "data_file_size": (
                os.path.getsize(self.data_file) if os.path.exists(self.data_file) else 0
            ),
        }

    def export_json(self, output_file: Optional[str] = None) -> str:
        """导出为JSON格式"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"time_management_export_{timestamp}.json"

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.data.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"成功导出数据到：{output_file}")
            return output_file
        except Exception as e:
            logger.error(f"导出数据失败：{e}")
            return ""
