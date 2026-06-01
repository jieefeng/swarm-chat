"""SSE连接管理器 - 支持线程隔离"""
import asyncio
import threading
from typing import Dict, Optional
from collections.abc import AsyncGenerator
import json


class SSEManager:
    """管理Server-Sent Events连接

    支持按 thread_id 过滤事件，实现线程隔离。
    """

    def __init__(self):
        # subscribers: {queue: Optional[thread_id]}
        self.subscribers: Dict[asyncio.Queue, Optional[str]] = {}
        self._lock = threading.Lock()

    async def subscribe(self, thread_id: Optional[str] = None) -> AsyncGenerator[dict, None]:
        """订阅SSE事件流

        Args:
            thread_id: 订阅指定线程的事件。None 表示接收所有事件。
        """
        queue: asyncio.Queue = asyncio.Queue()
        with self._lock:
            self.subscribers[queue] = thread_id
        print(f"[SSE SUBSCRIBE] Subscriber added (thread_id={thread_id}). Total: {len(self.subscribers)}")

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield event
                except asyncio.TimeoutError:
                    yield {"event": "keepalive", "data": json.dumps({"status": "ping"})}
        finally:
            with self._lock:
                del self.subscribers[queue]
            print(f"[SSE SUBSCRIBE] Subscriber removed. Total: {len(self.subscribers)}")

    async def broadcast(self, event_type: str, data: dict, thread_id: Optional[str] = None):
        """广播事件到订阅者

        Args:
            event_type: 事件类型
            data: 事件数据
            thread_id: 线程 ID。如果指定，只发给订阅了该线程的客户端。
        """
        data_str = json.dumps(data, ensure_ascii=False)
        print(f"[SSE BROADCAST] type={event_type}, thread_id={thread_id}, data={data_str[:200]}")
        event = {"event": event_type, "data": data_str}

        # 过滤逻辑：
        # - subscriber_thread_id=None: 接收所有事件
        # - subscriber_thread_id=thread_id: 只接收该线程的事件
        # - thread_id=None: 全局事件，所有订阅者都能收到
        # Copy targets under lock, then release and iterate
        with self._lock:
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

    async def broadcast_clarification_request(self, message_id: str, question: str, options: list[str]) -> None:
        """广播 HITL 澄清请求"""
        await self.broadcast("clarification_request", {
            "message_id": message_id,
            "question": question,
            "options": options,
        })

    def get_subscriber_count(self) -> int:
        """获取当前订阅者数量"""
        with self._lock:
            return len(self.subscribers)


# 全局SSE管理器实例
sse_manager = SSEManager()
