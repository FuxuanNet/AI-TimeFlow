#!/usr/bin/env python3
"""
测试AI生成时间表保存功能
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


async def test_ai_schedule_saving():
    """测试AI生成时间表的保存功能"""

    print("🧪 测试AI生成时间表保存功能")
    print("=" * 60)

    # 初始化服务和Agent
    service = TimeManagementService("test_ai_schedule.json")
    agent = NewTimeManagementAgent()  # Agent 会自己初始化服务

    # 模拟一个简单的JSON响应（避免调用API）
    mock_json_response = {
        "daily_schedule": [
            {
                "task_name": "测试任务1",
                "belong_to_day": "2025-07-16",
                "start_time": "09:00",
                "end_time": "10:00",
                "description": "这是一个测试任务",
                "can_reschedule": True,
                "can_compress": True,
                "can_parallel": False,
                "parent_task": "测试项目",
            },
            {
                "task_name": "测试任务2",
                "belong_to_day": "2025-07-16",
                "start_time": "14:00",
                "end_time": "16:00",
                "description": "另一个测试任务",
                "can_reschedule": False,
                "can_compress": True,
                "can_parallel": False,
                "parent_task": "测试项目",
            },
        ],
        "weekly_schedule": [
            {
                "task_name": "学习新技能",
                "belong_to_week": 1,
                "description": "每周学习新的编程技能",
                "parent_project": "技能提升",
                "priority": "high",
            }
        ],
    }

    print("📝 模拟用户请求...")
    user_request = "我明天需要安排一些工作任务，请帮我规划时间表"

    print("💾 测试保存AI生成的时间表...")
    try:
        await agent._save_ai_generated_schedule(mock_json_response, user_request)
        print("✅ AI时间表保存成功")
    except Exception as e:
        print(f"❌ 保存失败: {e}")

    print("\\n🔄 测试执行时间管理操作...")
    try:
        result = await agent._execute_time_management_actions(mock_json_response)
        print(f"✅ 操作执行成功:")
        print(f"   {result}")
    except Exception as e:
        print(f"❌ 执行失败: {e}")

    print("\\n📊 获取AI生成的时间表历史...")
    try:
        history = agent.get_ai_generated_schedules()
        print(f"✅ 历史记录获取成功:")
        print(f"   时间表数量: {history['count']}")
        print(f"   最近记录: {len(history['schedules'])}")
        if history["latest"]:
            print(f"   最新请求: {history['latest']['metadata']['user_request']}")
    except Exception as e:
        print(f"❌ 获取历史失败: {e}")

    print("\\n🎯 测试前端数据导出...")
    try:
        export_data = agent.export_schedule_for_frontend()
        print(f"✅ 前端数据导出成功")
        print(f"   系统统计: {export_data['system_info']['statistics']}")
        print(f"   AI历史记录: {export_data['ai_generated_history']['count']} 条")
    except Exception as e:
        print(f"❌ 导出失败: {e}")

    print("\\n📈 查看Agent的时间服务统计...")
    try:
        stats = agent.time_service.get_statistics()
        print(f"✅ 统计信息:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"❌ 获取统计失败: {e}")

    print("\\n📁 检查生成的文件...")

    # 检查ai_generated_schedules目录
    if os.path.exists("ai_generated_schedules"):
        files = os.listdir("ai_generated_schedules")
        print(f"✅ AI时间表目录存在，包含 {len(files)} 个文件:")
        for file in files:
            print(f"   - {file}")
    else:
        print("❌ AI时间表目录不存在")

    # 检查导出文件
    export_files = [f for f in os.listdir(".") if f.startswith("frontend_export_")]
    if export_files:
        print(f"✅ 前端导出文件存在 ({len(export_files)} 个):")
        for file in export_files[-3:]:  # 显示最近3个
            print(f"   - {file}")
    else:
        print("❌ 前端导出文件不存在")

    print("\\n🏁 测试完成！")

    # 关闭agent
    try:
        await agent.shutdown()
    except:
        pass


if __name__ == "__main__":
    asyncio.run(test_ai_schedule_saving())
