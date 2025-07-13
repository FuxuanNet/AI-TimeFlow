#!/usr/bin/env python3
"""
测试新时间管理系统 - 简化版（无AI功能）
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from time_planner.new_services import TimeManagementService
from time_planner.new_models import Priority
from loguru import logger


def test_basic_functionality():
    """测试基础功能"""

    print("🚀 启动基础功能测试")
    print("=" * 50)

    # 清理测试文件
    test_file = "test_basic_functionality.json"
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"🗑️ 已清理测试文件：{test_file}")

    # 初始化服务
    service = TimeManagementService(test_file)

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
    success1 = service.add_daily_task(
        task_name="测试会议",
        date_str="今天",
        start_time="14:00",
        end_time="15:30",
        description="这是一个测试会议",
        can_parallel=False,
    )
    print(f"  日任务1添加结果：{'✅ 成功' if success1 else '❌ 失败'}")

    success2 = service.add_daily_task(
        task_name="吃外卖-点餐",
        date_str="明天",
        start_time="12:00",
        end_time="12:05",
        description="点外卖，可以并行做其他事",
        can_parallel=True,
        parent_task="吃外卖",
    )
    print(f"  日任务2添加结果：{'✅ 成功' if success2 else '❌ 失败'}")

    # 测试添加周任务
    print("\\n📊 测试添加周任务...")

    # 测试不同优先级
    test_tasks = [
        ("学习Python基础", "学习Python项目", "high"),
        ("学习Python进阶", "学习Python项目", "medium"),
        ("完成Python作业", "学习Python项目", "critical"),
        ("阅读Python文档", "学习Python项目", "low"),
    ]

    for task_name, parent_project, priority in test_tasks:
        success = service.add_weekly_task(
            task_name=task_name,
            week_number=1,
            description=f"这是{task_name}任务",
            parent_project=parent_project,
            priority=priority,  # 传入字符串优先级
        )
        print(
            f"  周任务 '{task_name}' (优先级:{priority})：{'✅ 成功' if success else '❌ 失败'}"
        )

    # 测试查询功能
    print("\\n🔍 测试查询功能...")

    # 查询今天的日程
    today_schedule = service.get_daily_schedule("今天")
    if today_schedule:
        print(f"  今天有 {len(today_schedule.tasks)} 个任务")
        for task in today_schedule.tasks:
            print(f"    - {task.task_name} ({task.start_time}-{task.end_time})")
    else:
        print("  今天暂无安排")

    # 查询第1周的计划
    week1_schedule = service.get_weekly_schedule(1)
    if week1_schedule:
        print(f"\\n  第1周有 {len(week1_schedule.tasks)} 个任务")
        for task in week1_schedule.tasks:
            print(f"    - {task.task_name} (优先级:{task.priority.value})")
    else:
        print("\\n  第1周暂无计划")

    # 测试更新功能
    print("\\n✏️ 测试更新功能...")
    update_success = service.update_daily_task(
        date_str="今天",
        task_name="测试会议",
        updates={"description": "更新后的会议描述", "end_time": "16:00"},
    )
    print(f"  日任务更新结果：{'✅ 成功' if update_success else '❌ 失败'}")

    # 测试删除功能
    print("\\n🗑️ 测试删除功能...")
    delete_success = service.remove_weekly_task(1, "阅读Python文档")
    print(f"  周任务删除结果：{'✅ 成功' if delete_success else '❌ 失败'}")

    # 查看最终统计
    stats = service.get_statistics()
    print(f"\\n📈 最终统计信息：")
    print(f"  开始日期：{stats['start_date']}")
    print(f"  日程计划数：{stats['total_daily_schedules']}")
    print(f"  周计划数：{stats['total_weekly_schedules']}")
    print(f"  日任务总数：{stats['total_daily_tasks']}")
    print(f"  周任务总数：{stats['total_weekly_tasks']}")
    print(f"  数据文件大小：{stats['data_file_size']} 字节")

    # 导出数据
    export_file = service.export_json("test_basic_export.json")
    if export_file:
        print(f"\\n💾 测试数据已导出：{export_file}")

    print("\\n🏁 基础功能测试完成！")

    # 验证JSON格式
    print("\\n🔍 验证JSON数据格式...")
    try:
        import json

        with open(export_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        print("✅ JSON格式验证通过")
        print(f"  包含字段：{list(data.keys())}")

        if "daily_schedules" in data:
            print(f"  日程表数量：{len(data['daily_schedules'])}")
        if "weekly_schedules" in data:
            print(f"  周计划数量：{len(data['weekly_schedules'])}")

    except Exception as e:
        print(f"❌ JSON格式验证失败：{e}")


if __name__ == "__main__":
    # 设置简单日志
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<level>{level}</level> | {message}")

    try:
        test_basic_functionality()
    except KeyboardInterrupt:
        print("\\n🛑 测试被用户中断")
    except Exception as e:
        print(f"\\n💥 测试失败: {e}")
        import traceback

        traceback.print_exc()
