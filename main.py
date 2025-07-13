#!/usr/bin/env python3
"""
AI 时间管理系统 - 主程序入口

这是时间管理系统的主启动文件，用户可以通过以下方式启动：

1. 命令行模式：
   python main.py

2. 交互模式：
   python main.py --interactive

3. 帮助信息：
   python main.py --help

作者：AI Assistant
日期：2025-07-13
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from time_planner.cli import main as cli_main
from loguru import logger


def setup_logging(debug: bool = False):
    """设置日志配置"""
    # 创建日志目录
    os.makedirs("logs", exist_ok=True)

    # 清除默认日志处理器
    logger.remove()

    # 设置文件日志
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        level="DEBUG" if debug else "INFO",
    )

    # 设置控制台日志（只显示警告和错误）
    if debug:
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}",
            level="DEBUG",
        )
    else:
        logger.add(
            sys.stderr, format="<level>{level}</level> | {message}", level="WARNING"
        )


def print_banner():
    """打印系统横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                      🕒 AI 时间管理系统                        ║
    ║                                                              ║
    ║              让智能助手帮您合理安排时间                         ║
    ║                                                              ║
    ║  功能特色:                                                    ║
    ║  • 自然语言任务解析                                           ║
    ║  • 智能时间规划                                               ║
    ║  • 冲突检测与自动调整                                         ║
    ║  • 个性化建议                                                 ║
    ║  • 思维链推理                                                 ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_dependencies():
    """检查依赖环境"""
    missing_deps = []

    try:
        import pydantic
    except ImportError:
        missing_deps.append("pydantic")

    try:
        import dotenv
    except ImportError:
        missing_deps.append("python-dotenv")

    try:
        import loguru
    except ImportError:
        missing_deps.append("loguru")

    # 检查环境变量
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  警告: 未找到 .env 文件，请确保已配置 API 密钥")

    if missing_deps:
        print(f"❌ 缺少依赖包: {', '.join(missing_deps)}")
        print("请运行: pip install -r requirements.txt")
        return False

    return True


def check_mcp_server():
    """检查 MCP 服务器是否可用"""
    import subprocess

    try:
        # 尝试运行 MCP 服务器检查命令
        result = subprocess.run(
            ["npm", "list", "-g", "@modelcontextprotocol/server-sequential-thinking"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print("✅ MCP Sequential Thinking 服务器已安装")
            return True
        else:
            print("⚠️  MCP Sequential Thinking 服务器未安装")
            print(
                "请运行: npm install -g @modelcontextprotocol/server-sequential-thinking"
            )
            return False

    except subprocess.TimeoutExpired:
        print("⚠️  检查 MCP 服务器超时")
        return False
    except FileNotFoundError:
        print("⚠️  未找到 npm，请确保 Node.js 已安装")
        return False
    except Exception as e:
        print(f"⚠️  检查 MCP 服务器时出错: {e}")
        return False


async def run_interactive_mode():
    """运行交互模式"""
    print("🚀 启动交互模式...")
    await cli_main()


async def run_demo_mode():
    """运行演示模式"""
    print("🎯 演示模式")

    # 导入必要的模块
    try:
        from time_planner import get_agent, initialize_agent, shutdown_agent
        from time_planner.models import UserPreferences

        print("\\n正在初始化系统...")

        # 初始化 Agent
        if not initialize_agent():
            print("❌ 系统初始化失败")
            return

        print("✅ 系统初始化成功")

        # 创建默认用户偏好
        preferences = UserPreferences()

        # 获取 Agent 实例
        agent = get_agent()

        # 演示一些基本功能
        demo_requests = [
            "我明天上午需要学习数学2小时，请帮我安排",
            "查看我今天的日程安排",
            "我下周有个项目要完成，需要安排15小时的工作时间",
        ]

        print("\\n🎯 开始演示...")

        for i, request in enumerate(demo_requests, 1):
            print(f"\\n--- 演示 {i} ---")
            print(f"用户输入: {request}")
            print("AI处理中...")

            try:
                response = await agent.process_user_request(request, preferences)
                print(f"AI回复: {response}")
            except Exception as e:
                print(f"处理失败: {e}")

            # 等待一下
            await asyncio.sleep(1)

        print("\\n🎉 演示完成！")

    except Exception as e:
        logger.error(f"演示模式失败: {e}")
        print(f"❌ 演示失败: {e}")
    finally:
        shutdown_agent()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI 时间管理系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 启动交互模式
  python main.py --demo            # 运行演示模式  
  python main.py --check           # 检查系统环境
  python main.py --debug           # 开启调试模式
        """,
    )

    parser.add_argument("--demo", action="store_true", help="运行演示模式")

    parser.add_argument("--check", action="store_true", help="检查系统环境和依赖")

    parser.add_argument("--debug", action="store_true", help="开启调试模式")

    parser.add_argument("--no-banner", action="store_true", help="不显示启动横幅")

    args = parser.parse_args()

    # 设置日志
    setup_logging(debug=args.debug)

    # 显示横幅
    if not args.no_banner:
        print_banner()

    # 检查环境
    if args.check:
        print("🔍 检查系统环境...")
        deps_ok = check_dependencies()
        mcp_ok = check_mcp_server()

        if deps_ok and mcp_ok:
            print("\\n✅ 环境检查通过，系统可以正常运行")
        else:
            print("\\n❌ 环境检查失败，请根据上述提示解决问题")
        return

    # 快速环境检查
    if not check_dependencies():
        print("\\n❌ 依赖检查失败，程序退出")
        print("请运行: python main.py --check 查看详细信息")
        sys.exit(1)

    try:
        if args.demo:
            # 演示模式
            asyncio.run(run_demo_mode())
        else:
            # 默认交互模式
            asyncio.run(run_interactive_mode())

    except KeyboardInterrupt:
        print("\\n\\n👋 用户中断，程序退出")
    except Exception as e:
        logger.error(f"程序运行失败: {e}")
        print(f"\\n❌ 程序运行失败: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
