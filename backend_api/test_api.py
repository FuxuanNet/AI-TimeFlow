"""
API 测试脚本

用于测试修复后的 FastAPI 端点
"""

import requests
import json

# API 基础URL
BASE_URL = "http://localhost:8000"


def test_health():
    """测试健康检查端点"""
    print("🔍 测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False


def test_chat_message():
    """测试聊天消息端点"""
    print("\n💬 测试聊天消息...")
    try:
        payload = {"message": "你好，请告诉我现在的时间", "session_id": "test_session"}

        response = requests.post(
            f"{BASE_URL}/api/chat/message",
            headers={"Content-Type": "application/json"},
            json=payload,
        )

        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功!")
            print(f"AI 响应: {result.get('response', '无响应')}")
            print(f"使用的工具: {result.get('tools_used', [])}")
            return True
        else:
            print(f"❌ 失败: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 聊天测试失败: {e}")
        return False


def test_time_info():
    """测试时间信息端点"""
    print("\n⏰ 测试时间信息...")
    try:
        response = requests.get(f"{BASE_URL}/api/data/time-info")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功!")
            print(
                f"时间信息: {json.dumps(result.get('time_info', {}), indent=2, ensure_ascii=False)}"
            )
            return True
        else:
            print(f"❌ 失败: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 时间信息测试失败: {e}")
        return False


def test_task_creation():
    """测试任务创建端点"""
    print("\n📝 测试任务创建...")
    try:
        payload = {
            "task_name": "API测试任务",
            "description": "测试API创建的任务",
            "date_str": "2025-07-16",
            "start_time": "14:00",
            "end_time": "15:00",
            "can_reschedule": True,
            "can_compress": True,
            "can_parallel": False,
            "parent_task": None,
        }

        response = requests.post(
            f"{BASE_URL}/api/tasks/daily",
            headers={"Content-Type": "application/json"},
            json=payload,
        )

        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 成功!")
            print(f"创建结果: {result.get('message', '无消息')}")
            return True
        else:
            print(f"❌ 失败: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 任务创建测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("🚀 开始 API 测试...")

    tests = [
        ("健康检查", test_health),
        ("聊天消息", test_chat_message),
        ("时间信息", test_time_info),
        ("任务创建", test_task_creation),
    ]

    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))

    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")

    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\n总计: {passed}/{total} 个测试通过")


if __name__ == "__main__":
    main()
