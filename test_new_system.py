#!/usr/bin/env python3
"""
测试新时间管理系统
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from time_planner.new_agent import NewTimeManagementAgent
from time_planner.new_services import TimeManagementService
from loguru import logger


async def test_new_system():
    """测试新时间管理系统"""

    print("🚀 启动新时间管理系统测试")
    print("=" * 60)

    # 清理旧数据文件
    for file in ["time_management_data.json", "conversation_memory.json"]:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️ 已清理旧文件：{file}")

    # 测试服务层
    print("\\n📋 测试时间管理服务...")
    service = TimeManagementService("test_time_data.json")

    # 测试当前时间
    current_time = service.get_current_time_info()
    print(
        f"⏰ 当前时间：{current_time['current_datetime']} ({current_time['weekday_chinese']})"
    )

    # 测试相对日期解析
    print("\\n🔍 测试相对日期解析...")
    test_dates = ["今天", "明天", "昨天", "后天"]
    for date_term in test_dates:
        parsed = service.parse_relative_date(date_term)
        date_info = service.get_date_info(parsed)
        print(f"  {date_term} = {parsed} ({date_info.get('weekday_chinese', '未知')})")

    # 测试添加日任务
    print("\\n📅 测试添加日任务...")
    success = service.add_daily_task(
        task_name="测试会议",
        date_str="今天",
        start_time="14:00",
        end_time="15:30",
        description="这是一个测试会议",
        can_parallel=False,
    )
    print(f"  日任务添加结果：{'✅ 成功' if success else '❌ 失败'}")

    # 测试添加周任务
    print("\\n📊 测试添加周任务...")
    success = service.add_weekly_task(
        task_name="学习Python",
        week_number=1,
        description="学习Python基础语法",
        priority="high",
    )
    print(f"  周任务添加结果：{'✅ 成功' if success else '❌ 失败'}")

    # 查看统计信息
    stats = service.get_statistics()
    print(f"\\n📈 统计信息：")
    print(f"  日任务总数：{stats['total_daily_tasks']}")
    print(f"  周任务总数：{stats['total_weekly_tasks']}")

    # 测试Agent
    print("\\n🤖 测试AI Agent...")
    agent = NewTimeManagementAgent()
    agent.initialize()

    # 测试简单对话
    test_requests = [
        "你好，我叫测试用户",
        "你记住我的名字了吗？",
        "我明天下午3点有个会议，大概1小时",
        "我这周要学习新技术，安排下时间",
    ]

    for i, request in enumerate(test_requests, 1):
        print(f"\\n🔹 测试 {i}: {request}")
        try:
            response = await agent.process_user_request(request)
            print(
                f"🤖 回复: {response[:200]}..."
                if len(response) > 200
                else f"🤖 回复: {response}"
            )
        except Exception as e:
            print(f"❌ 错误: {e}")

    # 显示最终状态
    final_status = agent.get_conversation_status()
    print(f"\\n📊 最终状态:")
    print(f"  对话轮次：{final_status['conversation_rounds']}")
    print(f"  总消息数：{final_status['total_messages']}")
    print(f"  时间数据：{final_status['time_service_stats']}")

    # 关闭Agent
    agent.shutdown()

    # 导出测试数据
    export_file = service.export_json("test_export.json")
    if export_file:
        print(f"\\n💾 测试数据已导出：{export_file}")

    print("\\n🏁 测试完成！")


if __name__ == "__main__":
    # 设置简单日志
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<level>{level}</level> | {message}")

    try:
        asyncio.run(test_new_system())
    except KeyboardInterrupt:
        print("\\n🛑 测试被用户中断")
    except Exception as e:
        print(f"\\n💥 测试失败: {e}")
        import traceback

        traceback.print_exc()
