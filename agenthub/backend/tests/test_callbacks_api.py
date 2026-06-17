"""Callbacks API 集成测试

测试 HTTP 端点层：请求验证、401 凭证错误、200 正常响应。
服务层 (CallbackRouter) 已在 test_callback_router.py 中测试，
此处仅测试 HTTP 层，使用 mock 替换服务方法。
"""
import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
)

from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agenthub.backend.routers.callbacks import router
from agenthub.backend.services.invocation_registry import InvocationRegistry


@pytest.fixture
def registry():
    """每个测试独立的 InvocationRegistry"""
    return InvocationRegistry(ttl=3600)


@pytest.fixture
def valid_creds(registry):
    """生成一组有效凭证"""
    inv_id, token = registry.create(agent_id="designer", thread_id="thread-1")
    return inv_id, token


@pytest.fixture
def client(registry):
    """注入独立 registry 并返回 TestClient"""
    app = FastAPI()
    app.include_router(router)

    with patch(
        "agenthub.backend.routers.callbacks.callback_router"
    ) as mock_router, patch(
        "agenthub.backend.services.callback_router.invocation_registry", registry
    ):
        # 默认让 verify 通过（实际由 router 内部调用 callback_router，
        # 而 callback_router 自己调用 registry.verify）
        # 但这里我们 mock 了整个 callback_router，所以 verify 逻辑在 mock 里
        yield TestClient(app), mock_router, registry


def _make_creds(registry: InvocationRegistry):
    """创建并返回 (invocation_id, callback_token)"""
    return registry.create(agent_id="designer", thread_id="thread-1")


class TestPostMessageAPI:
    """POST /api/callbacks/post-message 测试"""

    def test_returns_401_on_bad_credentials(self, client):
        """bad creds → 401"""
        test_client, mock_router, _ = client
        mock_router.post_message = AsyncMock(
            side_effect=ValueError("Invalid or expired credentials")
        )

        resp = test_client.post(
            "/api/callbacks/post-message",
            json={
                "invocation_id": "bad-id",
                "callback_token": "bad-token",
                "content": "hello",
            },
        )
        assert resp.status_code == 401
        assert "Invalid" in resp.json()["detail"]

    def test_returns_200_with_message_id(self, client):
        """good creds → 200 + message_id"""
        test_client, mock_router, _ = client
        mock_router.post_message = AsyncMock(
            return_value={"status": "ok", "message_id": "msg-001"}
        )

        resp = test_client.post(
            "/api/callbacks/post-message",
            json={
                "invocation_id": "inv-1",
                "callback_token": "tok-1",
                "content": "hello team",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["message_id"] == "msg-001"
        mock_router.post_message.assert_awaited_once_with(
            invocation_id="inv-1",
            callback_token="tok-1",
            content="hello team",
            target_agent_id=None,
        )

    def test_returns_200_with_target_agent_id(self, client):
        """good creds + target_agent_id → 200"""
        test_client, mock_router, _ = client
        mock_router.post_message = AsyncMock(
            return_value={"status": "ok", "message_id": "msg-002"}
        )

        resp = test_client.post(
            "/api/callbacks/post-message",
            json={
                "invocation_id": "inv-2",
                "callback_token": "tok-2",
                "content": "@developer 请帮忙",
                "target_agent_id": "developer",
            },
        )
        assert resp.status_code == 200
        mock_router.post_message.assert_awaited_once_with(
            invocation_id="inv-2",
            callback_token="tok-2",
            content="@developer 请帮忙",
            target_agent_id="developer",
        )


class TestThreadContextAPI:
    """GET /api/callbacks/thread-context 测试"""

    def test_returns_401_on_bad_credentials(self, client):
        """bad creds → 401"""
        test_client, mock_router, _ = client
        mock_router.get_thread_context = AsyncMock(
            side_effect=ValueError("Invalid or expired credentials")
        )

        resp = test_client.get(
            "/api/callbacks/thread-context",
            params={"invocation_id": "bad", "callback_token": "bad"},
        )
        assert resp.status_code == 401

    def test_returns_200_with_messages(self, client):
        """good creds → 200 + messages list"""
        test_client, mock_router, _ = client
        fake_messages = [
            {"id": "m1", "content": "hello"},
            {"id": "m2", "content": "world"},
        ]
        mock_router.get_thread_context = AsyncMock(
            return_value={"messages": fake_messages}
        )

        resp = test_client.get(
            "/api/callbacks/thread-context",
            params={"invocation_id": "inv-3", "callback_token": "tok-3"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["messages"]) == 2
        assert data["messages"][0]["content"] == "hello"
        mock_router.get_thread_context.assert_awaited_once_with(
            invocation_id="inv-3", callback_token="tok-3"
        )


class TestPendingMentionsAPI:
    """GET /api/callbacks/pending-mentions 测试"""

    def test_returns_401_on_bad_credentials(self, client):
        """bad creds → 401"""
        test_client, mock_router, _ = client
        mock_router.get_pending_mentions = AsyncMock(
            side_effect=ValueError("Invalid or expired credentials")
        )

        resp = test_client.get(
            "/api/callbacks/pending-mentions",
            params={"invocation_id": "bad", "callback_token": "bad"},
        )
        assert resp.status_code == 401

    def test_returns_200_with_mentions(self, client):
        """good creds → 200 + mentions list"""
        test_client, mock_router, _ = client
        fake_mentions = [
            {"message_id": "m1", "from_agent": "designer", "content": "@developer hi"},
        ]
        mock_router.get_pending_mentions = AsyncMock(
            return_value={"mentions": fake_mentions}
        )

        resp = test_client.get(
            "/api/callbacks/pending-mentions",
            params={"invocation_id": "inv-4", "callback_token": "tok-4"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["mentions"]) == 1
        assert data["mentions"][0]["from_agent"] == "designer"
        mock_router.get_pending_mentions.assert_awaited_once_with(
            invocation_id="inv-4", callback_token="tok-4"
        )
