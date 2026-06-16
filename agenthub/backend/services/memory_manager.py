"""内存管理器 - 消息历史存储"""
import uuid
import os
from typing import List, Dict, Optional
from datetime import datetime
from collections import OrderedDict


class MemoryManager:
    """管理对话消息历史（按线程隔离）"""

    def __init__(self, max_messages: int = 1000, max_threads: int = 100):
        """
        Args:
            max_messages: 每个线程的最大消息数
            max_threads: 最大线程数（防止内存无限增长）
        """
        self._threads: OrderedDict[str, List[Dict]] = OrderedDict()  # thread_id -> messages
        self.max_messages = max_messages
        self.max_threads = max_threads

    def _get_thread(self, thread_id: str) -> List[Dict]:
        if thread_id not in self._threads:
            # 如果达到线程数上限，删除最旧的线程
            if len(self._threads) >= self.max_threads:
                oldest_thread_id, _ = self._threads.popitem(last=False)
                print(f"[MEMORY] Evicted oldest thread {oldest_thread_id} (max_threads={self.max_threads})")
            self._threads[thread_id] = []
        return self._threads[thread_id]

    async def add_message(self, role: str, content: str, user_id: str = "default",
                          agent_id: Optional[str] = None, sender_name: Optional[str] = None,
                          thread_id: str = "default") -> Dict:
        """添加消息到历史，返回消息字典（含id）"""
        message = {
            "id": f"msg_{uuid.uuid4().hex[:8]}",
            "role": role,
            "content": content,
            "agent_id": agent_id,
            "sender_name": sender_name or role,
            "timestamp": int(datetime.now().timestamp()),
            "type": "user" if role == "user" else "agent",
            "thread_id": thread_id,
        }
        thread = self._get_thread(thread_id)
        thread.append(message)

        if len(thread) > self.max_messages:
            self._threads[thread_id] = thread[-self.max_messages:]

        return message

    async def get_messages(self, user_id: str = "default", limit: int = 50,
                           thread_id: str = "default") -> List[Dict]:
        """获取最近的消息"""
        thread = self._get_thread(thread_id)
        return thread[-limit:] if limit > 0 else thread

    async def get_context_for_agent(self, agent_id: str, user_id: str = "default",
                                    limit: int = 10, thread_id: str = "default") -> str:
        """获取指定Agent的上下文"""
        recent = await self.get_messages(user_id=user_id, limit=limit, thread_id=thread_id)
        context_parts = []
        for msg in recent:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:200]
            context_parts.append(f"[{role}]: {content}")
        return "\n".join(context_parts)

    async def clear(self, user_id: str = "default", thread_id: Optional[str] = None):
        """清空消息历史。thread_id 为 None 时清空所有线程。"""
        if thread_id is not None:
            self._threads.pop(thread_id, None)
        else:
            self._threads.clear()


# 全局内存管理器实例（可通过环境变量配置）
memory_manager = MemoryManager(
    max_messages=int(os.getenv("MAX_MESSAGES", "1000")),
    max_threads=int(os.getenv("MAX_THREADS", "100")),
)


import os
import json
import logging

logger = logging.getLogger(__name__)


class RedisMemoryManager:
    """基于 Redis List 的消息存储管理器（按线程隔离）"""

    def __init__(self, redis_url: str = "redis://localhost:6379",
                 max_messages: int = 1000, ttl_days: int = 30):
        import redis.asyncio as aioredis
        self.redis = aioredis.from_url(redis_url, decode_responses=True, protocol=2)
        self.max_messages = max_messages
        self.ttl_seconds = ttl_days * 86400

    def _key(self, user_id: str, thread_id: str = "default") -> str:
        return f"chat:messages:{user_id}:{thread_id}"

    async def add_message(self, role: str, content: str,
                          user_id: str = "default",
                          agent_id: Optional[str] = None,
                          sender_name: Optional[str] = None,
                          thread_id: str = "default") -> Dict:
        message = {
            "id": f"msg_{uuid.uuid4().hex[:8]}",
            "role": role,
            "content": content,
            "agent_id": agent_id,
            "sender_name": sender_name or role,
            "timestamp": int(datetime.now().timestamp()),
            "type": "user" if role == "user" else "agent",
            "thread_id": thread_id,
        }
        key = self._key(user_id, thread_id)
        await self.redis.lpush(key, json.dumps(message, ensure_ascii=False))
        await self.redis.ltrim(key, 0, self.max_messages - 1)
        await self.redis.expire(key, self.ttl_seconds)
        return message

    async def get_messages(self, user_id: str = "default",
                           limit: int = 50,
                           thread_id: str = "default") -> List[Dict]:
        key = self._key(user_id, thread_id)
        raw = await self.redis.lrange(key, 0, limit - 1)
        return [json.loads(item) for item in reversed(raw)]

    async def get_context_for_agent(self, agent_id: str,
                                     user_id: str = "default",
                                     limit: int = 10,
                                     thread_id: str = "default") -> str:
        recent = await self.get_messages(user_id=user_id, limit=limit, thread_id=thread_id)
        context_parts = []
        for msg in recent:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]
            context_parts.append(f"[{role}]: {content}")
        return "\n".join(context_parts)

    async def clear(self, user_id: str = "default", thread_id: Optional[str] = None):
        if thread_id is not None:
            await self.redis.delete(self._key(user_id, thread_id))
        else:
            # 清空用户所有线程
            pattern = f"chat:messages:{user_id}:*"
            async for key in self.redis.scan_iter(match=pattern):
                await self.redis.delete(key)

    async def close(self):
        await self.redis.close()


def create_memory_manager():
    """根据 STORAGE_BACKEND 环境变量创建对应的 memory manager。

    sqlite 模式复用 database.py 的单例连接，避免创建冗余实例和路径不一致。
    """
    backend = os.getenv("STORAGE_BACKEND", "sqlite")
    max_messages = int(os.getenv("MAX_MESSAGES", "1000"))

    if backend == "redis":
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        ttl_days = int(os.getenv("MESSAGE_TTL_DAYS", "30"))
        try:
            import redis as sync_redis
            client = sync_redis.from_url(redis_url, protocol=2)
            client.ping()
            client.close()
            manager = RedisMemoryManager(
                redis_url=redis_url,
                max_messages=max_messages,
                ttl_days=ttl_days,
            )
            logger.info(f"RedisMemoryManager initialized: {redis_url}")
            return manager
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, falling back to sqlite")
            backend = "sqlite"

    if backend == "sqlite":
        from .database import sqlite_manager
        logger.info("Using shared SQLiteManager from database module")
        return sqlite_manager

    return MemoryManager(max_messages=max_messages)


redis_memory_manager = create_memory_manager()