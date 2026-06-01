"""线程管理服务 - CRUD + 消息存储"""
from datetime import datetime, timezone
from typing import Optional

from agenthub.backend.models.thread import Thread, ThreadMessage, ThreadStatus


class ThreadManager:
    """线程管理器

    负责线程的 CRUD 操作和消息存储。
    当前使用内存存储，后续可升级为 Redis/SQLite。
    """

    def __init__(self):
        self._threads: dict[str, Thread] = {}
        self._messages: dict[str, list[ThreadMessage]] = {}

    async def create_thread(self, title: str, created_by: str = "user",
                            description: str | None = None) -> Thread:
        """创建新线程"""
        thread = Thread(
            title=title,
            created_by=created_by,
            description=description,
        )
        self._threads[thread.id] = thread
        self._messages[thread.id] = []
        return thread

    async def get_thread(self, thread_id: str) -> Optional[Thread]:
        """获取线程"""
        return self._threads.get(thread_id)

    async def list_threads(self, status: str = "active") -> list[Thread]:
        """获取线程列表"""
        return [
            t for t in self._threads.values()
            if t.status == status
        ]

    async def archive_thread(self, thread_id: str) -> bool:
        """归档线程"""
        thread = self._threads.get(thread_id)
        if not thread:
            return False
        thread.status = ThreadStatus.ARCHIVED
        thread.updated_at = datetime.now(tz=timezone.utc)
        return True

    async def add_message(self, thread_id: str, sender_id: str,
                          content: str, mentions: list[str] | None = None,
                          reply_to: str | None = None) -> Optional[ThreadMessage]:
        """添加消息到线程"""
        if thread_id not in self._threads:
            return None

        message = ThreadMessage(
            thread_id=thread_id,
            sender_id=sender_id,
            content=content,
            mentions=mentions or [],
            reply_to=reply_to,
        )
        self._messages[thread_id].append(message)

        # 自动更新 participants
        thread = self._threads[thread_id]
        if sender_id not in thread.participants and sender_id != "user":
            thread.participants.append(sender_id)
        for agent_id in message.mentions:
            if agent_id not in thread.participants:
                thread.participants.append(agent_id)

        thread.updated_at = datetime.now(tz=timezone.utc)
        return message

    async def get_messages(self, thread_id: str, limit: int = 50) -> list[ThreadMessage]:
        """获取线程消息历史"""
        messages = self._messages.get(thread_id, [])
        return messages[-limit:]

    async def get_thread_context(self, thread_id: str, limit: int = 20) -> str:
        """获取线程上下文，格式化为 LLM 可用的字符串"""
        messages = await self.get_messages(thread_id, limit=limit)
        if not messages:
            return ""

        context_lines = []
        for msg in messages:
            role = "用户" if msg.sender_id == "user" else msg.sender_id
            context_lines.append(f"{role}: {msg.content}")

        return "\n".join(context_lines)


# 全局实例
thread_manager = ThreadManager()
