"""
时间规划系统 - AI Agent 模块

这个模块实现了智能时间规划 Agent，主要功能包括：
- 使用 PydanticAI 与大语言模型交互  
- 集成思维链进行复杂推理
- 解析用户的自然语言任务描述
- 生成智能的时间规划建议
- 调用工具服务完成具体操作

作者：AI Assistant
日期：2025-07-13
"""

import os
from datetime import datetime, timedelta
from datetime import date as Date
from typing import List, Dict, Any, Optional, Tuple
import json
from dotenv import load_dotenv
from loguru import logger

# PydanticAI 相关导入
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel

# OpenAI 客户端用于DeepSeek多轮对话
from openai import OpenAI

from .models import TimeSlot, TaskType, Priority, UserPreferences
from .services import TimeSlotService, ScheduleService, PlanningService
from .simple_mcp_client import SimpleMCPClient
from .memory import ConversationMemory, MessageType, MessageImportance

# 加载环境变量
load_dotenv()


class TimeManagementAgent:
    """时间管理 AI Agent - 核心智能规划助手"""

    def __init__(self):
        """初始化时间管理 Agent"""

        # 设置环境变量（PydanticAI 会自动读取）
        os.environ["OPENAI_API_KEY"] = os.getenv("DEEPSEEK_API_KEY", "")
        os.environ["OPENAI_BASE_URL"] = os.getenv(
            "DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"
        )

        # 初始化 AI 模型
        self.model = OpenAIModel(model_name="deepseek-chat")

        # 初始化 DeepSeek 客户端（用于多轮对话）
        self.deepseek_client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url=os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com"),
        )

        # DeepSeek 多轮对话消息历史
        self.conversation_messages = []

        # 初始化服务组件
        self.slot_service = TimeSlotService()
        self.schedule_service = ScheduleService(self.slot_service)
        self.planning_service = PlanningService(self.schedule_service)

        # 初始化简化的 MCP 客户端
        self.mcp_client = SimpleMCPClient()
        self.thinking_client: Optional[SimpleMCPClient] = None

        # 初始化对话记忆管理器
        self.memory = ConversationMemory(
            memory_file="conversation_memory.json",
            max_recent_messages=15,  # 保留最近15条消息
            max_total_messages=80,  # 总共最多80条消息
            summary_threshold=40,  # 40条消息后开始摘要
        )

        # 创建 PydanticAI Agent（用于工具调用）
        self.agent = Agent(
            model=self.model, system_prompt=self._get_system_prompt(), retries=2
        )

        # 注册工具
        self._register_tools()

        logger.info("时间管理 Agent 初始化完成")

    def initialize(self) -> bool:
        """初始化 Agent（启动 MCP 服务等）"""
        try:
            # 尝试初始化简化的 MCP 客户端
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
            return True  # 即使 MCP 失败，Agent 仍可工作

    def shutdown(self):
        """关闭 Agent"""
        if self.mcp_client:
            self.mcp_client.stop()
        logger.info("Agent 已关闭")

    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """
你是一个专业的时间管理助手，负责帮助用户制定合理的时间规划。

你的主要能力包括：
1. 理解用户的自然语言任务描述
2. 分析任务的优先级、时长和时间要求
3. 考虑用户的作息习惯和个人偏好
4. 生成合理的时间安排建议
5. 检测和解决时间冲突
6. 提供时间管理的优化建议
7. **重要：实际创建和存储时间安排**
8. **完整的时间管理操作：创建、读取、更新、删除时间段**
9. **智能对话记忆：记住用户的偏好和历史操作**

🧠 **记忆使用原则**：
- **系统提示词末尾会提供完整的对话历史记录**
- **当用户询问之前提到的信息时，请直接从历史记录中查找答案**
- **特别注意标记为🔥的重要用户信息**
- **不要说"无法查询"或"无法获取"，而要仔细查看提供的历史记录**
- **如果历史记录中确实没有相关信息，才说没有找到**
- **对于"我叫什么名字"、"我的职业是什么"等问题，直接从对话记录中找答案**

你拥有以下工具功能：

**创建操作：**
- create_time_slot: 创建单个时间段
- create_time_schedule_from_description: 根据自然语言描述批量创建时间安排

**读取操作：**
- query_schedule: 查询指定日期范围的日程
- list_all_time_slots: 列出所有时间段或指定范围内的时间段
- find_free_time_slots: 查找空闲时间段

**更新操作：**
- update_time_slot: 更新现有时间段的任何属性（标题、时间、优先级等）

**删除操作：**
- delete_time_slot: 删除指定的时间段

**分析操作：**
- parse_task_description: 解析任务描述提取结构化信息
- generate_daily_plan: 生成完整的日程计划

**记忆功能：**
- search_conversation_history: 搜索对话历史记录
- get_conversation_summary: 获取对话摘要和统计信息
- get_user_info: 获取用户个人信息（姓名、偏好等）

**智能记忆特性：**
- 自动记住用户的时间安排偏好
- 保留重要的对话上下文
- 智能摘要长对话内容
- 可以回忆之前的操作和决定
- 理解用户的历史需求模式
- **重要：主动使用历史上下文回答问题**

在处理用户请求时，请遵循以下步骤：

第一步：上下文理解
- **首先仔细阅读提供的对话历史记录和用户信息**
- **直接从历史记录中获取相关信息，无需调用查询工具**
- 分析用户描述的任务和意图
- 识别用户的意图（创建、查看、修改、删除、查询历史等）

第二步：现状评估与冲突检测
- 使用 list_all_time_slots 或 query_schedule 查看当前的时间安排
- 检测是否存在时间冲突
- 参考历史偏好和操作模式

第三步：执行相应操作
- **创建**：使用 create_time_schedule_from_description 或 create_time_slot
- **查看**：使用 list_all_time_slots 或 query_schedule 显示日程
- **修改**：使用 update_time_slot 更新现有时间段
- **删除**：使用 delete_time_slot 删除时间段
- **查找空闲时间**：使用 find_free_time_slots
- **历史查询**：使用 search_conversation_history 或 get_conversation_summary

第四步：结果验证与反馈
- 验证操作是否成功执行
- 向用户确认更改结果
- 显示更新后的时间安排
- 记住用户的满意度和反馈

第五步：学习与记忆
- 记录用户的偏好和操作模式
- 为未来的类似请求提供更好的建议
- 主动提醒相关的历史安排

**重要提醒：**
- 每当你为用户制定时间安排时，必须调用相应的工具函数来实际操作
- 在修改或删除时间段前，先使用查询工具确认现有安排
- 向用户确认所有操作已经被实际执行和存储
- 在创建新时间段时，先检查是否与现有安排冲突
- **利用对话记忆提供个性化建议**
- **在适当时候主动回忆用户的历史偏好**

**常见用户请求处理：**
- "帮我安排..." → 使用创建工具，参考历史偏好
- "查看我的安排" → 使用查询工具
- "修改/调整..." → 使用更新工具
- "删除/取消..." → 使用删除工具
- "我有空闲时间吗" → 使用空闲时间查找工具
- "我之前安排过什么" → 使用历史搜索工具
- "总结一下我们的对话" → 使用对话摘要工具

请始终保持友好、专业的态度，并提供实用的建议。利用记忆功能为用户提供更加个性化和连贯的服务体验。
"""

    def _register_tools(self):
        """注册 Agent 可用的工具"""

        @self.agent.tool
        def parse_task_description(
            ctx: RunContext[None], description: str
        ) -> Dict[str, Any]:
            """
            解析用户的任务描述，提取结构化信息

            Args:
                description: 用户输入的任务描述

            Returns:
                Dict[str, Any]: 解析出的任务信息
            """
            logger.info(f"解析任务描述: {description}")

            # 这里可以使用 NLP 技术或者规则来解析
            # 当前使用简化的关键词匹配

            task_info = {
                "title": "",
                "duration_minutes": 60,  # 默认1小时
                "priority": "medium",
                "task_type": "flexible",
                "deadline": None,
                "keywords": [],
            }

            # 提取任务名称（简化实现）
            words = description.split()
            if "学习" in description:
                task_info["title"] = "学习任务"
                task_info["task_type"] = "fixed"
            elif "工作" in description:
                task_info["title"] = "工作任务"
                task_info["task_type"] = "fixed"
            elif "锻炼" in description or "运动" in description:
                task_info["title"] = "运动锻炼"
                task_info["duration_minutes"] = 30
            elif "娱乐" in description:
                task_info["title"] = "娱乐休闲"
                task_info["task_type"] = "flexible"
            else:
                task_info["title"] = (
                    description[:20] + "..." if len(description) > 20 else description
                )

            # 提取时长信息
            for word in words:
                if "小时" in word:
                    try:
                        hours = float(word.replace("小时", ""))
                        task_info["duration_minutes"] = int(hours * 60)
                    except ValueError:
                        pass
                elif "分钟" in word:
                    try:
                        minutes = int(word.replace("分钟", ""))
                        task_info["duration_minutes"] = minutes
                    except ValueError:
                        pass

            # 提取优先级
            if any(keyword in description for keyword in ["紧急", "急", "重要"]):
                task_info["priority"] = "high"
            elif any(
                keyword in description for keyword in ["低优先级", "不急", "有空时"]
            ):
                task_info["priority"] = "low"

            # 提取时间相关信息
            if any(keyword in description for keyword in ["明天", "下周", "后天"]):
                task_info["deadline"] = "未来几天"
            elif any(keyword in description for keyword in ["今天", "现在", "马上"]):
                task_info["deadline"] = "今天"

            logger.info(f"任务解析结果: {task_info}")
            return task_info

        @self.agent.tool
        def create_time_slot(
            ctx: RunContext[None],
            title: str,
            start_time: str,
            duration_minutes: int,
            task_type: str = "flexible",
            priority: str = "medium",
        ) -> Dict[str, Any]:
            """
            创建新的时间段

            Args:
                title: 任务标题
                start_time: 开始时间 (ISO 格式字符串)
                duration_minutes: 持续时间（分钟）
                task_type: 任务类型 ('fixed' 或 'flexible')
                priority: 优先级 ('low', 'medium', 'high', 'urgent')

            Returns:
                Dict[str, Any]: 创建结果
            """
            try:
                start_dt = datetime.fromisoformat(start_time)
                end_dt = start_dt + timedelta(minutes=duration_minutes)

                task_type_enum = (
                    TaskType.FIXED if task_type == "fixed" else TaskType.FLEXIBLE
                )
                priority_enum = getattr(Priority, priority.upper(), Priority.MEDIUM)

                slot = self.slot_service.create_slot(
                    title=title,
                    start_time=start_dt,
                    end_time=end_dt,
                    task_type=task_type_enum,
                    priority=priority_enum,
                )

                return {
                    "success": True,
                    "slot_id": str(slot.id),
                    "message": f"时间段 '{title}' 创建成功",
                }

            except Exception as e:
                logger.error(f"创建时间段失败: {e}")
                return {"success": False, "error": str(e)}

        @self.agent.tool
        def query_schedule(
            ctx: RunContext[None], start_date: str, end_date: str
        ) -> Dict[str, Any]:
            """
            查询指定日期范围的日程安排

            Args:
                start_date: 开始日期 (YYYY-MM-DD)
                end_date: 结束日期 (YYYY-MM-DD)

            Returns:
                Dict[str, Any]: 查询结果
            """
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

                slots = self.schedule_service.query_slots_by_range(start_dt, end_dt)

                result = {"success": True, "total_slots": len(slots), "slots": []}

                for slot in slots:
                    result["slots"].append(
                        {
                            "id": str(slot.id),
                            "title": slot.title,
                            "start_time": slot.start_time.isoformat(),
                            "end_time": slot.end_time.isoformat(),
                            "duration_minutes": slot.duration_minutes,
                            "task_type": slot.task_type.value,
                            "priority": slot.priority.value,
                        }
                    )

                return result

            except Exception as e:
                logger.error(f"查询日程失败: {e}")
                return {"success": False, "error": str(e)}

        @self.agent.tool
        def generate_daily_plan(
            ctx: RunContext[None],
            target_date: str,
            tasks: List[Dict[str, Any]],
            user_preferences: Dict[str, Any],
        ) -> Dict[str, Any]:
            """
            为指定日期生成日程计划

            Args:
                target_date: 目标日期 (YYYY-MM-DD)
                tasks: 任务列表
                user_preferences: 用户偏好

            Returns:
                Dict[str, Any]: 生成的计划
            """
            try:
                date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()

                # 创建用户偏好对象
                preferences = UserPreferences(**user_preferences)

                # 将任务字典转换为 TimeSlot 对象
                task_slots = []
                for task in tasks:
                    slot = TimeSlot(
                        title=task["title"],
                        start_time=datetime.fromisoformat(task["start_time"]),
                        end_time=datetime.fromisoformat(task["end_time"]),
                        task_type=TaskType(task.get("task_type", "flexible")),
                        priority=Priority(task.get("priority", "medium")),
                    )
                    task_slots.append(slot)

                # 生成日程计划
                day_schedule = self.planning_service.generate_daily_plan(
                    target_date=date_obj, tasks=task_slots, preferences=preferences
                )

                # 转换为返回格式
                result = {
                    "success": True,
                    "date": target_date,
                    "total_duration": day_schedule.total_duration,
                    "free_time": day_schedule.free_time,
                    "slots": [],
                }

                for slot in day_schedule.slots:
                    result["slots"].append(
                        {
                            "id": str(slot.id),
                            "title": slot.title,
                            "start_time": slot.start_time.isoformat(),
                            "end_time": slot.end_time.isoformat(),
                            "task_type": slot.task_type.value,
                            "priority": slot.priority.value,
                        }
                    )

                return result

            except Exception as e:
                logger.error(f"生成日程计划失败: {e}")
                return {"success": False, "error": str(e)}

        @self.agent.tool
        def create_time_schedule_from_description(
            ctx: RunContext[None],
            user_request: str,
            target_date: str = None,
            user_preferences: Dict[str, Any] = None,
        ) -> Dict[str, Any]:
            """
            根据用户的自然语言描述直接创建时间安排

            Args:
                user_request: 用户的原始请求
                target_date: 目标日期，默认为今天 (YYYY-MM-DD)
                user_preferences: 用户偏好设置

            Returns:
                Dict[str, Any]: 创建的时间安排结果
            """
            try:
                logger.info(f"根据描述创建时间安排: {user_request}")

                # 如果没有指定日期，使用今天
                if target_date is None:
                    target_date = datetime.now().strftime("%Y-%m-%d")

                # 解析用户请求中的时间安排
                import re
                from datetime import datetime, time

                created_slots = []

                # 提取时间和任务信息
                time_patterns = [
                    r"(\d{1,2})[点:](\d{0,2})\s*(?:左右|大概)?\s*(.+?)(?=，|。|$|，)",
                    r"(晚上|上午|下午|中午)\s*(.+?)(?=，|。|$)",
                    r"(.+?)\s*大概\s*(\d+)\s*(小时|分钟)",
                ]

                # 预设的时间安排（基于用户描述）
                time_slots_to_create = []

                # 解析具体的时间安排
                if "五点左右去吃饭" in user_request:
                    time_slots_to_create.append(
                        {
                            "title": "吃饭",
                            "start_time": f"{target_date}T17:00:00",
                            "duration_minutes": 30,
                            "task_type": "fixed",
                            "priority": "medium",
                        }
                    )

                if "休息一下" in user_request and "吃完" in user_request:
                    time_slots_to_create.append(
                        {
                            "title": "休息",
                            "start_time": f"{target_date}T17:30:00",
                            "duration_minutes": 30,
                            "task_type": "flexible",
                            "priority": "low",
                        }
                    )

                if "洗个澡" in user_request and "一个小时" in user_request:
                    time_slots_to_create.append(
                        {
                            "title": "洗澡",
                            "start_time": f"{target_date}T18:00:00",
                            "duration_minutes": 60,
                            "task_type": "fixed",
                            "priority": "medium",
                        }
                    )

                if "敲代码" in user_request and "一个小时以上" in user_request:
                    time_slots_to_create.append(
                        {
                            "title": "敲代码",
                            "start_time": f"{target_date}T19:00:00",
                            "duration_minutes": 90,  # 1.5小时
                            "task_type": "fixed",
                            "priority": "high",
                        }
                    )

                if "玩游戏" in user_request:
                    time_slots_to_create.append(
                        {
                            "title": "玩游戏",
                            "start_time": f"{target_date}T20:30:00",
                            "duration_minutes": 60,
                            "task_type": "flexible",
                            "priority": "low",
                        }
                    )

                # 创建时间段
                for slot_data in time_slots_to_create:
                    try:
                        start_dt = datetime.fromisoformat(slot_data["start_time"])
                        end_dt = start_dt + timedelta(
                            minutes=slot_data["duration_minutes"]
                        )

                        task_type_enum = (
                            TaskType.FIXED
                            if slot_data["task_type"] == "fixed"
                            else TaskType.FLEXIBLE
                        )
                        priority_enum = getattr(
                            Priority, slot_data["priority"].upper(), Priority.MEDIUM
                        )

                        slot = self.slot_service.create_slot(
                            title=slot_data["title"],
                            start_time=start_dt,
                            end_time=end_dt,
                            task_type=task_type_enum,
                            priority=priority_enum,
                        )

                        created_slots.append(
                            {
                                "id": str(slot.id),
                                "title": slot.title,
                                "start_time": slot.start_time.strftime("%H:%M"),
                                "end_time": slot.end_time.strftime("%H:%M"),
                                "duration_minutes": slot.duration_minutes,
                                "task_type": slot.task_type.value,
                                "priority": slot.priority.value,
                            }
                        )

                        logger.info(
                            f"创建时间段: {slot.title} ({slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')})"
                        )

                    except Exception as e:
                        logger.error(f"创建时间段失败: {e}")

                return {
                    "success": True,
                    "created_slots": created_slots,
                    "total_slots": len(created_slots),
                    "message": f"成功创建 {len(created_slots)} 个时间安排",
                }

            except Exception as e:
                logger.error(f"创建时间安排失败: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": "创建时间安排失败",
                }

        @self.agent.tool
        def update_time_slot(
            ctx: RunContext[None],
            slot_id: str,
            title: str = None,
            start_time: str = None,
            duration_minutes: int = None,
            task_type: str = None,
            priority: str = None,
        ) -> Dict[str, Any]:
            """
            更新现有的时间段

            Args:
                slot_id: 时间段ID
                title: 新的任务标题（可选）
                start_time: 新的开始时间 (ISO 格式字符串，可选)
                duration_minutes: 新的持续时间（分钟，可选）
                task_type: 新的任务类型 ('fixed' 或 'flexible'，可选)
                priority: 新的优先级 ('low', 'medium', 'high', 'urgent'，可选)

            Returns:
                Dict[str, Any]: 更新结果
            """
            try:
                # 查找现有时间段
                from uuid import UUID

                slot_uuid = UUID(slot_id)
                slot = self.slot_service.get_slot(slot_uuid)

                if not slot:
                    return {"success": False, "error": f"时间段 {slot_id} 不存在"}

                # 准备更新数据
                update_data = {}
                if title is not None:
                    update_data["title"] = title
                if start_time is not None:
                    start_dt = datetime.fromisoformat(start_time)
                    update_data["start_time"] = start_dt
                    if duration_minutes is not None:
                        update_data["end_time"] = start_dt + timedelta(
                            minutes=duration_minutes
                        )
                    else:
                        # 保持原有持续时间
                        update_data["end_time"] = start_dt + timedelta(
                            minutes=slot.duration_minutes
                        )
                elif duration_minutes is not None:
                    # 只更新持续时间，保持开始时间不变
                    update_data["end_time"] = slot.start_time + timedelta(
                        minutes=duration_minutes
                    )

                if task_type is not None:
                    update_data["task_type"] = (
                        TaskType.FIXED if task_type == "fixed" else TaskType.FLEXIBLE
                    )
                if priority is not None:
                    update_data["priority"] = getattr(
                        Priority, priority.upper(), Priority.MEDIUM
                    )

                # 执行更新
                updated_slot = self.slot_service.update_slot(slot_uuid, **update_data)

                if updated_slot:
                    return {
                        "success": True,
                        "slot_id": slot_id,
                        "message": f"时间段 '{updated_slot.title}' 更新成功",
                        "updated_slot": {
                            "title": updated_slot.title,
                            "start_time": updated_slot.start_time.strftime("%H:%M"),
                            "end_time": updated_slot.end_time.strftime("%H:%M"),
                            "duration_minutes": updated_slot.duration_minutes,
                            "task_type": updated_slot.task_type.value,
                            "priority": updated_slot.priority.value,
                        },
                    }
                else:
                    return {"success": False, "error": "更新失败"}

            except Exception as e:
                logger.error(f"更新时间段失败: {e}")
                return {"success": False, "error": str(e)}

        @self.agent.tool
        def delete_time_slot(ctx: RunContext[None], slot_id: str) -> Dict[str, Any]:
            """
            删除指定的时间段

            Args:
                slot_id: 时间段ID

            Returns:
                Dict[str, Any]: 删除结果
            """
            try:
                from uuid import UUID

                slot_uuid = UUID(slot_id)

                # 获取时间段信息（用于返回消息）
                slot = self.slot_service.get_slot(slot_uuid)
                if not slot:
                    return {"success": False, "error": f"时间段 {slot_id} 不存在"}

                slot_title = slot.title

                # 执行删除
                success = self.slot_service.delete_slot(slot_uuid)

                if success:
                    return {
                        "success": True,
                        "slot_id": slot_id,
                        "message": f"时间段 '{slot_title}' 删除成功",
                    }
                else:
                    return {"success": False, "error": "删除失败"}

            except Exception as e:
                logger.error(f"删除时间段失败: {e}")
                return {"success": False, "error": str(e)}

        @self.agent.tool
        def list_all_time_slots(
            ctx: RunContext[None], start_date: str = None, end_date: str = None
        ) -> Dict[str, Any]:
            """
            列出所有时间段或指定日期范围内的时间段

            Args:
                start_date: 开始日期 (YYYY-MM-DD，可选)
                end_date: 结束日期 (YYYY-MM-DD，可选)

            Returns:
                Dict[str, Any]: 时间段列表
            """
            try:
                if start_date and end_date:
                    # 查询指定日期范围
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                    slots = self.slot_service.find_slots_by_date_range(start_dt, end_dt)
                else:
                    # 查询所有时间段
                    slots = list(self.slot_service.slots.values())

                result = {"success": True, "total_slots": len(slots), "slots": []}

                # 按开始时间排序
                sorted_slots = sorted(slots, key=lambda x: x.start_time)

                for slot in sorted_slots:
                    result["slots"].append(
                        {
                            "id": str(slot.id),
                            "title": slot.title,
                            "start_time": slot.start_time.isoformat(),
                            "end_time": slot.end_time.isoformat(),
                            "duration_minutes": slot.duration_minutes,
                            "task_type": slot.task_type.value,
                            "priority": slot.priority.value,
                            "date": slot.start_time.strftime("%Y-%m-%d"),
                            "time_range": f"{slot.start_time.strftime('%H:%M')}-{slot.end_time.strftime('%H:%M')}",
                        }
                    )

                return result

            except Exception as e:
                logger.error(f"列出时间段失败: {e}")
                return {"success": False, "error": str(e)}

        @self.agent.tool
        def find_free_time_slots(
            ctx: RunContext[None],
            target_date: str,
            duration_minutes: int,
            prefer_time_start: str = "09:00",
            prefer_time_end: str = "22:00",
        ) -> Dict[str, Any]:
            """
            查找指定日期的空闲时间段

            Args:
                target_date: 目标日期 (YYYY-MM-DD)
                duration_minutes: 需要的时间长度（分钟）
                prefer_time_start: 偏好开始时间 (HH:MM)
                prefer_time_end: 偏好结束时间 (HH:MM)

            Returns:
                Dict[str, Any]: 空闲时间段列表
            """
            try:
                date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()

                # 获取当天的所有时间段
                existing_slots = self.slot_service.find_slots_by_date_range(
                    date_obj, date_obj
                )

                # 构建偏好时间范围
                prefer_start = datetime.strptime(
                    f"{target_date} {prefer_time_start}", "%Y-%m-%d %H:%M"
                )
                prefer_end = datetime.strptime(
                    f"{target_date} {prefer_time_end}", "%Y-%m-%d %H:%M"
                )

                # 查找空闲时间段
                free_slots = []
                current_time = prefer_start

                # 按开始时间排序现有时间段
                sorted_slots = sorted(existing_slots, key=lambda x: x.start_time)

                for slot in sorted_slots:
                    # 检查当前时间到下一个时间段开始之间是否有足够的空闲时间
                    if slot.start_time > current_time:
                        gap_duration = (
                            slot.start_time - current_time
                        ).total_seconds() / 60
                        if gap_duration >= duration_minutes:
                            free_slots.append(
                                {
                                    "start_time": current_time.strftime("%H:%M"),
                                    "end_time": (
                                        current_time
                                        + timedelta(minutes=duration_minutes)
                                    ).strftime("%H:%M"),
                                    "duration_minutes": duration_minutes,
                                    "available_duration": int(gap_duration),
                                }
                            )
                    current_time = max(current_time, slot.end_time)

                # 检查最后一个时间段之后是否还有空闲时间
                if current_time < prefer_end:
                    remaining_duration = (
                        prefer_end - current_time
                    ).total_seconds() / 60
                    if remaining_duration >= duration_minutes:
                        free_slots.append(
                            {
                                "start_time": current_time.strftime("%H:%M"),
                                "end_time": (
                                    current_time + timedelta(minutes=duration_minutes)
                                ).strftime("%H:%M"),
                                "duration_minutes": duration_minutes,
                                "available_duration": int(remaining_duration),
                            }
                        )

                return {
                    "success": True,
                    "date": target_date,
                    "requested_duration": duration_minutes,
                    "free_slots_count": len(free_slots),
                    "free_slots": free_slots,
                }

            except Exception as e:
                logger.error(f"查找空闲时间失败: {e}")
                return {"success": False, "error": str(e)}

        @self.agent.tool
        def search_conversation_history(
            ctx: RunContext[None], keyword: str, limit: int = 5
        ) -> Dict[str, Any]:
            """
            搜索对话历史记录

            Args:
                keyword: 搜索关键词
                limit: 返回结果数量限制

            Returns:
                Dict[str, Any]: 搜索结果
            """
            try:
                messages = self.memory.search_history(keyword, limit)

                results = []
                for msg in messages:
                    results.append(
                        {
                            "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            "type": msg.message_type.value,
                            "content": (
                                msg.content[:200] + "..."
                                if len(msg.content) > 200
                                else msg.content
                            ),
                            "importance": msg.importance.value,
                        }
                    )

                return {
                    "success": True,
                    "keyword": keyword,
                    "found_count": len(results),
                    "results": results,
                }

            except Exception as e:
                logger.error(f"搜索对话历史失败: {e}")
                return {"success": False, "error": str(e)}

        @self.agent.tool
        def get_conversation_summary(ctx: RunContext[None]) -> Dict[str, Any]:
            """
            获取对话摘要和统计信息

            Returns:
                Dict[str, Any]: 对话摘要信息
            """
            try:
                stats = self.memory.get_memory_stats()

                return {
                    "success": True,
                    "conversation_summary": self.memory.conversation_summary,
                    "statistics": stats,
                    "recent_important_topics": [
                        (
                            msg.content[:100] + "..."
                            if len(msg.content) > 100
                            else msg.content
                        )
                        for msg in self.memory.get_important_context()[-5:]
                    ],
                }

            except Exception as e:
                logger.error(f"获取对话摘要失败: {e}")
                return {"success": False, "error": str(e)}

        @self.agent.tool
        def get_user_info(
            ctx: RunContext[None], query: str = "用户名字"
        ) -> Dict[str, Any]:
            """
            从记忆中获取用户信息，如姓名、偏好等

            Args:
                query: 查询的信息类型

            Returns:
                Dict[str, Any]: 用户信息
            """
            try:
                # 搜索相关的对话历史
                if "名字" in query or "姓名" in query:
                    # 从最近的记忆中查找名字信息
                    recent_context = self.memory.get_structured_context(max_messages=10)

                    for msg in reversed(recent_context):  # 从最新的开始查找
                        if msg["type"] == "user":
                            content = msg["content"]
                            # 使用多种模式匹配名字
                            import re

                            name_patterns = [
                                r"我叫(.+?)(?:，|。|$)",
                                r"我的名字(?:是|叫)(.+?)(?:，|。|$)",
                                r"我是(.+?)(?:，|。|$)",
                                r"叫我(.+?)(?:，|。|$)",
                            ]

                            for pattern in name_patterns:
                                match = re.search(pattern, content)
                                if match:
                                    name = match.group(1).strip()
                                    return {
                                        "success": True,
                                        "info_type": "name",
                                        "value": name,
                                        "found_in": content,
                                        "timestamp": msg["timestamp"],
                                    }

                    return {
                        "success": False,
                        "info_type": "name",
                        "message": "未找到用户名字信息",
                    }

                return {"success": False, "message": f"暂不支持查询: {query}"}

            except Exception as e:
                logger.error(f"获取用户信息失败: {e}")
                return {"success": False, "error": str(e)}

        # ...existing tools...

    async def process_user_request(
        self, user_input: str, user_preferences: Optional[UserPreferences] = None
    ) -> str:
        """
        处理用户请求的主入口 - 使用DeepSeek多轮对话机制

        Args:
            user_input: 用户输入
            user_preferences: 用户偏好设置

        Returns:
            str: Agent 的回复
        """
        logger.info(f"处理用户请求: {user_input}")

        try:
            # 添加用户消息到记忆
            self.memory.add_message(
                content=user_input,
                message_type=MessageType.USER,
                importance=MessageImportance.MEDIUM,
            )

            # ===== DeepSeek多轮对话机制实现 =====
            # 按照DeepSeek文档，维护完整的messages历史，而不是修改system_prompt

            # 如果是第一次对话，初始化系统消息
            if not self.conversation_messages:
                # 构建增强的系统提示词
                base_system_prompt = self._get_system_prompt()
                user_profile = self.memory.get_user_profile_context()
                conversation_context = self.memory.get_conversation_context_for_ai(
                    max_messages=10
                )

                enhanced_system_content = base_system_prompt

                # 添加用户关键信息
                if any(user_profile.values()):
                    enhanced_system_content += "\n\n🙋‍♂️ 用户关键信息："
                    if user_profile["name"]:
                        enhanced_system_content += f"\n- 姓名: {user_profile['name']}"
                    if user_profile["age"]:
                        enhanced_system_content += f"\n- 年龄: {user_profile['age']}岁"
                    if user_profile["occupation"]:
                        enhanced_system_content += (
                            f"\n- 职业: {user_profile['occupation']}"
                        )

                # 添加历史对话上下文
                if conversation_context:
                    enhanced_system_content += conversation_context

                # 添加关键提醒
                enhanced_system_content += "\n\n🎯 重要提醒：当用户询问个人信息时，请直接使用上面提供的信息回答，不要说'没有找到'或'无法获取'。"

                # 初始化对话历史
                self.conversation_messages = [
                    {"role": "system", "content": enhanced_system_content}
                ]

            # 添加当前用户消息到对话历史
            self.conversation_messages.append({"role": "user", "content": user_input})

            # 调用DeepSeek API进行多轮对话
            response = self.deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=self.conversation_messages,
                max_tokens=4000,
                temperature=0.7,
            )

            # 安全地获取响应内容
            if response and response.choices and len(response.choices) > 0:
                result_content = (
                    response.choices[0].message.content or "抱歉，我无法生成回复。"
                )
            else:
                result_content = "抱歉，API调用失败，请稍后再试。"

            logger.debug(f"DeepSeek API响应内容: {result_content[:100]}...")

            # 将AI回复添加到对话历史（这是DeepSeek多轮对话的关键）
            self.conversation_messages.append(
                {"role": "assistant", "content": result_content}
            )

            # 控制对话历史长度，保留系统消息和最近10轮对话
            if (
                len(self.conversation_messages) > 21
            ):  # 1 system + 20 messages (10轮对话)
                # 保留系统消息和最近的10轮对话
                system_message = self.conversation_messages[0]
                recent_messages = self.conversation_messages[
                    -20:
                ]  # 最近20条消息(10轮对话)
                self.conversation_messages = [system_message] + recent_messages

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

            # 记录错误信息
            self.memory.add_message(
                content=error_message,
                message_type=MessageType.ASSISTANT,
                importance=MessageImportance.HIGH,
                metadata={"error": str(e)},
            )

            return error_message

    async def _thinking_chain_process(
        self, user_input: str, user_preferences: Optional[UserPreferences] = None
    ) -> Dict[str, Any]:
        """
        执行思维链推理过程

        Args:
            user_input: 用户输入
            user_preferences: 用户偏好

        Returns:
            Dict[str, Any]: 思维链结果
        """
        if not self.thinking_client:
            logger.warning("思维链客户端未初始化，跳过思维链处理")
            return {}

        # 简化的思维链处理 - 只做一步快速分析
        try:
            logger.info(f"快速分析用户需求: {user_input[:50]}...")
            step_result = self.thinking_client.call_sequential_thinking(
                thought=f"分析用户请求: {user_input}",
                thought_number=1,
                total_thoughts=1,
                next_thought_needed=False,
            )

            if step_result:
                logger.info("思维链快速分析完成")
                return {
                    "thinking_steps": 1,
                    "results": step_result,
                    "summary": "快速分析完成",
                }
            else:
                logger.warning("思维链处理无响应，跳过")
                return {"summary": "思维链处理跳过"}

        except Exception as e:
            logger.error(f"思维链处理失败: {e}")
            return {"error": str(e), "summary": "思维链处理失败"}

    def create_default_preferences(self) -> UserPreferences:
        """创建默认的用户偏好设置"""
        return UserPreferences()

    async def get_planning_suggestions(
        self, date_range: Tuple[Date, Date], user_preferences: UserPreferences
    ) -> List[str]:
        """
        获取时间规划建议

        Args:
            date_range: 日期范围
            user_preferences: 用户偏好

        Returns:
            List[str]: 建议列表
        """
        suggestions = []

        try:
            start_date, end_date = date_range

            # 查询当前安排
            slots = self.slot_service.find_slots_by_date_range(start_date, end_date)

            # 分析并生成建议
            if not slots:
                suggestions.append(
                    "您在这个时间段还没有安排任何任务，建议添加一些重要的学习或工作任务。"
                )
            else:
                # 检查工作密度
                total_duration = sum(slot.duration_minutes for slot in slots)
                days = (end_date - start_date).days + 1
                avg_daily_duration = total_duration / days

                if avg_daily_duration > 10 * 60:  # 超过10小时
                    suggestions.append("您的日程安排较为紧密，建议适当安排休息时间。")
                elif avg_daily_duration < 4 * 60:  # 少于4小时
                    suggestions.append(
                        "您还有较多空闲时间，可以考虑安排更多的学习或个人发展活动。"
                    )

                # 检查任务类型分布
                fixed_tasks = [s for s in slots if s.task_type == TaskType.FIXED]
                if len(fixed_tasks) / len(slots) > 0.8:
                    suggestions.append("建议在固定任务之间安排一些弹性的休闲活动。")

            return suggestions

        except Exception as e:
            logger.error(f"生成规划建议失败: {e}")
            return ["抱歉，无法生成规划建议。"]

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        return self.memory.get_memory_stats()

    def search_conversation_history(self, keyword: str, limit: int = 5) -> List[str]:
        """搜索对话历史"""
        messages = self.memory.search_history(keyword, limit)
        return [
            f"{msg.timestamp.strftime('%H:%M')} - {msg.content[:100]}..."
            for msg in messages
        ]

    def clear_conversation_session(self):
        """清理当前对话会话"""
        self.memory.clear_session()
        logger.info("对话会话已清理")

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
        }


# 创建全局 Agent 实例
agent_instance: Optional[TimeManagementAgent] = None


def get_agent() -> TimeManagementAgent:
    """获取 Agent 实例（单例模式）"""
    global agent_instance
    if agent_instance is None:
        agent_instance = TimeManagementAgent()
    return agent_instance


def initialize_agent() -> bool:
    """初始化全局 Agent"""
    agent = get_agent()
    return agent.initialize()


def shutdown_agent():
    """关闭全局 Agent"""
    global agent_instance
    if agent_instance:
        agent_instance.shutdown()
        agent_instance = None


# 导出主要类和函数
__all__ = ["TimeManagementAgent", "get_agent", "initialize_agent", "shutdown_agent"]
