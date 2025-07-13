"""
时间规划系统 - 命令行界面

这个模块提供了用户友好的命令行界面，让用户可以通过简单的文本交互
来使用时间规划系统的所有功能。

主要功能：
- 接收用户的自然语言输入
- 显示时间规划结果
- 提供交互式的配置界面
- 展示日程安排的可视化

作者：AI Assistant  
日期：2025-07-13
"""

import asyncio
import sys
from datetime import datetime, date, timedelta
from typing import Optional
import json
import os
from loguru import logger

# 配置日志
logger.remove()
logger.add(
    "logs/time_planner.log",
    rotation="1 day",
    format="{time} | {level} | {message}",
    level="INFO",
)
logger.add(sys.stderr, level="WARNING")

from .agent import get_agent, initialize_agent, shutdown_agent
from .models import UserPreferences


class TimeManagementCLI:
    """时间管理系统命令行界面"""

    def __init__(self):
        """初始化命令行界面"""
        self.agent = get_agent()
        self.user_preferences: Optional[UserPreferences] = None
        self.is_running = False

        print("=" * 60)
        print("  🕒 AI 时间管理系统")
        print("  让智能助手帮您合理安排时间")
        print("=" * 60)

    async def start(self):
        """启动命令行界面"""
        print("\\n正在初始化系统...")

        # 初始化 Agent
        success = initialize_agent()
        if success:
            print("✅ 系统初始化完成")
            if hasattr(self.agent, "thinking_client") and self.agent.thinking_client:
                print("🧠 思维链功能已启用")
            else:
                print("ℹ️  基础模式运行（思维链功能未启用）")

            # 检查记忆功能
            if hasattr(self.agent, "memory") and self.agent.memory:
                stats = self.agent.get_memory_stats()
                print(f"💾 记忆功能已启用 (已有 {stats['total_messages']} 条历史记录)")
            else:
                print("⚠️  记忆功能未启用")
        else:
            print("❌ 系统初始化失败，请检查配置")
            return

        print()

        # 首次使用设置
        await self._first_time_setup()

        # 主循环
        self.is_running = True
        print("\\n🤖 您好！我是您的时间管理助手。")
        print("您可以用自然语言告诉我您的任务和需求，我会帮您制定合理的时间安排。")
        print("输入 'help' 查看帮助，输入 'quit' 退出系统。\\n")

        while self.is_running:
            try:
                await self._handle_user_input()
            except KeyboardInterrupt:
                print("\\n\\n👋 再见！")
                break
            except Exception as e:
                logger.error(f"处理用户输入时出错: {e}")
                print(f"❌ 出现错误: {e}")

        # 清理资源
        shutdown_agent()

    async def _first_time_setup(self):
        """首次使用设置"""
        if os.path.exists("user_preferences.json"):
            # 加载已有的用户偏好
            try:
                with open("user_preferences.json", "r", encoding="utf-8") as f:
                    prefs_data = json.load(f)
                    self.user_preferences = UserPreferences(**prefs_data)
                print("✅ 已加载您的个人偏好设置")
                return
            except Exception as e:
                logger.warning(f"加载用户偏好失败: {e}")

        print("\\n🔧 首次使用，让我们设置一些基本偏好：")

        # 收集基本偏好
        preferences_data = {}

        # 作息时间
        wake_time = input("请输入您的起床时间（如 07:00）：").strip()
        if wake_time:
            try:
                hour, minute = map(int, wake_time.split(":"))
                preferences_data["wake_up_time"] = f"{hour:02d}:{minute:02d}"
            except:
                pass

        sleep_time = input("请输入您的睡觉时间（如 23:00）：").strip()
        if sleep_time:
            try:
                hour, minute = map(int, sleep_time.split(":"))
                preferences_data["sleep_time"] = f"{hour:02d}:{minute:02d}"
            except:
                pass

        # 工作偏好
        work_days = input(
            "您偏好在哪些天工作？（输入数字，如：1,2,3,4,5 代表周一到周五）："
        ).strip()
        if work_days:
            try:
                days = [int(d.strip()) - 1 for d in work_days.split(",")]  # 转换为0-6
                preferences_data["preferred_work_days"] = days
            except:
                pass

        # 创建用户偏好对象
        self.user_preferences = UserPreferences(**preferences_data)

        # 保存到文件
        try:
            with open("user_preferences.json", "w", encoding="utf-8") as f:
                json.dump(
                    self.user_preferences.dict(),
                    f,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
            print("✅ 偏好设置已保存")
        except Exception as e:
            logger.error(f"保存用户偏好失败: {e}")

    async def _handle_user_input(self):
        """处理用户输入"""
        try:
            user_input = input("🙋 请告诉我您的需求：").strip()

            if not user_input:
                return

            # 处理特殊命令
            if user_input.lower() in ["quit", "exit", "退出"]:
                self.is_running = False
                return

            if user_input.lower() in ["help", "帮助"]:
                self._show_help()
                return

            if user_input.lower() in ["prefs", "偏好", "设置"]:
                await self._manage_preferences()
                return

            if user_input.lower() in ["schedule", "日程", "查看日程"]:
                await self._show_schedule()
                return

            # 处理时间管理请求
            print("\\n🤔 正在思考和分析...")

            response = await self.agent.process_user_request(
                user_input=user_input, user_preferences=self.user_preferences
            )

            print(f"\\n🤖 AI助手：{response}")

        except Exception as e:
            logger.error(f"处理用户输入失败: {e}")
            print(f"❌ 处理请求时出现错误：{e}")

    def _show_help(self):
        """显示帮助信息"""
        print(
            """
📖 帮助信息：

基本使用：
- 直接用自然语言描述您的任务，如："明天上午学习数学2小时"
- 询问日程安排，如："查看我明天的安排"
- 请求规划建议，如："帮我安排这周的学习计划"

特殊命令：
- help / 帮助    : 显示此帮助信息
- schedule / 日程 : 查看当前日程安排
- prefs / 设置   : 管理个人偏好设置
- quit / 退出    : 退出系统

示例：
1. "我需要在明天下午准备期末考试，大概需要3小时"
2. "这周我有一个项目要完成，需要安排10小时的工作时间"
3. "帮我看看今天还有多少空闲时间"
4. "我想每天安排30分钟运动，该如何规划？"
        """
        )

    async def _manage_preferences(self):
        """管理用户偏好"""
        print("\\n⚙️ 当前偏好设置：")

        if self.user_preferences:
            print(f"起床时间：{self.user_preferences.wake_up_time}")
            print(f"睡觉时间：{self.user_preferences.sleep_time}")
            print(f"用餐时长：{self.user_preferences.meal_duration}分钟")
            print(f"偏好工作日：{self.user_preferences.preferred_work_days}")
            print(f"最大连续工作时间：{self.user_preferences.max_continuous_work}分钟")

        choice = input("\\n是否要修改设置？(y/n)：").strip().lower()
        if choice in ["y", "yes", "是"]:
            await self._first_time_setup()

    async def _show_schedule(self):
        """显示日程安排"""
        print("\\n📅 查看日程安排")

        # 获取查看范围
        choice = input("查看哪天的日程？(1)今天 (2)明天 (3)这周 (4)自定义：").strip()

        start_date = datetime.now().date()
        end_date = start_date

        if choice == "1":
            # 今天
            pass
        elif choice == "2":
            # 明天
            start_date = start_date + timedelta(days=1)
            end_date = start_date
        elif choice == "3":
            # 这周
            days_since_monday = start_date.weekday()
            start_date = start_date - timedelta(days=days_since_monday)
            end_date = start_date + timedelta(days=6)
        elif choice == "4":
            # 自定义
            date_str = input("请输入日期 (YYYY-MM-DD)：").strip()
            try:
                start_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                end_date = start_date
            except ValueError:
                print("❌ 日期格式错误")
                return
        else:
            print("❌ 无效选择")
            return

        # 查询并显示日程
        try:
            # 使用 Agent 工具查询
            from .agent import get_agent

            agent = get_agent()

            # 直接调用服务查询
            slots = agent.slot_service.find_slots_by_date_range(start_date, end_date)

            if not slots:
                print(f"\\n📭 {start_date} 到 {end_date} 期间暂无安排")
                return

            print(f"\\n📋 {start_date} 到 {end_date} 的日程：")
            print("-" * 60)

            current_date = None
            for slot in slots:
                slot_date = slot.start_time.date()

                # 显示日期分隔符
                if current_date != slot_date:
                    if current_date is not None:
                        print()
                    print(f"📅 {slot_date.strftime('%Y年%m月%d日 %A')}：")
                    current_date = slot_date

                # 显示时间段信息
                start_time = slot.start_time.strftime("%H:%M")
                end_time = slot.end_time.strftime("%H:%M")
                duration = slot.duration_minutes

                # 任务类型和优先级标识
                type_icon = "🔒" if slot.task_type.value == "fixed" else "🔄"
                priority_icon = self._get_priority_icon(slot.priority.value)

                print(
                    f"  {type_icon} {priority_icon} {start_time}-{end_time} {slot.title} ({duration}分钟)"
                )

                if slot.description:
                    print(f"      💭 {slot.description}")

            print("-" * 60)

        except Exception as e:
            logger.error(f"查询日程失败: {e}")
            print(f"❌ 查询日程时出现错误：{e}")

    def _get_priority_icon(self, priority: str) -> str:
        """获取优先级图标"""
        icons = {"low": "🟢", "medium": "🟡", "high": "🟠", "urgent": "🔴"}
        return icons.get(priority, "⚪")

    async def run(self):
        """运行命令行界面"""
        try:
            await self.start()
        except Exception as e:
            logger.error(f"CLI运行出错: {e}")
            print(f"❌ 系统运行出错：{e}")
        finally:
            shutdown_agent()


async def main():
    """主函数"""
    cli = TimeManagementCLI()
    await cli.run()


if __name__ == "__main__":
    # 创建日志目录
    os.makedirs("logs", exist_ok=True)

    # 运行 CLI
    asyncio.run(main())
