#!/usr/bin/env python3
"""
测试时间安排功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from time_planner.agent import TimeManagementAgent
from loguru import logger


async def test_time_planning():
    """测试时间安排功能"""
    
    print("🚀 启动时间安排测试")
    print("=" * 50)
    
    # 初始化Agent
    agent = TimeManagementAgent()
    agent.initialize()
    
    # 重置对话历史
    agent.reset_conversation()
    
    test_request = "我今天大概五点左右去吃饭，大概半个小时多吃完，然后休息一下。之后去洗个澡，大概需要花一个小时。晚上的时候我希望玩会儿游戏，不过我必须要花一个小时以上来敲代码，我希望干完之后再玩游戏，然后睡觉，帮我安排下时间"
    
    print(f"👤 用户请求: {test_request}")
    print("🤔 处理中...")
    
    try:
        # 处理用户请求
        response = await agent.process_user_request(test_request)
        print(f"🤖 AI回复: {response}")
        
        if "抱歉" in response and "错误" in response:
            print("❌ 测试失败：出现错误")
        else:
            print("✅ 测试成功：获得正常回复")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 显示对话状态
    status = agent.get_conversation_status()
    print(f"\n📈 对话状态: {status}")
    
    # 关闭Agent
    agent.shutdown()
    print("\n🏁 测试完成")


if __name__ == "__main__":
    # 设置简单日志
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<level>{level}</level> | {message}")
    
    try:
        asyncio.run(test_time_planning())
    except KeyboardInterrupt:
        print("\n🛑 测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试失败: {e}")
        import traceback
        traceback.print_exc()
