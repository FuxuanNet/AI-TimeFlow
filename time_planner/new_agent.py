"""
时间管理系统 - 新的AI Agent

使用DeepSeek JSON输出功能和新的数据结构

作者：AI Assistant
日期：2025-07-13
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from loguru import logger

# OpenAI 客户端用于DeepSeek多轮对话和JSON输出
from openai import OpenAI

from .new_models import TimeUtils, Priority
from .new_services import TimeManagementService
from .simple_mcp_client import SimpleMCPClient
from .memory import ConversationMemory, MessageType, MessageImportance

# 加载环境变量
load_dotenv()


class NewTimeManagementAgent:
    """新的时间管理 AI Agent"""

    def __init__(self):
        """初始化时间管理 Agent"""

        # 设置环境变量
        os.environ["OPENAI_API_KEY"] = os.getenv("DEEPSEEK_API_KEY", "")
        os.environ["OPENAI_BASE_URL"] = os.getenv(
            "DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"
        )

        # 初始化 DeepSeek 客户端
        self.deepseek_client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com"),
        )

        # DeepSeek 多轮对话消息历史
        self.conversation_messages = []

        # 初始化服务组件
        self.time_service = TimeManagementService("time_management_data.json")

        # 初始化简化的 MCP 客户端
        self.mcp_client = SimpleMCPClient()
        self.thinking_client: Optional[SimpleMCPClient] = None

        # 初始化对话记忆管理器
        self.memory = ConversationMemory(
            memory_file="conversation_memory.json",
            max_recent_messages=15,
            max_total_messages=80,
            summary_threshold=40,
        )

        logger.info("新时间管理 Agent 初始化完成")

    def initialize(self) -> bool:
        """初始化 Agent"""
        try:
            logger.info("正在初始化 MCP 服务...")
            if self.mcp_client.start_and_initialize():
                self.thinking_client = self.mcp_client
                logger.info("MCP 思维链服务已启用")
            else:
                logger.warning("MCP 服务初始化失败，将以基础模式运行")
                self.thinking_client = None

            logger.info("Agent 初始化完成")
            return True

        except Exception as e:
            logger.warning(f"MCP 服务初始化失败: {e}，将以基础模式运行")
            self.thinking_client = None
            return True

    def shutdown(self):
        """关闭 Agent"""
        if self.mcp_client:
            self.mcp_client.stop()
        logger.info("Agent 已关闭")

    def reset_conversation(self):
        """重置DeepSeek多轮对话历史"""
        self.conversation_messages = []
        logger.info("DeepSeek对话历史已重置")

    def get_conversation_status(self) -> Dict[str, Any]:
        """获取当前对话状态"""
        return {
            "conversation_rounds": len(
                [msg for msg in self.conversation_messages if msg["role"] == "user"]
            ),
            "total_messages": len(self.conversation_messages),
            "has_system_message": len(self.conversation_messages) > 0
            and self.conversation_messages[0]["role"] == "system",
            "memory_messages": self.memory.get_total_message_count(),
            "time_service_stats": self.time_service.get_statistics(),
        }

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        current_time = self.time_service.get_current_time_info()

        return f"""
你是一个专业的时间管理助手，当前时间是 {current_time['current_datetime']} ({current_time['weekday_chinese']})。

你的主要职责：
1. 帮助用户管理两种不同类型的时间表：
   - 按天管理的时间表：用于短期、紧急、具体的任务（如会议、约会、吃饭等）
   - 按周管理的时间表：用于长期、学习、复杂的项目（如学习新技能、项目开发等）

2. 智能判断任务类型：
   - 日任务特征：时间具体、周期短、需要提醒、有明确开始结束时间
   - 周任务特征：长期规划、学习类、可分解的复杂项目、优先级驱动

3. 时间相关能力：
   - 理解相对时间（今天、明天、昨天、后天、前天等）
   - 自动计算周数（从用户首次使用系统开始）
   - 处理时间冲突和并行任务
   - 提供详细的时间查询功能

4. 时间查询工具：
   - get_current_time_info(): 获取当前基础时间信息
   - get_detailed_time_info(): 获取详细时间信息（包含时间段、格式化时间等）
   - get_time_until_next_period(): 获取距离下一个时间段的剩余时间
   - get_week_progress(): 获取本周进度信息
   - get_date_info(date): 获取指定日期的详细信息
   - parse_relative_date(term): 解析相对日期词汇

5. JSON输出要求：
   当需要创建、修改时间安排时，必须输出JSON格式的结果。请在回复中包含JSON对象。

**重要时间信息：**
- 当前日期：{current_time['current_date']}
- 当前时间：{current_time['current_time']}
- 今天是：{current_time['weekday_chinese']}
- 是否周末：{'是' if current_time['is_weekend'] else '否'}

**数据结构说明：**
日任务属性：task_name, belong_to_day, start_time, end_time, description, can_reschedule, can_compress, can_parallel, parent_task
周任务属性：task_name, belong_to_week, description, parent_project, priority

**任务拆解原则：**
- 如果用户提到的任务有些部分可以并行、有些不能，请拆解成多个子任务
- 同一个大任务拆解的子任务应该有相同的parent_task或parent_project值
- 按优先级给周任务排序：critical > high > medium > low

你拥有以下时间管理工具功能：add_daily_task, add_weekly_task, get_daily_schedule, get_weekly_schedule, update_daily_task, update_weekly_task, remove_daily_task, remove_weekly_task, get_current_time_info, get_detailed_time_info, get_time_until_next_period, get_week_progress, get_date_info, parse_relative_date, get_statistics

记住要使用JSON格式输出任务安排结果！
"""

    async def process_user_request(self, user_input: str) -> str:
        """处理用户请求 - 使用DeepSeek多轮对话和JSON输出"""

        logger.info(f"处理用户请求: {user_input}")

        try:
            # 添加用户消息到记忆
            self.memory.add_message(
                content=user_input,
                message_type=MessageType.USER,
                importance=MessageImportance.MEDIUM,
            )

            # 判断请求类型
            needs_json_output = any(
                keyword in user_input.lower()
                for keyword in [
                    "安排",
                    "计划",
                    "任务",
                    "日程",
                    "提醒",
                    "学习",
                    "工作",
                    "会议",
                    "添加",
                    "创建",
                ]
            )

            # 检查是否是时间查询请求
            is_time_query = any(
                keyword in user_input.lower()
                for keyword in [
                    "现在几点",
                    "当前时间",
                    "今天几号",
                    "星期几",
                    "几点了",
                    "时间",
                    "日期",
                    "本周进度",
                    "周几",
                    "周末",
                    "还有多久",
                    "距离",
                    "什么时候",
                ]
            )

            # 如果是时间查询，先获取时间信息并添加到上下文
            time_context = ""
            if is_time_query:
                detailed_time = self.get_detailed_time_info()
                next_period = self.get_time_until_next_period()
                week_progress = self.get_week_progress()

                time_context = f"""
                
📅 当前详细时间信息：
- 完整时间：{detailed_time['formatted_time']}
- 时间段：{detailed_time['time_period']}
- 周几：{detailed_time['weekday_chinese']}
- 是否周末：{'是' if detailed_time['is_weekend'] else '否'}
- 年第几天：第{detailed_time['day_of_year']}天
- 距离{next_period['next_period']}：{next_period['message']}
- 本周进度：第{week_progress['days_passed']}天，完成{week_progress['progress_percentage']}%
"""

            # 构建系统提示词
            if not self.conversation_messages:
                base_system_prompt = self._get_system_prompt()
                user_profile = self.memory.get_user_profile_context()
                conversation_context = self.memory.get_conversation_context_for_ai(
                    max_messages=10
                )

                enhanced_system_content = base_system_prompt

                # 添加用户关键信息
                if any(user_profile.values()):
                    enhanced_system_content += "\\n\\n🙋‍♂️ 用户关键信息："
                    if user_profile["name"]:
                        enhanced_system_content += f"\\n- 姓名: {user_profile['name']}"
                    if user_profile["age"]:
                        enhanced_system_content += f"\\n- 年龄: {user_profile['age']}岁"
                    if user_profile["occupation"]:
                        enhanced_system_content += (
                            f"\\n- 职业: {user_profile['occupation']}"
                        )

                # 添加历史对话上下文
                if conversation_context:
                    enhanced_system_content += conversation_context

                # 添加时间查询上下文（如果需要）
                if time_context:
                    enhanced_system_content += time_context

                # 如果需要JSON输出，添加JSON指示
                if needs_json_output:
                    enhanced_system_content += """

🎯 JSON输出要求：
当创建或修改时间安排时，请在回复中包含JSON格式的任务数据。

JSON格式示例：
{
  "task_type": "daily" | "weekly",
  "action": "add" | "update" | "remove",
  "tasks": [
    {
      "task_name": "任务名称",
      "start_time": "HH:MM",
      "end_time": "HH:MM",
      "description": "任务描述",
      "can_parallel": true/false,
      "parent_task": "父任务名称(可选)"
    }
  ]
}

请确保输出合法的JSON格式！"""

                self.conversation_messages = [
                    {"role": "system", "content": enhanced_system_content}
                ]

            # 添加当前用户消息
            self.conversation_messages.append({"role": "user", "content": user_input})

            # 构建API调用参数
            api_params = {
                "model": "deepseek-chat",
                "messages": self.conversation_messages,
                "max_tokens": 4000,
                "temperature": 0.7,
            }

            # 如果需要JSON输出，添加response_format参数
            if needs_json_output:
                api_params["response_format"] = {"type": "json_object"}

            # 调用DeepSeek API
            response = self.deepseek_client.chat.completions.create(**api_params)

            # 安全地获取响应内容
            if response and response.choices and len(response.choices) > 0:
                result_content = (
                    response.choices[0].message.content or "抱歉，我无法生成回复。"
                )
            else:
                result_content = "抱歉，API调用失败，请稍后再试。"

            # 将AI回复添加到对话历史
            self.conversation_messages.append(
                {"role": "assistant", "content": result_content}
            )

            # 控制对话历史长度
            if len(self.conversation_messages) > 21:
                system_message = self.conversation_messages[0]
                recent_messages = self.conversation_messages[-20:]
                self.conversation_messages = [system_message] + recent_messages

            # 如果返回了JSON格式，尝试解析并执行操作
            if needs_json_output:
                try:
                    # 尝试从回复中提取JSON
                    json_data = json.loads(result_content)
                    execution_result = await self._execute_time_management_actions(
                        json_data
                    )

                    if execution_result:
                        result_content += f"\\n\\n✅ 时间安排已成功保存到系统中。\\n{execution_result}"
                except json.JSONDecodeError:
                    # 如果不是纯JSON，可能是混合回复
                    logger.debug("回复不是纯JSON格式，可能是自然语言回复")
                except Exception as e:
                    logger.error(f"执行时间管理操作失败：{e}")

            # 添加助手回复到记忆
            importance = (
                MessageImportance.HIGH
                if any(
                    keyword in result_content.lower()
                    for keyword in ["创建", "删除", "修改", "成功", "失败"]
                )
                else MessageImportance.MEDIUM
            )

            self.memory.add_message(
                content=result_content,
                message_type=MessageType.ASSISTANT,
                importance=importance,
            )

            logger.info("用户请求处理完成")
            return result_content

        except Exception as e:
            error_message = f"抱歉，处理您的请求时出现了错误：{str(e)}"
            logger.error(f"处理用户请求失败: {e}")

            self.memory.add_message(
                content=error_message,
                message_type=MessageType.ASSISTANT,
                importance=MessageImportance.HIGH,
                metadata={"error": str(e), "error_type": type(e).__name__},
            )

            return error_message

    async def _execute_time_management_actions(self, json_data: Dict[str, Any]) -> str:
        """执行时间管理操作"""
        try:
            task_type = json_data.get("task_type", "daily")
            action = json_data.get("action", "add")
            tasks = json_data.get("tasks", [])

            results = []

            for task_data in tasks:
                if task_type == "daily" and action == "add":
                    success = self.time_service.add_daily_task(
                        task_name=task_data.get("task_name", ""),
                        date_str=task_data.get(
                            "belong_to_day",
                            self.time_service.get_current_time_info()["current_date"],
                        ),
                        start_time=task_data.get("start_time", "09:00"),
                        end_time=task_data.get("end_time", "10:00"),
                        description=task_data.get("description", ""),
                        can_reschedule=task_data.get("can_reschedule", True),
                        can_compress=task_data.get("can_compress", True),
                        can_parallel=task_data.get("can_parallel", False),
                        parent_task=task_data.get("parent_task"),
                    )
                    if success:
                        results.append(
                            f"✓ 日任务 '{task_data.get('task_name')}' 已添加"
                        )

                elif task_type == "weekly" and action == "add":
                    current_time = self.time_service.get_current_time_info()
                    current_week = self.time_service.get_week_number(
                        current_time["current_date"]
                    )

                    success = self.time_service.add_weekly_task(
                        task_name=task_data.get("task_name", ""),
                        week_number=task_data.get("belong_to_week", current_week),
                        description=task_data.get("description", ""),
                        parent_project=task_data.get("parent_project"),
                        priority=Priority(task_data.get("priority", "medium")),
                    )
                    if success:
                        results.append(
                            f"✓ 周任务 '{task_data.get('task_name')}' 已添加"
                        )

            return (
                "\\n".join(results) if results else "操作完成，但没有具体任务被处理。"
            )

        except Exception as e:
            logger.error(f"执行时间管理操作失败：{e}")
            return f"执行操作时出现错误：{str(e)}"

    def get_current_time_info(self) -> Dict[str, Any]:
        """获取当前时间信息（工具函数）"""
        return self.time_service.get_current_time_info()

    def get_detailed_time_info(self) -> Dict[str, Any]:
        """获取详细的当前时间信息（工具函数）"""
        return self.time_service.get_detailed_time_info()

    def get_time_until_next_period(self) -> Dict[str, Any]:
        """获取距离下一个时间段的剩余时间（工具函数）"""
        return self.time_service.get_time_until_next_period()

    def get_week_progress(self) -> Dict[str, Any]:
        """获取本周进度信息（工具函数）"""
        return self.time_service.get_week_progress()

    def get_date_info(self, date_str: str) -> Dict[str, Any]:
        """获取指定日期信息（工具函数）"""
        return self.time_service.get_date_info(date_str)

    def get_schedule_summary(self, date_str: Optional[str] = None) -> str:
        """获取日程摘要"""
        if not date_str:
            current_time = self.time_service.get_current_time_info()
            date_str = current_time["current_date"]

        schedule = self.time_service.get_daily_schedule(date_str)
        if schedule:
            tasks_info = []
            for task in schedule.tasks:
                tasks_info.append(
                    f"- {task.task_name} ({task.start_time}-{task.end_time})"
                )
            return f"{date_str} 的日程：\\n" + "\\n".join(tasks_info)
        else:
            return f"{date_str} 暂无安排的日程。"
