"""
对话历史管理模块

实现智能的对话历史记忆功能：
- 保留重要的对话上下文
- 自动压缩和清理历史记录
- 智能摘要长对话内容
- 保持关键信息的持久性

作者：AI Assistant
日期：2025-07-13
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from loguru import logger


class MessageType(Enum):
    """消息类型"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


class MessageImportance(Enum):
    """消息重要性级别"""

    CRITICAL = "critical"  # 关键信息，永久保留
    HIGH = "high"  # 重要信息，长期保留
    MEDIUM = "medium"  # 一般信息，中期保留
    LOW = "low"  # 低重要性，短期保留


@dataclass
class ConversationMessage:
    """对话消息"""

    id: str
    timestamp: datetime
    message_type: MessageType
    content: str
    importance: MessageImportance = MessageImportance.MEDIUM
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "message_type": self.message_type.value,
            "content": self.content,
            "importance": self.importance.value,
            "metadata": self.metadata or {},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMessage":
        """从字典创建对象"""
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            message_type=MessageType(data["message_type"]),
            content=data["content"],
            importance=MessageImportance(data["importance"]),
            metadata=data.get("metadata", {}),
        )


class ConversationMemory:
    """对话记忆管理器"""

    def __init__(
        self,
        memory_file: str = "conversation_memory.json",
        max_recent_messages: int = 20,
        max_total_messages: int = 100,
        summary_threshold: int = 50,
    ):
        """
        初始化对话记忆管理器

        Args:
            memory_file: 记忆文件路径
            max_recent_messages: 最大近期消息数量
            max_total_messages: 最大总消息数量
            summary_threshold: 触发摘要的消息数量阈值
        """
        self.memory_file = memory_file
        self.max_recent_messages = max_recent_messages
        self.max_total_messages = max_total_messages
        self.summary_threshold = summary_threshold

        self.messages: List[ConversationMessage] = []
        self.conversation_summary: str = ""
        self.session_start: datetime = datetime.now()

        self._load_memory()
        logger.info(f"对话记忆管理器初始化完成，加载了 {len(self.messages)} 条历史记录")

    def add_message(
        self,
        content: str,
        message_type: MessageType,
        importance: MessageImportance = MessageImportance.MEDIUM,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        添加新消息到记忆中

        Args:
            content: 消息内容
            message_type: 消息类型
            importance: 重要性级别
            metadata: 附加元数据

        Returns:
            str: 消息ID
        """
        message_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.messages)}"

        # 自动判断重要性
        if not importance:
            importance = self._auto_determine_importance(content, message_type)

        message = ConversationMessage(
            id=message_id,
            timestamp=datetime.now(),
            message_type=message_type,
            content=content,
            importance=importance,
            metadata=metadata,
        )

        self.messages.append(message)
        logger.debug(f"添加消息到记忆: {message_type.value} - {content[:50]}...")

        # 检查是否需要清理记忆
        self._check_memory_cleanup()

        # 保存到文件
        self._save_memory()

        return message_id

    def get_recent_context(self, max_messages: int = None) -> List[str]:
        """
        获取近期对话上下文

        Args:
            max_messages: 最大消息数量

        Returns:
            List[str]: 格式化的对话历史文本
        """
        if max_messages is None:
            max_messages = self.max_recent_messages

        # 获取最近的消息
        recent_messages = self.messages[-max_messages:] if self.messages else []

        # 转换为文本格式
        context = []

        # 添加近期消息
        for msg in recent_messages:
            time_str = msg.timestamp.strftime("%H:%M")
            if msg.message_type == MessageType.USER:
                context.append(f"[{time_str}] 用户: {msg.content}")
            elif msg.message_type == MessageType.ASSISTANT:
                context.append(f"[{time_str}] 助手: {msg.content}")

        return context

    def get_structured_context(self, max_messages: int = None) -> List[Dict[str, str]]:
        """
        获取结构化的对话上下文，包含详细的消息类型和内容

        Args:
            max_messages: 最大消息数量

        Returns:
            List[Dict[str, str]]: 结构化的对话历史
        """
        if max_messages is None:
            max_messages = self.max_recent_messages

        # 获取最近的消息
        recent_messages = self.messages[-max_messages:] if self.messages else []

        # 转换为结构化格式
        context = []
        for msg in recent_messages:
            context.append(
                {
                    "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "type": msg.message_type.value,
                    "content": msg.content,
                    "importance": msg.importance.value,
                }
            )

        return context

    def get_important_context(self) -> List[ConversationMessage]:
        """获取重要的历史上下文"""
        important_messages = [
            msg
            for msg in self.messages
            if msg.importance in [MessageImportance.CRITICAL, MessageImportance.HIGH]
        ]
        return important_messages[-10:]  # 最多返回10条重要消息

    def search_history(self, keyword: str, limit: int = 5) -> List[ConversationMessage]:
        """
        搜索历史对话

        Args:
            keyword: 搜索关键词
            limit: 返回结果数量限制

        Returns:
            List[ConversationMessage]: 匹配的消息列表
        """
        matches = []
        for msg in reversed(self.messages):  # 从最新的开始搜索
            if keyword.lower() in msg.content.lower():
                matches.append(msg)
                if len(matches) >= limit:
                    break
        return matches

    def _auto_determine_importance(
        self, content: str, message_type: MessageType
    ) -> MessageImportance:
        """自动判断消息重要性"""
        # 关键词判断
        critical_keywords = ["创建", "删除", "修改", "安排", "时间", "日程", "任务"]
        high_keywords = ["查询", "显示", "查看", "空闲", "冲突"]

        content_lower = content.lower()

        # 工具调用通常是重要的
        if message_type == MessageType.TOOL_CALL:
            return MessageImportance.HIGH

        # 检查关键词
        if any(keyword in content_lower for keyword in critical_keywords):
            return MessageImportance.HIGH
        elif any(keyword in content_lower for keyword in high_keywords):
            return MessageImportance.MEDIUM

        # 长消息通常更重要
        if len(content) > 200:
            return MessageImportance.MEDIUM

        return MessageImportance.LOW

    def _check_memory_cleanup(self):
        """检查并执行记忆清理"""
        if len(self.messages) > self.summary_threshold:
            self._create_summary()
            self._cleanup_old_messages()

    def _create_summary(self):
        """创建对话摘要"""
        # 获取需要摘要的消息（保留最近的消息不摘要）
        messages_to_summarize = self.messages[: -self.max_recent_messages]

        if not messages_to_summarize:
            return

        # 提取关键信息
        key_actions = []
        for msg in messages_to_summarize:
            if msg.importance in [MessageImportance.CRITICAL, MessageImportance.HIGH]:
                if msg.message_type == MessageType.USER:
                    key_actions.append(f"用户请求: {msg.content[:100]}")
                elif msg.message_type == MessageType.TOOL_CALL:
                    key_actions.append(f"执行操作: {msg.content[:100]}")

        # 生成摘要
        if key_actions:
            self.conversation_summary = "本次对话中的关键操作：" + "; ".join(
                key_actions[-10:]
            )  # 最多保留10个关键操作
            logger.info(f"生成对话摘要: {len(key_actions)} 个关键操作")

    def _cleanup_old_messages(self):
        """清理旧消息"""
        if len(self.messages) <= self.max_total_messages:
            return

        # 保留关键和高重要性的消息
        important_messages = [
            msg
            for msg in self.messages
            if msg.importance in [MessageImportance.CRITICAL, MessageImportance.HIGH]
        ]

        # 保留最近的消息
        recent_messages = self.messages[-self.max_recent_messages :]

        # 合并并去重
        kept_messages = []
        kept_ids = set()

        for msg in important_messages + recent_messages:
            if msg.id not in kept_ids:
                kept_messages.append(msg)
                kept_ids.add(msg.id)

        # 按时间排序
        kept_messages.sort(key=lambda x: x.timestamp)

        removed_count = len(self.messages) - len(kept_messages)
        self.messages = kept_messages

        if removed_count > 0:
            logger.info(
                f"清理了 {removed_count} 条旧消息，保留 {len(self.messages)} 条重要消息"
            )

    def _load_memory(self):
        """从文件加载记忆"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.conversation_summary = data.get("summary", "")

                for msg_data in data.get("messages", []):
                    message = ConversationMessage.from_dict(msg_data)
                    self.messages.append(message)

                logger.info(
                    f"从 {self.memory_file} 加载了 {len(self.messages)} 条历史记录"
                )
            except Exception as e:
                logger.error(f"加载对话记忆失败: {e}")
                self.messages = []
                self.conversation_summary = ""
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

            os.makedirs(
                (
                    os.path.dirname(self.memory_file)
                    if os.path.dirname(self.memory_file)
                    else "."
                ),
                exist_ok=True,
            )

            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"保存了 {len(self.messages)} 条记忆到 {self.memory_file}")
        except Exception as e:
            logger.error(f"保存对话记忆失败: {e}")

    def clear_session(self):
        """清理当前会话（保留重要历史）"""
        # 只保留关键消息
        important_messages = [
            msg for msg in self.messages if msg.importance == MessageImportance.CRITICAL
        ]

        removed_count = len(self.messages) - len(important_messages)
        self.messages = important_messages
        self.session_start = datetime.now()

        self._save_memory()
        logger.info(
            f"清理会话，移除了 {removed_count} 条消息，保留 {len(self.messages)} 条关键消息"
        )

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

    def get_conversation_context_for_ai(self, max_messages: int = None) -> str:
        """
        获取适合AI直接使用的对话上下文字符串

        Args:
            max_messages: 最大消息数量

        Returns:
            str: 格式化的对话历史字符串，可直接添加到系统提示词
        """
        if max_messages is None:
            max_messages = self.max_recent_messages

        # 获取最近的消息
        recent_messages = self.messages[-max_messages:] if self.messages else []

        if not recent_messages:
            return ""

        context_lines = []
        context_lines.append("\n" + "=" * 50)
        context_lines.append("💬 对话历史上下文")
        context_lines.append("=" * 50)

        # 简化格式，突出重要信息
        for i, msg in enumerate(recent_messages, 1):
            if msg.message_type == MessageType.USER:
                # 检查是否包含重要的个人信息
                content = msg.content
                if any(
                    keyword in content
                    for keyword in ["我叫", "我是", "我的名字", "我今年", "岁"]
                ):
                    context_lines.append(f"🔥 重要: {content}")
                else:
                    context_lines.append(f"用户说: {content}")
            elif msg.message_type == MessageType.ASSISTANT:
                context_lines.append(f"我回复: {content}")

        context_lines.append("=" * 50)
        context_lines.append("📝 说明：上面是完整的对话记录")
        context_lines.append("🎯 当用户询问之前的信息时，请直接从上面的记录中查找答案")
        context_lines.append("=" * 50)

        return "\n".join(context_lines)

    def get_user_profile_context(self) -> Dict[str, Any]:
        """
        从对话历史中提取用户画像信息

        Returns:
            Dict[str, Any]: 用户画像信息
        """
        profile = {
            "name": None,
            "age": None,
            "occupation": None,
            "preferences": [],
            "important_info": [],
        }

        # 分析最近的消息，提取用户信息
        for msg in reversed(self.messages[-20:]):  # 只分析最近20条消息
            if msg.message_type == MessageType.USER:
                content = msg.content

                # 提取姓名
                if not profile["name"]:
                    import re

                    name_patterns = [
                        r"我叫(.+?)(?:，|。|$)",
                        r"我的名字(?:是|叫)(.+?)(?:，|。|$)",
                        r"我是(.+?)(?:，|。|$)",
                        r"叫我(.+?)(?:，|。|$)",
                    ]
                    for pattern in name_patterns:
                        match = re.search(pattern, content)
                        if match:
                            name = match.group(1).strip()
                            # 过滤问句
                            if (
                                "?" not in name
                                and "？" not in name
                                and "什么" not in name
                            ):
                                profile["name"] = name
                                break

                # 提取年龄
                if not profile["age"]:
                    age_match = re.search(r"我(?:今年)?(\d+)岁", content)
                    if age_match:
                        profile["age"] = int(age_match.group(1))

                # 提取职业
                if not profile["occupation"]:
                    job_patterns = [
                        r"我是(?:一名|一个)?(.+?)(?:，|。|$)",
                        r"我的职业是(.+?)(?:，|。|$)",
                        r"我从事(.+?)(?:工作|行业)",
                    ]
                    for pattern in job_patterns:
                        match = re.search(pattern, content)
                        if match:
                            job = match.group(1).strip()
                            # 过滤无效职业和问句
                            if (
                                job not in ["学生", "人", "什么", "谁"]
                                and len(job) < 20
                                and "?" not in job
                                and "？" not in job
                                and "什么" not in job
                                and "多大" not in job
                                and "职业" not in job
                            ):
                                profile["occupation"] = job
                                break

        return profile

    def get_total_message_count(self) -> int:
        """获取总消息数量"""
        return len(self.messages)


# 导出主要类
__all__ = [
    "ConversationMemory",
    "MessageType",
    "MessageImportance",
    "ConversationMessage",
]
