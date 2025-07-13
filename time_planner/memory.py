"""
时间管理系统 - 对话记忆管理模块

实现智能对话记忆功能，支持多层级记忆管理和持久化存储

作者：AI Assistant
日期：2025-07-13
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
from loguru import logger


class MessageType(str, Enum):
    """消息类型枚举"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


class MessageImportance(str, Enum):
    """消息重要性枚举"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConversationMessage:
    """对话消息类"""

    def __init__(
        self,
        content: str,
        message_type: MessageType = MessageType.USER,
        importance: MessageImportance = MessageImportance.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(content) % 1000}"
        self.timestamp = datetime.now().isoformat()
        self.content = content
        self.message_type = message_type
        self.importance = importance
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "message_type": self.message_type.value,
            "content": self.content,
            "importance": self.importance.value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMessage":
        """从字典创建实例"""
        msg = cls(
            content=data["content"],
            message_type=MessageType(data["message_type"]),
            importance=MessageImportance(data["importance"]),
            metadata=data.get("metadata", {}),
        )
        msg.id = data["id"]
        msg.timestamp = data["timestamp"]
        return msg


class ConversationMemory:
    """对话记忆管理器"""

    def __init__(
        self,
        memory_file: str = "conversation_memory.json",
        max_recent_messages: int = 20,
        max_total_messages: int = 100,
        summary_threshold: int = 50,
    ):
        """初始化对话记忆管理器"""
        self.memory_file = memory_file
        self.max_recent_messages = max_recent_messages
        self.max_total_messages = max_total_messages
        self.summary_threshold = summary_threshold

        self.messages: List[ConversationMessage] = []
        self.conversation_summary = ""
        self.session_start = datetime.now()

        self._load_memory()
        logger.info(f"对话记忆管理器初始化完成，加载了 {len(self.messages)} 条历史记录")

    def add_message(
        self,
        content: str,
        message_type: MessageType = MessageType.USER,
        importance: MessageImportance = MessageImportance.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """添加消息到记忆中"""
        message = ConversationMessage(content, message_type, importance, metadata)
        self.messages.append(message)

        # 检查是否需要清理记忆
        self._check_memory_cleanup()

        # 保存到文件
        self._save_memory()

        logger.debug(f"添加消息到记忆: {message_type.value} - {content[:50]}...")

    def get_recent_context(self, max_messages: int = None) -> List[str]:
        """获取最近的对话上下文"""
        limit = max_messages or self.max_recent_messages
        recent_messages = self.messages[-limit:]

        context = []
        for msg in recent_messages:
            prefix = "用户" if msg.message_type == MessageType.USER else "助手"
            context.append(f"{prefix}: {msg.content}")

        return context

    def get_structured_context(self, max_messages: int = None) -> List[Dict[str, str]]:
        """获取结构化的对话上下文"""
        limit = max_messages or self.max_recent_messages
        recent_messages = self.messages[-limit:]

        context = []
        for msg in recent_messages:
            context.append(
                {
                    "role": (
                        "user" if msg.message_type == MessageType.USER else "assistant"
                    ),
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "importance": msg.importance.value,
                }
            )

        return context

    def get_important_context(self) -> List[ConversationMessage]:
        """获取重要消息上下文"""
        return [
            msg
            for msg in self.messages
            if msg.importance in [MessageImportance.HIGH, MessageImportance.CRITICAL]
        ]

    def search_history(self, keyword: str, limit: int = 5) -> List[ConversationMessage]:
        """搜索历史记录"""
        keyword_lower = keyword.lower()
        results = []

        for msg in reversed(self.messages):
            if keyword_lower in msg.content.lower():
                results.append(msg)
                if len(results) >= limit:
                    break

        return results

    def _auto_determine_importance(
        self, content: str, message_type: MessageType
    ) -> MessageImportance:
        """自动判断消息重要性"""
        content_lower = content.lower()

        # 关键词判断
        critical_keywords = ["紧急", "重要", "立即", "马上", "错误", "失败"]
        high_keywords = ["任务", "计划", "安排", "会议", "截止", "提醒"]

        if any(keyword in content_lower for keyword in critical_keywords):
            return MessageImportance.CRITICAL
        elif any(keyword in content_lower for keyword in high_keywords):
            return MessageImportance.HIGH
        elif message_type == MessageType.SYSTEM:
            return MessageImportance.HIGH
        else:
            return MessageImportance.MEDIUM

    def _check_memory_cleanup(self):
        """检查是否需要清理记忆"""
        if len(self.messages) > self.summary_threshold:
            self._create_summary()

        if len(self.messages) > self.max_total_messages:
            self._cleanup_old_messages()

    def _create_summary(self):
        """创建对话摘要"""
        # 简化版摘要生成
        old_messages = self.messages[: -self.max_recent_messages]

        if old_messages:
            user_messages = [
                msg.content
                for msg in old_messages
                if msg.message_type == MessageType.USER
            ]
            summary_points = []

            # 提取关键信息
            for content in user_messages[-10:]:  # 最近10条用户消息
                if any(
                    keyword in content for keyword in ["我叫", "我是", "姓名", "名字"]
                ):
                    summary_points.append(f"用户信息: {content}")
                elif any(keyword in content for keyword in ["安排", "计划", "任务"]):
                    summary_points.append(f"时间安排: {content}")

            self.conversation_summary = "; ".join(summary_points)
            logger.info(f"创建对话摘要: {len(summary_points)} 个要点")

    def _cleanup_old_messages(self):
        """清理旧消息"""
        # 保留重要消息和最近消息
        important_messages = [
            msg
            for msg in self.messages
            if msg.importance in [MessageImportance.HIGH, MessageImportance.CRITICAL]
        ]

        recent_messages = self.messages[-self.max_recent_messages :]

        # 合并去重
        kept_messages = []
        seen_ids = set()

        for msg in important_messages + recent_messages:
            if msg.id not in seen_ids:
                kept_messages.append(msg)
                seen_ids.add(msg.id)

        # 按时间排序
        kept_messages.sort(key=lambda x: x.timestamp)

        removed_count = len(self.messages) - len(kept_messages)
        self.messages = kept_messages

        logger.info(f"清理了 {removed_count} 条旧消息，保留 {len(kept_messages)} 条")

    def _load_memory(self):
        """从文件加载记忆"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.conversation_summary = data.get("summary", "")
                self.session_start = datetime.fromisoformat(
                    data.get("session_start", datetime.now().isoformat())
                )

                # 加载消息
                self.messages = []
                for msg_data in data.get("messages", []):
                    self.messages.append(ConversationMessage.from_dict(msg_data))

                logger.debug(f"从文件加载了 {len(self.messages)} 条记忆")

            except Exception as e:
                logger.error(f"加载记忆文件失败: {e}")
                self.messages = []
        else:
            logger.info(f"对话记忆文件 {self.memory_file} 不存在，将创建新文件")

    def _save_memory(self):
        """保存记忆到文件"""
        try:
            data = {
                "summary": self.conversation_summary,
                "session_start": self.session_start.isoformat(),
                "last_updated": datetime.now().isoformat(),
                "messages": [msg.to_dict() for msg in self.messages],
            }

            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存记忆文件失败: {e}")

    def clear_session(self):
        """清除当前会话的记忆"""
        self.messages = []
        self.conversation_summary = ""
        self.session_start = datetime.now()
        self._save_memory()
        logger.info("已清除当前会话记忆")

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        importance_counts = {}
        for importance in MessageImportance:
            importance_counts[importance.value] = len(
                [msg for msg in self.messages if msg.importance == importance]
            )

        return {
            "total_messages": len(self.messages),
            "summary_length": len(self.conversation_summary),
            "session_duration": (datetime.now() - self.session_start).total_seconds()
            / 3600,  # 小时
            "importance_distribution": importance_counts,
            "memory_file_size": (
                os.path.getsize(self.memory_file)
                if os.path.exists(self.memory_file)
                else 0
            ),
        }

    def get_total_message_count(self) -> int:
        """获取总消息数量"""
        return len(self.messages)

    def get_conversation_context_for_ai(self, max_messages: int = None) -> str:
        """获取适合AI直接使用的对话上下文字符串"""
        limit = max_messages or self.max_recent_messages
        recent_messages = self.messages[-limit:]

        if not recent_messages:
            return ""

        context_lines = ["\\n\\n📝 对话历史记录："]

        for msg in recent_messages:
            if msg.message_type == MessageType.USER:
                context_lines.append(f"👤 用户: {msg.content}")
            elif msg.message_type == MessageType.ASSISTANT:
                context_lines.append(f"🤖 助手: {msg.content}")

        return "\\n".join(context_lines)

    def get_user_profile_context(self) -> Dict[str, Any]:
        """获取用户档案上下文"""
        profile = {"name": None, "age": None, "occupation": None}

        # 从所有消息中提取用户信息
        for msg in self.messages:
            if msg.message_type == MessageType.USER:
                content = msg.content

                # 提取姓名
                name_patterns = [
                    r"我叫([\\u4e00-\\u9fa5a-zA-Z]+)",
                    r"我的名字是([\\u4e00-\\u9fa5a-zA-Z]+)",
                    r"我是([\\u4e00-\\u9fa5a-zA-Z]+)",
                ]
                for pattern in name_patterns:
                    match = re.search(pattern, content)
                    if match:
                        profile["name"] = match.group(1)
                        break

                # 提取年龄
                age_patterns = [r"我(今年)?([0-9]+)岁", r"年龄是?([0-9]+)"]
                for pattern in age_patterns:
                    match = re.search(pattern, content)
                    if match:
                        profile["age"] = (
                            match.group(2)
                            if len(match.groups()) > 1
                            else match.group(1)
                        )
                        break

                # 提取职业
                job_patterns = [
                    r"我是(一名|一个)?([\\u4e00-\\u9fa5]+工程师|[\\u4e00-\\u9fa5]+师|[\\u4e00-\\u9fa5]+员)",
                    r"职业是([\\u4e00-\\u9fa5a-zA-Z]+)",
                    r"工作是([\\u4e00-\\u9fa5a-zA-Z]+)",
                ]
                for pattern in job_patterns:
                    match = re.search(pattern, content)
                    if match:
                        profile["occupation"] = (
                            match.group(2)
                            if len(match.groups()) > 1
                            else match.group(1)
                        )
                        break

        return profile
