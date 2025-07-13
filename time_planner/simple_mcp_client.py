"""
简化的MCP客户端 - 基于成功的测试脚本
"""

import subprocess
import json
import time
import threading
from typing import Dict, Any, Optional, List
from loguru import logger


class SimpleMCPClient:
    """简化的MCP客户端 - 直接基于成功的测试逻辑"""

    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.is_initialized = False
        self.tools: List[Dict[str, Any]] = []

    def start_and_initialize(self) -> bool:
        """启动并初始化MCP服务器"""
        try:
            # 启动MCP服务器
            logger.info("启动 MCP 服务器...")
            self.process = subprocess.Popen(
                ["node", "sequentialthinking/dist/index.js"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
            )

            # 等待服务器启动
            time.sleep(2)

            # 发送初始化请求
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "AI Time Management System",
                        "version": "1.0.0",
                    },
                },
            }

            logger.info("发送初始化请求...")
            request_json = json.dumps(init_request) + "\n"
            self.process.stdin.write(request_json)
            self.process.stdin.flush()

            # 等待初始化响应
            if self._wait_for_response(1, timeout=5):
                logger.info("MCP 初始化成功")

                # 获取工具列表
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {},
                }

                logger.info("获取工具列表...")
                tools_json = json.dumps(tools_request) + "\n"
                self.process.stdin.write(tools_json)
                self.process.stdin.flush()

                # 等待工具列表响应
                tools_response = self._wait_for_response(2, timeout=5)
                if tools_response and "result" in tools_response:
                    self.tools = tools_response["result"].get("tools", [])
                    logger.info(f"获取到 {len(self.tools)} 个工具")
                    self.is_initialized = True
                    return True

            logger.error("MCP 初始化失败")
            self.stop()
            return False

        except Exception as e:
            logger.error(f"启动 MCP 服务器失败: {e}")
            self.stop()
            return False

    def _wait_for_response(
        self, expected_id: int, timeout: float = 5.0
    ) -> Optional[Dict[str, Any]]:
        """等待特定ID的响应"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.process and self.process.stdout.readable():
                line = self.process.stdout.readline()
                if line:
                    line = line.strip()

                    # 只处理JSON响应
                    if line.startswith("{") and line.endswith("}"):
                        try:
                            response = json.loads(line)
                            if response.get("id") == expected_id:
                                logger.debug(f"收到响应 ID {expected_id}: {response}")
                                return response
                        except json.JSONDecodeError:
                            pass
                    else:
                        # 服务器日志消息
                        logger.debug(f"MCP 服务器日志: {line}")

            time.sleep(0.1)

        logger.warning(f"等待响应 ID {expected_id} 超时")
        return None

    def call_sequential_thinking(
        self,
        thought: str,
        thought_number: int = 1,
        total_thoughts: int = 1,
        next_thought_needed: bool = False,
    ) -> Optional[str]:
        """调用 sequential thinking 工具"""
        if not self.is_initialized:
            logger.warning("MCP 客户端未初始化")
            return None

        try:
            request_id = int(time.time() * 1000) % 10000  # 简单的请求ID生成

            request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": "sequentialthinking",
                    "arguments": {
                        "thought": thought,
                        "thoughtNumber": thought_number,
                        "totalThoughts": total_thoughts,
                        "nextThoughtNeeded": next_thought_needed,
                    },
                },
            }

            logger.debug(f"调用 sequential thinking: {thought[:50]}...")
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json)
            self.process.stdin.flush()

            # 等待响应
            response = self._wait_for_response(request_id, timeout=10)
            if response and "result" in response:
                content = response["result"].get("content", [])
                if content and len(content) > 0:
                    return content[0].get("text", "")

            return None

        except Exception as e:
            logger.error(f"调用 sequential thinking 失败: {e}")
            return None

    def stop(self):
        """停止MCP服务器"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
                logger.info("MCP 服务器已停止")
            except:
                if self.process:
                    self.process.kill()
            finally:
                self.process = None
                self.is_initialized = False

    def is_available(self) -> bool:
        """检查MCP客户端是否可用"""
        return self.is_initialized and self.process and self.process.poll() is None
