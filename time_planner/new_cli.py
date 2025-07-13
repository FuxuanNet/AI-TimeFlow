"""
时间管理系统 - 新的命令行界面

使用新的数据结构和Agent

作者：AI Assistant
日期：2025-07-13
"""

import asyncio
import signal
import sys
from typing import Optional
from loguru import logger

from .new_agent import NewTimeManagementAgent


class NewCLI:
    """新的命令行界面"""

    def __init__(self):
        """初始化CLI"""
        self.agent = NewTimeManagementAgent()
        self.is_running = False
        logger.info("新命令行界面初始化完成")

    async def start(self):
        """启动CLI"""
        try:
            # 初始化Agent
            if not self.agent.initialize():
                logger.error("Agent初始化失败")
                return

            self.is_running = True

            # 设置信号处理
            signal.signal(signal.SIGINT, self._signal_handler)

            # 显示欢迎信息
            self._show_welcome()

            # 主循环
            await self._main_loop()

        except Exception as e:
            logger.error(f"CLI启动失败：{e}")
        finally:
            await self._cleanup()

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        print("\\n\\n👋 正在退出系统...")
        self.is_running = False

    def _show_welcome(self):
        """显示欢迎信息"""
        print(
            """
╔══════════════════════════════════════════════════════════════╗
║                    🕒 AI 时间管理系统 v2.0                     ║
║                                                              ║
║              让智能助手帮您合理安排时间                         ║
║                                                              ║
║  功能特色:                                                    ║
║  • 智能区分日任务和周任务                                       ║
║  • 自然语言时间解析                                           ║
║  • DeepSeek 多轮对话记忆                                      ║
║  • JSON 结构化数据存储                                        ║
║  • 思维链推理                                                 ║
║  • 任务并行和冲突检测                                         ║
╚══════════════════════════════════════════════════════════════╝

📋 使用说明：
• 直接用自然语言描述您的时间安排需求
• 系统会自动判断是日任务还是周任务
• 输入 'help' 查看详细帮助
• 输入 'status' 查看系统状态
• 输入 'export' 导出数据
• 输入 'quit' 或 Ctrl+C 退出系统

您可以用自然语言告诉我您的任务和需求，我会帮您制定合理的时间安排。
输入 'help' 查看帮助，输入 'quit' 退出系统。
"""
        )

    async def _main_loop(self):
        """主循环"""
        while self.is_running:
            try:
                # 获取用户输入
                user_input = await self._get_user_input()

                if not user_input or not user_input.strip():
                    continue

                user_input = user_input.strip()

                # 处理特殊命令
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("👋 感谢使用AI时间管理系统，再见！")
                    break
                elif user_input.lower() == "help":
                    self._show_help()
                    continue
                elif user_input.lower() == "status":
                    await self._show_status()
                    continue
                elif user_input.lower() == "export":
                    await self._export_data()
                    continue
                elif user_input.lower() == "clear":
                    self._clear_screen()
                    continue
                elif user_input.lower() == "reset":
                    await self._reset_conversation()
                    continue

                # 处理正常的时间管理请求
                print("\\n🤔 正在思考和分析...")

                try:
                    response = await self.agent.process_user_request(user_input)
                    print(f"\\n🤖 AI助手：{response}")

                except Exception as e:
                    print(f"\\n❌ 处理请求时出现错误：{str(e)}")
                    logger.error(f"处理用户请求失败：{e}")

            except KeyboardInterrupt:
                print("\\n\\n👋 正在退出系统...")
                break
            except Exception as e:
                print(f"\\n❌ 系统错误：{str(e)}")
                logger.error(f"主循环错误：{e}")

    async def _get_user_input(self) -> str:
        """获取用户输入"""
        try:
            # 使用异步方式获取输入（简化版本）
            return input("\\n🙋 请告诉我您的需求：")
        except EOFError:
            return "quit"
        except KeyboardInterrupt:
            return "quit"

    def _show_help(self):
        """显示帮助信息"""
        print(
            """
📚 AI时间管理系统帮助

🔹 基本使用：
  直接用自然语言描述您的需求，例如：
  • "我明天下午2点有个会议，大概1小时"
  • "这周我要学习Python，每天安排2小时"
  • "今天晚上7点吃饭，8点看电影"

🔹 时间表达：
  • 支持相对时间：今天、明天、昨天、后天、前天
  • 支持具体日期：2025-01-15、1月15日
  • 支持时间范围：下午2点到4点、19:00-21:00

🔹 任务类型：
  • 日任务：具体时间的短期任务（会议、约会、吃饭等）
  • 周任务：长期学习和项目（学习技能、复杂项目等）

🔹 特殊命令：
  • help     - 显示此帮助信息
  • status   - 查看系统状态和统计
  • export   - 导出时间管理数据
  • clear    - 清屏
  • reset    - 重置对话历史
  • quit     - 退出系统

🔹 智能功能：
  • 自动判断任务类型和优先级
  • 任务冲突检测和建议
  • 支持任务拆解和并行安排
  • 记住您的偏好和历史对话
"""
        )

    async def _show_status(self):
        """显示系统状态"""
        try:
            # 获取对话状态
            conv_status = self.agent.get_conversation_status()

            # 获取当前时间信息
            time_info = self.agent.get_current_time_info()

            # 获取今天的日程摘要
            today_summary = self.agent.get_schedule_summary()

            print(
                f"""
📊 系统状态报告

🕒 当前时间信息：
  • 当前时间：{time_info['current_datetime']}
  • 今天是：{time_info['weekday_chinese']}
  • 是否周末：{'是' if time_info['is_weekend'] else '否'}

💬 对话状态：
  • 对话轮次：{conv_status['conversation_rounds']}
  • 消息总数：{conv_status['total_messages']}
  • 记忆消息：{conv_status['memory_messages']}

📈 时间管理数据：
  • 开始使用日期：{conv_status['time_service_stats']['start_date']}
  • 日程计划数：{conv_status['time_service_stats']['total_daily_schedules']}
  • 周计划数：{conv_status['time_service_stats']['total_weekly_schedules']}
  • 日任务总数：{conv_status['time_service_stats']['total_daily_tasks']}
  • 周任务总数：{conv_status['time_service_stats']['total_weekly_tasks']}

📅 今日日程：
{today_summary}
"""
            )

        except Exception as e:
            print(f"❌ 获取状态信息失败：{str(e)}")
            logger.error(f"获取状态信息失败：{e}")

    async def _export_data(self):
        """导出数据"""
        try:
            output_file = self.agent.time_service.export_json()
            if output_file:
                print(f"✅ 数据已成功导出到：{output_file}")
            else:
                print("❌ 数据导出失败")
        except Exception as e:
            print(f"❌ 导出数据时出现错误：{str(e)}")
            logger.error(f"导出数据失败：{e}")

    def _clear_screen(self):
        """清屏"""
        import os

        os.system("cls" if os.name == "nt" else "clear")
        self._show_welcome()

    async def _reset_conversation(self):
        """重置对话历史"""
        try:
            self.agent.reset_conversation()
            print("✅ 对话历史已重置")
        except Exception as e:
            print(f"❌ 重置对话历史失败：{str(e)}")
            logger.error(f"重置对话历史失败：{e}")

    async def _cleanup(self):
        """清理资源"""
        try:
            self.agent.shutdown()
            logger.info("系统已关闭")
        except Exception as e:
            logger.error(f"清理资源失败：{e}")


async def main():
    """主函数"""
    cli = NewCLI()
    await cli.start()


if __name__ == "__main__":
    asyncio.run(main())
