"""messages.py A2A 集成测试

测试：
- POST /api/messages 走 a2a_router.route_execution
- POST /api/a2a/cancel 返回 200
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
)

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _make_async_iter(items):
    """创建一个 async generator，yield 列表中的每个元素"""
    async def _gen():
        for item in items:
            yield item
    return _gen()


@pytest.fixture
def client():
    """创建 TestClient，mock 掉外部依赖"""
    app = FastAPI()

    # Mock 掉所有外部依赖，让 messages 路由可以加载
    mock_memory = AsyncMock()
    mock_memory.get_messages = AsyncMock(return_value=[])
    mock_memory.add_message = AsyncMock(
        return_value={"id": "msg_test", "role": "user", "content": "hi"}
    )
    mock_memory.get_context_for_agent = AsyncMock(return_value="")

    mock_db = AsyncMock()
    mock_db.add_message = AsyncMock(return_value=None)
    mock_db.get_messages = AsyncMock(return_value=[])

    mock_sse = AsyncMock()
    mock_sse.broadcast = AsyncMock()
    mock_sse.broadcast_stream_chunk = AsyncMock()

    mock_message_router = MagicMock()
    mock_message_router.parse.return_value = {
        "content": "hello",
        "target": [],
        "is_broadcast": False,
        "is_termination": False,
    }

    mock_a2a = AsyncMock()

    with (
        patch("agenthub.backend.services.memory_manager.redis_memory_manager", mock_memory),
        patch("agenthub.backend.services.memory_manager.memory_manager", mock_memory),
        patch("agenthub.backend.routers.messages.memory", mock_memory),
        patch("agenthub.backend.routers.messages.get_db", AsyncMock(return_value=mock_db)),
        patch("agenthub.backend.routers.messages.sse_manager", mock_sse),
        patch("agenthub.backend.routers.messages.message_router", mock_message_router),
        patch("agenthub.backend.routers.messages.a2a_router", mock_a2a),
    ):
        # 需要重新导入 router 以让 patch 生效
        from agenthub.backend.routers.messages import router
        app.include_router(router)
        yield TestClient(app), mock_a2a, mock_memory, mock_sse, mock_message_router, mock_db


class TestA2ACancelEndpoint:
    """POST /api/a2a/cancel 测试"""

    def test_cancel_returns_200(self, client):
        """cancel 请求返回 200 + ok 状态"""
        test_client, mock_a2a, *_ = client
        resp = test_client.post("/api/a2a/cancel", params={"thread_id": "t1"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["thread_id"] == "t1"
        mock_a2a.cancel_thread.assert_called_once_with("t1")

    def test_cancel_missing_thread_id_returns_422(self, client):
        """缺少 thread_id 参数返回 422"""
        test_client, *_ = client
        resp = test_client.post("/api/a2a/cancel")
        assert resp.status_code == 422


class TestSendMessageWithA2ARouter:
    """POST /api/messages 走 a2a_router 路径测试"""

    def test_send_message_with_agent_id_routes_through_a2a(self, client):
        """指定 agent_id 时走 a2a_router.route_execution"""
        test_client, mock_a2a, mock_memory, mock_sse, mock_msg_router, mock_db = client

        # mock a2a_router.route_execution 返回空 async iterator
        mock_a2a.route_execution = MagicMock(
            return_value=_make_async_iter([])
        )

        resp = test_client.post(
            "/api/messages",
            json={
                "content": "hello",
                "sender": "user",
                "sender_name": "User",
                "agent_id": "designer",
                "user_id": "u1",
                "thread_id": "t1",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["is_a2a"] is True

        # 验证 route_execution 被调用，且 initial_agents 包含 designer
        mock_a2a.route_execution.assert_called_once()
        call_kwargs = mock_a2a.route_execution.call_args
        assert call_kwargs.kwargs["initial_agents"] == ["designer"]
        assert call_kwargs.kwargs["message"] == "hello"
        assert call_kwargs.kwargs["thread_id"] == "t1"

    def test_send_message_broadcasts_a2a_events(self, client):
        """a2a_router 回调触发正确的 SSE 广播"""
        test_client, mock_a2a, mock_memory, mock_sse, mock_msg_router, mock_db = client

        # 捕获传给 route_execution 的回调参数
        captured_callbacks = {}

        async def fake_route_execution(**kwargs):
            captured_callbacks.update(kwargs)
            # 模拟 yield 事件
            yield {"type": "a2a_start", "agent_id": "designer", "depth": 1}
            yield {"type": "a2a_chunk", "agent_id": "designer", "content": "hi"}
            yield {"type": "a2a_done", "agent_id": "designer", "response": "hi"}
            yield {"type": "a2a_complete", "is_final": True}

        def route_execution_side_effect(**kwargs):
            # 在 mock 被调用时创建 async generator，此时 kwargs 已可用
            return fake_route_execution(**kwargs)

        mock_a2a.route_execution = MagicMock(
            side_effect=route_execution_side_effect
        )

        resp = test_client.post(
            "/api/messages",
            json={
                "content": "分析需求",
                "sender": "user",
                "sender_name": "User",
                "agent_id": "designer",
                "user_id": "u1",
                "thread_id": "t1",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["is_a2a"] is True

        # 验证回调函数被传入
        assert "on_agent_start" in captured_callbacks
        assert "on_agent_chunk" in captured_callbacks
        assert "on_agent_done" in captured_callbacks
        assert "on_a2a_complete" in captured_callbacks
        assert "on_a2a_cancelled" in captured_callbacks
