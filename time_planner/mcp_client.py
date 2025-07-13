"""
时间规划系统 - MCP 客户端模块

这个模块负责与 MCP (Model Context Protocol) 服务器通信，
特别是与 Sequential Thinking 服务器进行思维链交互。

主要功能：
- 启动和管理 MCP 服务器进程
- 发送 JSON-RPC 请求到 MCP 服务器
- 处理思维链的步骤化思考过程
- 管理与大语言模型的交互

作者：AI Assistant
日期：2025-07-13
"""

import subprocess
import json
import asyncio
import os
from typing import Dict, Any, Optional, List
from uuid import uuid4
from loguru import logger
import threading
import queue
import time


class MCPClient:
    """MCP 客户端 - 管理与 MCP 服务器的通信"""

    def __init__(self, server_command: str = None):
        """
        初始化 MCP 客户端

        Args:
            server_command: MCP 服务器启动命令
        """
        # 如果没有指定命令，尝试本地目录
        if server_command is None:
            import os

            # 检查本地 sequentialthinking 目录
            local_mcp_path = os.path.join(os.getcwd(), "sequentialthinking")
            if os.path.exists(local_mcp_path):
                # 检查是否有编译后的 dist 目录
                dist_path = os.path.join(local_mcp_path, "dist", "index.js")
                if os.path.exists(dist_path):
                    self.server_command = f"node {dist_path}"
                    logger.info(f"使用本地编译的 MCP 服务器: {self.server_command}")
                else:
                    # 尝试直接运行 TypeScript（需要 ts-node）
                    index_ts = os.path.join(local_mcp_path, "index.ts")
                    if os.path.exists(index_ts):
                        self.server_command = f"npx ts-node {index_ts}"
                        logger.info(
                            f"使用 ts-node 运行本地 MCP 服务器: {self.server_command}"
                        )
                    else:
                        logger.warning("本地 MCP 服务器未找到，使用全局版本")
                        self.server_command = "mcp-server-sequential-thinking"
            else:
                # 回退到全局安装的版本
                self.server_command = "mcp-server-sequential-thinking"
                logger.info("使用全局安装的 MCP 服务器")
        else:
            self.server_command = server_command
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        self.response_queue = queue.Queue()
        self.reader_thread: Optional[threading.Thread] = None
        self.is_running = False

        logger.info(f"MCP 客户端初始化: {server_command}")

    def start_server(self) -> bool:
        """
        启动 MCP 服务器进程

        Returns:
            bool: 是否启动成功
        """
        try:
            # 启动 MCP 服务器进程
            self.process = subprocess.Popen(
                self.server_command.split(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,  # 无缓冲
            )

            # 启动输出读取线程
            self.reader_thread = threading.Thread(target=self._read_output, daemon=True)
            self.reader_thread.start()

            self.is_running = True
            logger.info("MCP 服务器启动成功")

            # 等待服务器完全启动（与测试脚本一致）
            time.sleep(2)

            # 执行 MCP 初始化握手
            if self._initialize_mcp():
                # 测试连接
                if self._test_connection():
                    return True
                else:
                    self.stop_server()
                    return False
            else:
                self.stop_server()
                return False

        except Exception as e:
            logger.error(f"启动 MCP 服务器失败: {e}")
            return False

    def stop_server(self):
        """停止 MCP 服务器进程"""
        self.is_running = False

        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                logger.info("MCP 服务器已停止")
            except subprocess.TimeoutExpired:
                self.process.kill()
                logger.warning("MCP 服务器被强制终止")
            except Exception as e:
                logger.error(f"停止 MCP 服务器时出错: {e}")
            finally:
                self.process = None

    def _read_output(self):
        """在后台线程中读取服务器输出"""
        if not self.process or not self.process.stdout:
            return

        try:
            while self.is_running and self.process.poll() is None:
                line = self.process.stdout.readline()
                if line:
                    line = line.strip()
                    if line:
                        # 尝试解析 JSON 响应
                        if line.startswith("{") and line.endswith("}"):
                            try:
                                response = json.loads(line)
                                self.response_queue.put(response)
                                logger.info(
                                    f"收到 MCP 响应: {response.get('id', 'unknown')}"
                                )
                                logger.debug(f"响应详情: {response}")
                            except json.JSONDecodeError as e:
                                logger.warning(f"无法解析 MCP 响应: {line}, 错误: {e}")
                        else:
                            # 非JSON消息，可能是服务器日志
                            logger.info(f"MCP 服务器日志: {line}")
        except Exception as e:
            logger.error(f"读取 MCP 输出时出错: {e}")

    def _test_connection(self) -> bool:
        """测试与 MCP 服务器的连接，包含重试机制"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"MCP连接测试 第{attempt + 1}次尝试...")
                # 发送 ListTools 请求测试连接
                response = self.send_request("tools/list", {}, timeout=15.0)
                if response is not None and "result" in response:
                    logger.info("MCP连接测试成功")
                    return True
                else:
                    logger.warning(f"MCP连接测试失败，尝试 {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        time.sleep(2)  # 等待后重试
            except Exception as e:
                logger.error(
                    f"MCP 连接测试失败 (尝试 {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(2)  # 等待后重试

        logger.error("MCP连接测试最终失败")
        return False

    def send_request(
        self, method: str, params: Dict[str, Any], timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """
        发送 JSON-RPC 请求到 MCP 服务器

        Args:
            method: RPC 方法名
            params: 请求参数
            timeout: 超时时间（秒）

        Returns:
            Optional[Dict[str, Any]]: 服务器响应，如果失败返回 None
        """
        if not self.process or not self.is_running:
            logger.error("MCP 服务器未运行")
            return None

        # 生成请求 ID
        self.request_id += 1
        request_id = self.request_id

        # 构造 JSON-RPC 请求
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        try:
            # 发送请求
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json)
            self.process.stdin.flush()

            logger.info(f"发送 MCP 请求: {method} (ID: {request_id})")
            logger.debug(f"请求详情: {request_json.strip()}")

            # 等待响应
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    response = self.response_queue.get(timeout=0.5)  # 增加超时时间
                    if response.get("id") == request_id:
                        logger.info(
                            f"收到 MCP 响应: {method} (ID: {request_id}) - 成功"
                        )
                        return response
                    else:
                        # 不是我们要的响应，放回队列
                        logger.debug(
                            f"收到其他响应 ID: {response.get('id')}, 期望: {request_id}"
                        )
                        self.response_queue.put(response)
                except queue.Empty:
                    continue

            logger.warning(f"MCP 请求超时: method={method}, timeout={timeout}s")
            return None

        except Exception as e:
            logger.error(f"发送 MCP 请求失败: {e}")
            return None

    def list_tools(self) -> Optional[List[Dict[str, Any]]]:
        """
        获取可用工具列表

        Returns:
            Optional[List[Dict[str, Any]]]: 工具列表
        """
        response = self.send_request("tools/list", {})
        if response and "result" in response:
            tools = response["result"].get("tools", [])
            logger.info(f"获取到 {len(tools)} 个可用工具")
            return tools
        return None

    def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        调用指定工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            Optional[Dict[str, Any]]: 工具执行结果
        """
        params = {"name": tool_name, "arguments": arguments}

        response = self.send_request("tools/call", params)
        if response and "result" in response:
            logger.info(f"工具调用成功: {tool_name}")
            return response["result"]
        else:
            logger.error(f"工具调用失败: {tool_name}")
            return None

    def _initialize_mcp(self) -> bool:
        """
        执行 MCP 协议初始化握手

        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("开始 MCP 协议初始化...")

            # 发送初始化请求（与测试脚本相同的参数）
            init_params = {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "AI Time Management System", "version": "1.0.0"},
            }

            response = self.send_request("initialize", init_params, timeout=10.0)

            if response and "result" in response:
                result = response["result"]
                logger.info(
                    f"MCP 协议初始化成功: {result.get('serverInfo', {}).get('name', 'unknown')}"
                )

                # 发送 initialized 通知
                self._send_notification("notifications/initialized")
                return True
            else:
                logger.error(f"MCP 初始化失败：无有效响应 - {response}")
                return False

        except Exception as e:
            logger.error(f"MCP 初始化异常: {e}")
            return False

    def _send_notification(self, method: str, params: Dict[str, Any] = None):
        """
        发送 JSON-RPC 通知（无需响应）

        Args:
            method: 通知方法名
            params: 通知参数
        """
        if not self.process or not self.is_running:
            return

        if params is None:
            params = {}

        try:
            notification = {"jsonrpc": "2.0", "method": method, "params": params}

            notification_json = json.dumps(notification) + "\n"
            self.process.stdin.write(notification_json)
            self.process.stdin.flush()

            logger.debug(f"发送 MCP 通知: {notification}")

        except Exception as e:
            logger.error(f"发送 MCP 通知失败: {e}")


class SequentialThinkingClient:
    """Sequential Thinking 客户端 - 专门处理思维链相关的操作"""

    def __init__(self, mcp_client: MCPClient):
        """
        初始化思维链客户端

        Args:
            mcp_client: MCP 客户端实例
        """
        self.mcp_client = mcp_client
        self.thinking_session_id: Optional[str] = None
        logger.info("Sequential Thinking 客户端初始化完成")

    def start_thinking_session(self) -> str:
        """
        开始新的思维链会话

        Returns:
            str: 会话ID
        """
        self.thinking_session_id = str(uuid4())
        logger.info(f"开始思维链会话: {self.thinking_session_id}")
        return self.thinking_session_id

    def think_step(
        self,
        thought: str,
        thought_number: int,
        total_thoughts: Optional[int] = None,
        next_thought_needed: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        执行思维链的一个步骤

        Args:
            thought: 当前步骤的思考内容
            thought_number: 思考步骤编号
            total_thoughts: 总思考步骤数（可选）
            next_thought_needed: 是否需要下一步思考
            context: 上下文信息

        Returns:
            Optional[Dict[str, Any]]: 思考结果
        """
        arguments = {
            "thought": thought,
            "thoughtNumber": thought_number,
            "nextThoughtNeeded": next_thought_needed,
        }

        if total_thoughts is not None:
            arguments["totalThoughts"] = total_thoughts

        if context:
            arguments["context"] = context

        if self.thinking_session_id:
            arguments["sessionId"] = self.thinking_session_id

        logger.info(f"执行思维链步骤 {thought_number}: {thought[:50]}...")

        result = self.mcp_client.call_tool("sequentialthinking", arguments)

        if result:
            logger.info(f"思维链步骤 {thought_number} 完成")
        else:
            logger.error(f"思维链步骤 {thought_number} 失败")

        return result

    def complete_thinking_chain(
        self, thinking_steps: List[str], context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        完成完整的思维链过程

        Args:
            thinking_steps: 思维步骤列表
            context: 上下文信息

        Returns:
            List[Dict[str, Any]]: 所有思维步骤的结果
        """
        session_id = self.start_thinking_session()
        results = []

        total_steps = len(thinking_steps)

        for i, thought in enumerate(thinking_steps, 1):
            is_last_step = i == total_steps

            result = self.think_step(
                thought=thought,
                thought_number=i,
                total_thoughts=total_steps,
                next_thought_needed=not is_last_step,
                context=context,
            )

            if result:
                results.append(result)
                # 更新上下文以包含前一步的结果
                if context is None:
                    context = {}
                context[f"step_{i}_result"] = result
            else:
                logger.error(f"思维链在第 {i} 步中断")
                break

        logger.info(f"思维链会话 {session_id} 完成，共 {len(results)} 步")
        return results


class MCPManager:
    """MCP 管理器 - 统一管理所有 MCP 相关的操作"""

    def __init__(self, server_command: str = None):
        """
        初始化 MCP 管理器

        Args:
            server_command: MCP 服务器命令，如果为 None 则从环境变量读取
        """
        if server_command is None:
            # 检查本地 sequentialthinking 项目
            local_mcp_path = os.path.join(
                os.getcwd(), "sequentialthinking", "dist", "index.js"
            )
            if os.path.exists(local_mcp_path):
                server_command = f"node {local_mcp_path}"
                logger.info("使用本地 MCP 服务器")
            else:
                # 尝试使用全局安装的版本
                server_command = "mcp-server-sequential-thinking"
                logger.info("使用全局安装的 MCP 服务器")

        self.mcp_client = MCPClient(server_command)
        self.thinking_client = SequentialThinkingClient(self.mcp_client)
        self.is_initialized = False

        logger.info(f"MCP 管理器初始化完成，使用命令: {server_command}")

    def initialize(self) -> bool:
        """
        初始化 MCP 服务

        Returns:
            bool: 是否初始化成功
        """
        if self.is_initialized:
            return True

        # 启动 MCP 服务器
        if not self.mcp_client.start_server():
            logger.error("MCP 服务器启动失败")
            return False

        # 验证工具可用性
        tools = self.mcp_client.list_tools()
        if not tools:
            logger.error("无法获取工具列表")
            self.mcp_client.stop_server()
            return False

        # 检查是否有 sequential thinking 工具
        tool_names = [tool.get("name", "") for tool in tools]
        if "sequentialthinking" not in tool_names:
            logger.error("Sequential Thinking 工具不可用")
            self.mcp_client.stop_server()
            return False

        self.is_initialized = True
        logger.info("MCP 服务初始化成功")
        return True

    def shutdown(self):
        """关闭 MCP 服务"""
        if self.mcp_client:
            self.mcp_client.stop_server()
        self.is_initialized = False
        logger.info("MCP 服务已关闭")

    def get_thinking_client(self) -> Optional[SequentialThinkingClient]:
        """获取思维链客户端"""
        if self.is_initialized:
            return self.thinking_client
        return None

    def __enter__(self):
        """上下文管理器入口"""
        if not self.initialize():
            raise RuntimeError("MCP 服务初始化失败")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.shutdown()


# 导出主要类
__all__ = ["MCPClient", "SequentialThinkingClient", "MCPManager"]
