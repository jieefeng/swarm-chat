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

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    yield event
                except asyncio.TimeoutError:
                    yield "keepalive: ping\n\n"
        finally:
            with self._lock:
                self.subscribers.remove(queue)

    async def broadcast(self, event_type: str, data: dict):
        """广播事件到所有订阅者"""
        message = f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        with self._lock:
            for queue in self.subscribers:
                await queue.put(message)

    def get_subscriber_count(self) -> int:
        """获取当前订阅者数量"""
        with self._lock:
            return len(self.subscribers)


# 全局SSE管理器实例
sse_manager = SSEManager()