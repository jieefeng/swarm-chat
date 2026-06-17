"""CallbackRouter 单元测试（验证已存在实现，mock memory/sse/a2a_router）"""
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
)

from agenthub.backend.services.callback_router import CallbackRouter
from agenthub.backend.services.invocation_registry import InvocationRegistry


@pytest.fixture
def mock_memory():
    m = MagicMock()
    m.add_message = AsyncMock(return_value={"id": "msg-1"})
    m.get_messages = AsyncMock(return_value=[
        {"id": "1", "content": "hello", "agent_id": "designer"},
    ])
    return m


@pytest.fixture
def mock_sse():
    m = MagicMock()
    m.broadcast = AsyncMock()
    return m


@pytest.fixture
def mock_a2a_router():
    m = MagicMock()
    m.enqueue_a2a_targets = MagicMock()
    return m


@pytest.fixture
def registry():
    return InvocationRegistry(ttl=10)


@pytest.fixture
def callback_router(mock_memory, mock_sse, mock_a2a_router, registry):
    with patch(
        "agenthub.backend.services.callback_router.memory", mock_memory
    ), patch(
        "agenthub.backend.services.callback_router.sse_manager", mock_sse
    ), patch(
        "agenthub.backend.services.callback_router.a2a_router", mock_a2a_router
    ), patch(
        "agenthub.backend.services.callback_router.invocation_registry", registry
    ), patch(
        "agenthub.backend.services.callback_router.AGENT_CONFIGS",
        {"designer": {"name": "苍龙"}, "developer": {"name": "玄武"}},
    ):
        yield CallbackRouter()


class TestPostMessage:
    async def test_invalid_credentials_raises_value_error(self, callback_router):
        with pytest.raises(ValueError, match="Invalid or expired credentials"):
            await callback_router.post_message("bad-inv", "bad-tok", "hello")

    async def test_valid_credentials_persists_message(
        self, callback_router, mock_memory, mock_sse, registry
    ):
        inv_id, token = registry.create("designer", "thread-1")
        result = await callback_router.post_message(
            inv_id, token, "设计师的回复"
        )
        assert result["status"] == "ok"
        assert result["message_id"] == "msg-1"
        mock_memory.add_message.assert_called_once()
        args, kwargs = mock_memory.add_message.call_args
        assert kwargs["role"] == "designer"
        assert kwargs["content"] == "设计师的回复"
        assert kwargs["thread_id"] == "thread-1"
        mock_sse.broadcast.assert_called_once()
        assert mock_sse.broadcast.call_args[0][0] == "message"

    async def test_with_target_agent_id_enqueues_to_a2a(
        self, callback_router, mock_a2a_router, registry
    ):
        inv_id, token = registry.create("designer", "thread-2")
        await callback_router.post_message(
            inv_id, token, "@developer 接手", target_agent_id="developer"
        )
        mock_a2a_router.enqueue_a2a_targets.assert_called_once_with(
            "thread-2", ["developer"]
        )

    async def test_without_target_agent_id_does_not_enqueue(
        self, callback_router, mock_a2a_router, registry
    ):
        inv_id, token = registry.create("designer", "thread-3")
        await callback_router.post_message(inv_id, token, "普通消息")
        mock_a2a_router.enqueue_a2a_targets.assert_not_called()


class TestGetThreadContext:
    async def test_invalid_credentials_raises(self, callback_router):
        with pytest.raises(ValueError):
            await callback_router.get_thread_context("bad", "bad")

    async def test_returns_messages(
        self, callback_router, mock_memory, registry
    ):
        inv_id, token = registry.create("developer", "thread-4")
        result = await callback_router.get_thread_context(inv_id, token)
        assert len(result["messages"]) == 1
        assert result["messages"][0]["content"] == "hello"
        mock_memory.get_messages.assert_called_once_with(thread_id="thread-4")


class TestGetPendingMentions:
    async def test_invalid_credentials_raises(self, callback_router):
        with pytest.raises(ValueError):
            await callback_router.get_pending_mentions("bad", "bad")

    async def test_returns_mentions_to_current_agent(
        self, callback_router, mock_memory, registry
    ):
        mock_memory.get_messages = AsyncMock(return_value=[
            {
                "id": "m1",
                "content": "@designer 你来",
                "agent_id": "developer",
                "timestamp": "2026-06-17T00:00:00",
            },
            {
                "id": "m2",
                "content": "普通消息",
                "agent_id": "user",
                "timestamp": "2026-06-17T00:00:01",
            },
        ])
        inv_id, token = registry.create("designer", "thread-5")
        result = await callback_router.get_pending_mentions(inv_id, token)
        assert len(result["mentions"]) == 1
        assert result["mentions"][0]["message_id"] == "m1"
        assert result["mentions"][0]["from_agent"] == "developer"
