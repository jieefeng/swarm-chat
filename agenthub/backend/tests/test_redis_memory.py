"""RedisMemoryManager 单元测试（使用 fakeredis）"""
import pytest
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fakeredis.aioredis
from agenthub.backend.services.memory_manager import RedisMemoryManager


@pytest.fixture
async def redis_memory():
    """创建使用 fakeredis 的 RedisMemoryManager 实例"""
    fake_server = fakeredis.aioredis.FakeServer()
    client = fakeredis.aioredis.FakeRedis(server=fake_server, decode_responses=True)
    manager = RedisMemoryManager.__new__(RedisMemoryManager)
    manager.redis = client
    manager.max_messages = 1000
    manager.ttl_seconds = 30 * 86400
    yield manager
    await client.aclose()


class TestRedisMemoryManager:
    """RedisMemoryManager 测试类"""

    @pytest.mark.asyncio
    async def test_add_user_message(self, redis_memory):
        """添加用户消息后，消息包含正确的字段"""
        msg = await redis_memory.add_message(role="user", content="你好")
        assert msg["role"] == "user"
        assert msg["content"] == "你好"
        assert msg["type"] == "user"
        assert "id" in msg
        assert "timestamp" in msg

    @pytest.mark.asyncio
    async def test_add_agent_message(self, redis_memory):
        """添加 Agent 消息后，type 为 agent"""
        msg = await redis_memory.add_message(
            role="agent", content="我是助手", agent_id="pm",
            sender_name="产品经理"
        )
        assert msg["role"] == "agent"
        assert msg["type"] == "agent"
        assert msg["agent_id"] == "pm"
        assert msg["sender_name"] == "产品经理"

    @pytest.mark.asyncio
    async def test_get_messages_returns_latest(self, redis_memory):
        """get_messages 返回最近的消息，按时间正序"""
        for i in range(5):
            await redis_memory.add_message(role="user", content=f"消息{i}")
        messages = await redis_memory.get_messages(limit=3)
        assert len(messages) == 3
        assert messages[0]["content"] == "消息2"
        assert messages[2]["content"] == "消息4"

    @pytest.mark.asyncio
    async def test_max_messages_trim(self, redis_memory):
        """超过 max_messages 后，旧消息被淘汰"""
        redis_memory.max_messages = 10
        for i in range(15):
            await redis_memory.add_message(role="user", content=f"消息{i}")
        messages = await redis_memory.get_messages(limit=50)
        assert len(messages) == 10
        assert messages[-1]["content"] == "消息14"

    @pytest.mark.asyncio
    async def test_user_isolation(self, redis_memory):
        """不同用户的消息互相隔离"""
        await redis_memory.add_message(role="user", content="用户A的消息", user_id="user_a")
        await redis_memory.add_message(role="user", content="用户B的消息", user_id="user_b")
        msgs_a = await redis_memory.get_messages(user_id="user_a")
        msgs_b = await redis_memory.get_messages(user_id="user_b")
        assert len(msgs_a) == 1
        assert len(msgs_b) == 1
        assert msgs_a[0]["content"] == "用户A的消息"
        assert msgs_b[0]["content"] == "用户B的消息"

    @pytest.mark.asyncio
    async def test_clear(self, redis_memory):
        """clear 删除指定用户的所有消息"""
        await redis_memory.add_message(role="user", content="测试", user_id="u1")
        await redis_memory.clear(user_id="u1")
        messages = await redis_memory.get_messages(user_id="u1")
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_get_context_for_agent(self, redis_memory):
        """get_context_for_agent 返回格式化的上下文字符串"""
        await redis_memory.add_message(role="user", content="你好")
        await redis_memory.add_message(role="agent", content="你好，我是PM", agent_id="pm")
        context = await redis_memory.get_context_for_agent(agent_id="pm", limit=5)
        assert "[user]: 你好" in context
        assert "[agent]: 你好，我是PM" in context

    @pytest.mark.asyncio
    async def test_default_user_id(self, redis_memory):
        """不指定 user_id 时使用 default"""
        await redis_memory.add_message(role="user", content="默认用户")
        messages = await redis_memory.get_messages()
        assert len(messages) == 1
        assert messages[0]["content"] == "默认用户"
