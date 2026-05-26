"""SSE连接管理器 - 修复内存泄漏"""
import asyncio
import threading
from typing import Dict, Set
from collections.abc import AsyncGenerator
import json


class SSEManager:
    """管理Server-Sent Events连接"""

    def __init__(self):
        self.subscribers: Set[asyncio.Queue] = set()
        self._lock = threading.Lock()

    async def subscribe(self) -> AsyncGenerator[str, None]:
        """订阅SSE事件流"""
        queue: asyncio.Queue = asyncio.Queue()
        with self._lock:
            self.subscribers.add(queue)
        print(f"[SSE SUBSCRIBE] Subscriber added. Total: {len(self.subscribers)}")

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    print(f"[SSE SUBSCRIBE] Got event from queue: {event[:100]}...")
                    yield event
                except asyncio.TimeoutError:
                    yield "keepalive: ping\n\n"
        finally:
            with self._lock:
                self.subscribers.remove(queue)
            print(f"[SSE SUBSCRIBE] Subscriber removed. Total: {len(self.subscribers)}")

    async def broadcast(self, event_type: str, data: dict):
        """广播事件到所有订阅者"""
        message = f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        print(f"[SSE BROADCAST] type={event_type}, data={json.dumps(data, ensure_ascii=False)[:200]}")
        with self._lock:
            for queue in self.subscribers:
                await queue.put(message)

    async def broadcast_stream_chunk(self, message_id: str, chunk: str, seq: int) -> None:
        """广播流式文本片段"""
        await self.broadcast("stream_chunk", {
            "message_id": message_id,
            "chunk": chunk,
            "seq": seq,
        })

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

    async def broadcast_artifact_diff(self, task_id: str, file_path: str, old_content: str, new_content: str) -> None:
        """广播代码 Diff"""
        await self.broadcast("artifact_diff", {
            "task_id": task_id,
            "file_path": file_path,
            "old_content": old_content,
            "new_content": new_content,
        })

    def get_subscriber_count(self) -> int:
        """获取当前订阅者数量"""
        with self._lock:
            return len(self.subscribers)


# 全局SSE管理器实例
sse_manager = SSEManager()