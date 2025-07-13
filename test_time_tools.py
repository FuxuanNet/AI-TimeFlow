#!/usr/bin/env python3
"""
测试时间查询工具
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from time_planner.new_services import TimeManagementService
from time_planner.new_models import TimeUtils
import json


def test_time_tools():
    """测试所有时间工具"""

    print("🕐 时间管理系统 - 时间查询工具测试")
    print("=" * 60)

    # 初始化服务
    service = TimeManagementService("test_time_tools.json")

    print("\n📅 基础时间信息：")
    current_time = service.get_current_time_info()
    for key, value in current_time.items():
        print(f"  {key}: {value}")

    print("\n🔍 详细时间信息：")
    detailed_time = service.get_detailed_time_info()
    for key, value in detailed_time.items():
        print(f"  {key}: {value}")

    print("\n⏰ 距离下一个时间段：")
    next_period = service.get_time_until_next_period()
    for key, value in next_period.items():
        print(f"  {key}: {value}")

    print("\n📊 本周进度：")
    week_progress = service.get_week_progress()
    for key, value in week_progress.items():
        print(f"  {key}: {value}")

    print("\n🗓️ 相对日期解析测试：")
    test_dates = ["今天", "明天", "昨天", "后天", "前天"]
    for date_term in test_dates:
        parsed = service.parse_relative_date(date_term)
        date_info = service.get_date_info(parsed)
        print(f"  {date_term} -> {parsed} ({date_info.get('weekday_chinese', '未知')})")

    print("\n📍 指定日期信息：")
    test_specific_dates = ["2025-07-14", "2025-07-20", "2025-12-31"]
    for date_str in test_specific_dates:
        date_info = service.get_date_info(date_str)
        if "error" not in date_info:
            print(
                f"  {date_str}: {date_info['weekday_chinese']}, 年第{date_info['day_of_year']}天, 周末: {'是' if date_info['is_weekend'] else '否'}"
            )
        else:
            print(f"  {date_str}: {date_info['error']}")

    print("\n💾 时间工具数据导出：")
    time_data = {
        "current_time": current_time,
        "detailed_time": detailed_time,
        "next_period": next_period,
        "week_progress": week_progress,
        "relative_dates": {
            date: service.parse_relative_date(date) for date in test_dates
        },
    }

    with open("time_tools_export.json", "w", encoding="utf-8") as f:
        json.dump(time_data, f, ensure_ascii=False, indent=2)
    print("  ✅ 时间数据已导出到：time_tools_export.json")

    print("\n🎯 实用场景测试：")
    print("  场景1：用户询问当前时间")
    print(
        f"    回答：现在是 {detailed_time['formatted_time']} ({detailed_time['weekday_chinese']} {detailed_time['time_period']})"
    )

    print("  场景2：用户询问今天是否周末")
    print(
        f"    回答：今天是{current_time['weekday_chinese']}，{'是' if current_time['is_weekend'] else '不是'}周末"
    )

    print("  场景3：用户询问本周过了多少")
    print(
        f"    回答：本周已过去 {week_progress['days_passed']}/{7} 天，进度 {week_progress['progress_percentage']}%"
    )

    print("  场景4：用户询问距离下个时间段还有多久")
    print(f"    回答：{next_period['message']}")

    print("\n🏁 时间工具测试完成！")


if __name__ == "__main__":
    test_time_tools()
