#!/usr/bin/env python3
"""
测试DeepSeek多轮对话机制
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


async def test_deepseek_conversation():
    """测试DeepSeek多轮对话记忆功能"""
    
    print("🚀 启动DeepSeek多轮对话测试")
    print("=" * 50)
    
    # 初始化Agent
    agent = TimeManagementAgent()
    agent.initialize()
    
    # 重置对话历史，确保干净的开始
    agent.reset_conversation()
    
    test_cases = [
        "你好，我叫李华，是一名软件工程师，今年28岁。",
        "你记住我的名字了吗？",
        "我的职业是什么？",
        "我多大了？",
        "能帮我总结一下你知道的关于我的信息吗？"
    ]
    
    for i, user_input in enumerate(test_cases, 1):
        print(f"\n🔹 测试轮次 {i}")
        print(f"👤 用户: {user_input}")
        
        try:
            # 获取对话状态
            status = agent.get_conversation_status()
            print(f"📊 对话状态: {status}")
            
            # 处理用户请求
            response = await agent.process_user_request(user_input)
            print(f"🤖 AI回复: {response}")
            
            # 检查回复质量
            if i == 2 and "李华" not in response.lower():
                print("❌ 姓名记忆测试失败")
            elif i == 3 and ("工程师" not in response.lower() and "软件" not in response.lower()):
                print("❌ 职业记忆测试失败")
            elif i == 4 and "28" not in response:
                print("❌ 年龄记忆测试失败")
            elif i >= 2:
                print("✅ 记忆测试通过")
                
        except Exception as e:
            print(f"❌ 错误: {e}")
        
        print("-" * 50)
    
    # 显示最终对话状态
    final_status = agent.get_conversation_status()
    print(f"\n📈 最终对话状态: {final_status}")
    
    # 关闭Agent
    agent.shutdown()
    print("\n🏁 测试完成")


if __name__ == "__main__":
    # 设置简单日志
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<level>{level}</level> | {message}")
    
    try:
        asyncio.run(test_deepseek_conversation())
    except KeyboardInterrupt:
        print("\n🛑 测试被用户中断")
    except Exception as e:
        print(f"\n💥 测试失败: {e}")
        import traceback
        traceback.print_exc()
