"""SSE连接管理器 - 支持线程隔离"""
import asyncio
import logging
from typing import Dict, Optional
from collections.abc import AsyncGenerator
import json

logger = logging.getLogger(__name__)


class SSEManager:
    """管理Server-Sent Events连接

    支持按 thread_id 过滤事件，实现线程隔离。
    """

    def __init__(self):
        # subscribers: {queue: Optional[thread_id]}
        self.subscribers: Dict[asyncio.Queue, Optional[str]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, thread_id: Optional[str] = None) -> AsyncGenerator[dict, None]:
        """订阅SSE事件流

        Args:
            thread_id: 订阅指定线程的事件。None 表示接收所有事件。
        """
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self.subscribers[queue] = thread_id
        logger.info("Subscriber added (thread_id=%s). Total: %d", thread_id, len(self.subscribers))

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield event
                except asyncio.TimeoutError:
                    yield {"event": "keepalive", "data": json.dumps({"status": "ping"})}
        finally:
            async with self._lock:
                del self.subscribers[queue]
            logger.info("Subscriber removed. Total: %d", len(self.subscribers))

    async def broadcast(self, event_type: str, data: dict, thread_id: Optional[str] = None):
        """广播事件到订阅者

        Args:
            event_type: 事件类型
            data: 事件数据
            thread_id: 线程 ID。如果指定，只发给订阅了该线程的客户端。
        """
        data_str = json.dumps(data, ensure_ascii=False)
        logger.debug("Broadcast type=%s, thread_id=%s", event_type, thread_id)
        event = {"event": event_type, "data": data_str}

        # 过滤逻辑：
        # - subscriber_thread_id=None: 接收所有事件
        # - subscriber_thread_id=thread_id: 只接收该线程的事件
        # - thread_id=None: 全局事件，所有订阅者都能收到
        # Copy targets under lock, then release and iterate
        async with self._lock:
            targets = [
                q for q, sid in self.subscribers.items()
                if sid is None or thread_id is None or sid == thread_id
            ]
        for queue in targets:
            await queue.put(event)

    async def broadcast_stream_chunk(self, message_id: str, chunk: str, seq: int,
                                      thread_id: Optional[str] = None) -> None:
        """广播流式文本片段"""
        await self.broadcast("stream_chunk", {
            "message_id": message_id,
            "chunk": chunk,
            "seq": seq,
        }, thread_id=thread_id)

    async def broadcast_task_created(self, task_id: str, title: str, assigned_to: str) -> None:
        """广播任务创建事件"""
        await self.broadcast("task_created", {
            "task_id": task_id,
            "title": title,
            "assigned_to": assigned_to,
        })

    async def broadcast_task_update(self, task_id: str, status: str, title: str) -> None:
        """广播任务状态变更"""
        await self.broadcast("task_update", {
            "task_id": task_id,
            "status": status,
            "title": title,
        })

    async def broadcast_clarification_request(self, message_id: str, question: str, options: list[str],
                                               thread_id: str | None = None) -> None:
        """广播 HITL 澄清请求"""
        await self.broadcast("clarification_request", {
            "message_id": message_id,
            "question": question,
            "options": options,
        }, thread_id=thread_id)

    async def get_subscriber_count(self) -> int:
        """获取当前订阅者数量"""
        async with self._lock:
            return len(self.subscribers)

    async def broadcast_tool_start(self, agent_id: str, command: str,
                                    message_id: str, thread_id: str | None = None) -> None:
        """广播工具开始执行事件"""
        await self.broadcast("tool_start", {
            "agent_id": agent_id,
            "command": command,
            "message_id": message_id,
        }, thread_id=thread_id)

    async def broadcast_tool_progress(self, agent_id: str, output: str,
                                       message_id: str, thread_id: str | None = None) -> None:
        """广播工具执行进度"""
        await self.broadcast("tool_progress", {
            "agent_id": agent_id,
            "output": output,
            "message_id": message_id,
        }, thread_id=thread_id)

    async def broadcast_tool_result(self, agent_id: str, content: str, success: bool,
                                     message_id: str, thread_id: str | None = None) -> None:
        """广播工具执行结果"""
        await self.broadcast("tool_result", {
            "agent_id": agent_id,
            "content": content,
            "success": success,
            "message_id": message_id,
        }, thread_id=thread_id)

    # A2A 事件广播方法
    async def broadcast_a2a_start(self, agent_id: str, depth: int,
                                   thread_id: str | None = None) -> None:
        """广播 A2A 链开始执行事件"""
        await self.broadcast("a2a_start", {
            "agent_id": agent_id,
            "depth": depth,
        }, thread_id=thread_id)

    async def broadcast_a2a_progress(self, agent_id: str, depth: int,
                                      thread_id: str | None = None) -> None:
        """广播 A2A 链执行进度"""
        await self.broadcast("a2a_progress", {
            "agent_id": agent_id,
            "depth": depth,
        }, thread_id=thread_id)

    async def broadcast_a2a_done(self, is_final: bool,
                                  thread_id: str | None = None) -> None:
        """广播 A2A 链完成事件"""
        await self.broadcast("a2a_done", {
            "is_final": is_final,
        }, thread_id=thread_id)

    async def broadcast_a2a_cancelled(self, reason: str,
                                       thread_id: str | None = None) -> None:
        """广播 A2A 链取消事件"""
        await self.broadcast("a2a_cancelled", {
            "reason": reason,
        }, thread_id=thread_id)

    async def broadcast_a2a_error(self, error: str,
                                   thread_id: str | None = None) -> None:
        """广播 A2A 链错误事件"""
        await self.broadcast("a2a_error", {
            "error": error,
        }, thread_id=thread_id)


# 全局SSE管理器实例
sse_manager = SSEManager()
