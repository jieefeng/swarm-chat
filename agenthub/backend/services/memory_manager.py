"""内存管理器 - 消息历史存储"""
import uuid
from typing import List, Dict, Optional
from datetime import datetime


class MemoryManager:
    """管理对话消息历史"""

    def __init__(self, max_messages: int = 1000):
        self.messages: List[Dict] = []
        self.max_messages = max_messages

    async def add_message(self, role: str, content: str, user_id: str = "default", agent_id: Optional[str] = None, sender_name: Optional[str] = None) -> Dict:
        """添加消息到历史，返回消息字典（含id）"""
        message = {
            "id": f"msg_{uuid.uuid4().hex[:8]}",
            "role": role,
            "content": content,
            "agent_id": agent_id,
            "sender_name": sender_name or role,
            "timestamp": int(datetime.now().timestamp()),
            "type": "user" if role == "user" else "agent",
        }
        self.messages.append(message)

        # 保持消息数量在限制内
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

        return message

    async def get_messages(self, user_id: str = "default", limit: int = 50) -> List[Dict]:
        """获取最近的消息"""
        return self.messages[-limit:] if limit > 0 else self.messages

    async def get_context_for_agent(self, agent_id: str, user_id: str = "default", limit: int = 10) -> str:
        """获取指定Agent的上下文

        Args:
            agent_id: Agent ID
            limit: 返回消息条数

        Returns:
            格式化的上下文字符串
        """
        recent = await self.get_messages(user_id=user_id, limit=limit)
        context_parts = []
        for msg in recent:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:200]  # 截断到200字符
            context_parts.append(f"[{role}]: {content}")
        return "\n".join(context_parts)

    async def clear(self, user_id: str = "default"):
        """清空消息历史"""
        self.messages.clear()


# 全局内存管理器实例
memory_manager = MemoryManager()


import os
import json
import logging

logger = logging.getLogger(__name__)


class RedisMemoryManager:
    """基于 Redis List 的消息存储管理器"""

    def __init__(self, redis_url: str = "redis://localhost:6379",
                 max_messages: int = 1000, ttl_days: int = 30):
        import redis.asyncio as aioredis
        self.redis = aioredis.from_url(redis_url, decode_responses=True, protocol=2)
        self.max_messages = max_messages
        self.ttl_seconds = ttl_days * 86400

    def _key(self, user_id: str) -> str:
        return f"chat:messages:{user_id}"

    async def add_message(self, role: str, content: str,
                          user_id: str = "default",
                          agent_id: Optional[str] = None,
                          sender_name: Optional[str] = None) -> Dict:
        message = {
            "id": f"msg_{uuid.uuid4().hex[:8]}",
            "role": role,
            "content": content,
            "agent_id": agent_id,
            "sender_name": sender_name or role,
            "timestamp": int(datetime.now().timestamp()),
            "type": "user" if role == "user" else "agent",
        }
        key = self._key(user_id)
        await self.redis.lpush(key, json.dumps(message, ensure_ascii=False))
        await self.redis.ltrim(key, 0, self.max_messages - 1)
        await self.redis.expire(key, self.ttl_seconds)
        return message

    async def get_messages(self, user_id: str = "default",
                           limit: int = 50) -> List[Dict]:
        key = self._key(user_id)
        raw = await self.redis.lrange(key, 0, limit - 1)
        return [json.loads(item) for item in reversed(raw)]

    async def get_context_for_agent(self, agent_id: str,
                                     user_id: str = "default",
                                     limit: int = 10) -> str:
        recent = await self.get_messages(user_id=user_id, limit=limit)
        context_parts = []
        for msg in recent:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]
            context_parts.append(f"[{role}]: {content}")
        return "\n".join(context_parts)

    async def clear(self, user_id: str = "default"):
        await self.redis.delete(self._key(user_id))

    async def close(self):
        await self.redis.close()


def create_memory_manager():
    """根据 STORAGE_BACKEND 环境变量创建对应的 memory manager"""
    backend = os.getenv("STORAGE_BACKEND", "memory")
    if backend == "redis":
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        max_messages = int(os.getenv("MAX_MESSAGES", "1000"))
        ttl_days = int(os.getenv("MESSAGE_TTL_DAYS", "30"))
        try:
            # Test connection synchronously (from_url is lazy, won't fail at construction)
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
            logger.warning(f"Redis connection failed: {e}, falling back to memory")
            return MemoryManager(max_messages=max_messages)
    return MemoryManager(max_messages=int(os.getenv("MAX_MESSAGES", "1000")))


redis_memory_manager = create_memory_manager()