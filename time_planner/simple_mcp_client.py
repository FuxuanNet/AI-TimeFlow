"""
简化的 MCP 客户端

用于与思维链服务器通信

作者：AI Assistant
日期：2025-07-13
"""

import asyncio
import json
import subprocess
import sys
import time
from typing import Dict, Any, Optional, List
from loguru import logger


class SimpleMCPClient:
    """简化的 MCP 客户端"""

    def __init__(self, server_path: str = "sequentialthinking"):
        """初始化客户端"""
        self.server_path = server_path
        self.process: Optional[subprocess.Popen] = None
        self.is_connected = False
        self.tools: List[Dict[str, Any]] = []

    def start_and_initialize(self) -> bool:
        """启动并初始化 MCP 服务器"""
        try:
            logger.info("启动 MCP 服务器...")

            # 尝试启动服务器进程
            try:
                self.process = subprocess.Popen(
                    [sys.executable, "-m", self.server_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=0,
                )

                # 等待一下让服务器启动
                time.sleep(2)

                # 检查进程是否还在运行
                if self.process.poll() is None:
                    logger.info("MCP 服务器进程启动成功")
                else:
                    logger.warning("MCP 服务器进程启动失败")
                    return False

            except Exception as e:
                logger.warning(f"启动 MCP 服务器失败: {e}")
                return False

            logger.info("发送初始化请求...")

            # 发送初始化请求
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "time-management-client",
                        "version": "1.0.0",
                    },
                },
            }

            response = self._send_request(init_request)
            if response and "result" in response:
                logger.info("MCP 初始化成功")

                # 获取工具列表
                self._get_tools()

                self.is_connected = True
                return True
            else:
                logger.warning("MCP 初始化失败")
                return False

        except Exception as e:
            logger.error(f"MCP 客户端初始化失败: {e}")
            return False

    def _send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """发送请求到 MCP 服务器"""
        try:
            if not self.process or self.process.stdin is None:
                return None

            # 发送请求
            request_str = json.dumps(request) + "\n"
            self.process.stdin.write(request_str)
            self.process.stdin.flush()

            # 读取响应（简化版本，实际应该有超时处理）
            if self.process.stdout:
                response_str = self.process.stdout.readline()
                if response_str:
                    return json.loads(response_str.strip())

            return None

        except Exception as e:
            logger.error(f"发送 MCP 请求失败: {e}")
            return None

    def _get_tools(self):
        """获取可用工具列表"""
        try:
            logger.info("获取工具列表...")

            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {},
            }

            response = self._send_request(tools_request)
            if response and "result" in response:
                self.tools = response["result"].get("tools", [])
                logger.info(f"获取到 {len(self.tools)} 个工具")
                for tool in self.tools:
                    logger.debug(f"可用工具: {tool.get('name', 'unknown')}")
            else:
                logger.warning("获取工具列表失败")

        except Exception as e:
            logger.error(f"获取工具列表失败: {e}")

    def call_tool(
        self, name: str, arguments: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """调用工具"""
        try:
            if not self.is_connected:
                logger.warning("MCP 客户端未连接")
                return None

            call_request = {
                "jsonrpc": "2.0",
                "id": int(time.time()),
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }

            response = self._send_request(call_request)
            if response and "result" in response:
                return response["result"]
            else:
                logger.warning(f"工具调用失败: {name}")
                return None

        except Exception as e:
            logger.error(f"调用工具失败: {e}")
            return None

    def thinking_step(
        self, thought: str, thought_number: int = 1, next_needed: bool = True
    ) -> Optional[str]:
        """执行思维链步骤"""
        try:
            if not self.is_connected:
                return None

            # 构建思维链参数
            arguments = {
                "thought": thought,
                "thoughtNumber": thought_number,
                "nextThoughtNeeded": next_needed,
            }

            # 调用思维链工具
            result = self.call_tool("sequentialthinking", arguments)
            if result and "content" in result:
                return result["content"][0].get("text", "") if result["content"] else ""

            return None

        except Exception as e:
            logger.error(f"思维链处理失败: {e}")
            return None

    def stop(self):
        """停止 MCP 服务器"""
        try:
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
                logger.info("MCP 服务器已停止")
        except Exception as e:
            logger.error(f"停止 MCP 服务器失败: {e}")
            if self.process:
                self.process.kill()
        finally:
            self.process = None
            self.is_connected = False

    def is_available(self) -> bool:
        """检查 MCP 服务是否可用"""
        return self.is_connected and self.process and self.process.poll() is None

    def get_tools_info(self) -> List[Dict[str, Any]]:
        """获取工具信息"""
        return self.tools.copy()


# 如果直接运行此文件，进行简单测试
if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)

    client = SimpleMCPClient()

    print("测试 MCP 客户端...")
    if client.start_and_initialize():
        print("✅ MCP 客户端初始化成功")

        # 测试思维链
        result = client.thinking_step("测试思维链功能", 1, False)
        if result:
            print(f"✅ 思维链测试成功: {result}")
        else:
            print("❌ 思维链测试失败")

        client.stop()
    else:
        print("❌ MCP 客户端初始化失败")
