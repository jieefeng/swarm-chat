"""会话 (Thread) API 端点测试"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# 强制使用 sqlite 存储后端，确保线程管理可用
os.environ["STORAGE_BACKEND"] = "sqlite"

from agenthub.backend.main import app

client = TestClient(app)
API_KEY = "dev-secret-key"
HEADERS = {"X-API-Key": API_KEY}


class TestThreadsAPI:
    """会话 API 测试类"""

    def _create_thread(self, title: str = "测试会话") -> dict:
        """辅助方法：创建会话并返回响应数据"""
        response = client.post(
            "/api/threads",
            headers=HEADERS,
            json={"title": title},
        )
        assert response.status_code == 201
        return response.json()

    def test_create_thread_default_title(self):
        """POST /api/threads 无标题时使用默认标题"""
        response = client.post("/api/threads", headers=HEADERS, json={})
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["id"].startswith("thread_")
        assert data["title"] == "新会话"
        assert "created_at" in data
        assert "updated_at" in data
        assert data["is_pinned"] is False
        assert data["is_archived"] is False

    def test_create_thread_with_title(self):
        """POST /api/threads 指定标题"""
        response = client.post(
            "/api/threads",
            headers=HEADERS,
            json={"title": "我的第一次对话"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "我的第一次对话"

    def test_get_threads_empty(self):
        """GET /api/threads 返回会话列表（可能为空）"""
        response = client.get("/api/threads", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "threads" in data
        assert isinstance(data["threads"], list)

    def test_get_threads_with_data(self):
        """GET /api/threads 返回包含 message_count 的会话列表"""
        # 创建一个会话
        thread = self._create_thread("会话列表测试")

        response = client.get("/api/threads", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "threads" in data

        # 找到刚创建的会话
        found = [t for t in data["threads"] if t["id"] == thread["id"]]
        assert len(found) == 1
        t = found[0]
        assert t["title"] == "会话列表测试"
        assert "message_count" in t
        assert t["message_count"] == 0

    def test_update_thread_title(self):
        """PATCH /api/threads/{id} 更新标题"""
        thread = self._create_thread("原始标题")

        response = client.patch(
            f"/api/threads/{thread['id']}",
            headers=HEADERS,
            json={"title": "新标题"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "新标题"

    def test_update_thread_pin(self):
        """PATCH /api/threads/{id} 置顶会话"""
        thread = self._create_thread("置顶测试")

        response = client.patch(
            f"/api/threads/{thread['id']}",
            headers=HEADERS,
            json={"is_pinned": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_pinned"] is True

    def test_update_thread_not_found(self):
        """PATCH /api/threads/{id} 会话不存在返回 405"""
        response = client.patch(
            "/api/threads/thread_nonexistent",
            headers=HEADERS,
            json={"title": "不存在"},
        )
        assert response.status_code == 405

    def test_delete_thread(self):
        """DELETE /api/threads/{id} 删除会话"""
        thread = self._create_thread("待删除")

        response = client.delete(
            f"/api/threads/{thread['id']}",
            headers=HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 删除后再次获取应返回 405
        response = client.patch(
            f"/api/threads/{thread['id']}",
            headers=HEADERS,
            json={"title": "已删除"},
        )
        assert response.status_code == 405

    def test_delete_thread_not_found(self):
        """DELETE /api/threads/{id} 会话不存在返回 405"""
        response = client.delete(
            "/api/threads/thread_nonexistent",
            headers=HEADERS,
        )
        assert response.status_code == 405

    def test_get_thread_messages_empty(self):
        """GET /api/threads/{id}/messages 空会话返回空列表"""
        thread = self._create_thread("空会话")

        response = client.get(
            f"/api/threads/{thread['id']}/messages",
            headers=HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert data["messages"] == []

    def test_get_thread_messages_not_found(self):
        """GET /api/threads/{id}/messages 会话不存在返回 405"""
        response = client.get(
            "/api/threads/thread_nonexistent/messages",
            headers=HEADERS,
        )
        assert response.status_code == 405

    def test_delete_thread_cascades_messages(self):
        """DELETE /api/threads/{id} 级联删除消息"""
        import asyncio
        from agenthub.backend.routers.threads import sqlite_manager

        thread = self._create_thread("级联删除测试")

        # 直接通过 SQLiteManager 添加消息（避免触发 LLM 调用）
        async def _add_test_message():
            await sqlite_manager.init_db()
            await sqlite_manager.add_message(
                thread_id=thread["id"],
                role="user",
                content="测试消息",
                agent_id="user",
                sender_name="用户",
            )
        asyncio.run(_add_test_message())

        # 确认消息存在
        response = client.get(
            f"/api/threads/{thread['id']}/messages",
            headers=HEADERS,
        )
        assert response.status_code == 200
        assert len(response.json()["messages"]) > 0

        # 删除会话
        response = client.delete(
            f"/api/threads/{thread['id']}",
            headers=HEADERS,
        )
        assert response.status_code == 200

        # 消息也应被删除（会话已不存在，返回 405）
        response = client.get(
            f"/api/threads/{thread['id']}/messages",
            headers=HEADERS,
        )
        assert response.status_code == 405

    def test_delete_all_threads_except_keep(self):
        """DELETE /api/threads?keep=<id> 删除除指定会话外的所有会话"""
        t1 = self._create_thread("保留")
        t2 = self._create_thread("待删 1")
        t3 = self._create_thread("待删 2")

        response = client.delete(
            f"/api/threads?keep={t1['id']}",
            headers=HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["deleted_count"] == 2

        # 验证只剩 t1
        response = client.get("/api/threads", headers=HEADERS)
        assert response.status_code == 200
        ids = [t["id"] for t in response.json()["threads"]]
        assert t1["id"] in ids
        assert t2["id"] not in ids
        assert t3["id"] not in ids

    def test_delete_all_threads_keep_missing_returns_404(self):
        """DELETE /api/threads?keep=<不存在> 返回 404"""
        response = client.delete(
            "/api/threads?keep=thread_nonexistent",
            headers=HEADERS,
        )
        assert response.status_code == 404

    def test_delete_all_threads_cascades_messages(self):
        """DELETE /api/threads 级联删除被删会话的消息"""
        import asyncio
        from agenthub.backend.routers.threads import sqlite_manager

        keep_thread = self._create_thread("保留会话")
        doomed_thread = self._create_thread("待删会话")

        async def _add_test_message():
            await sqlite_manager.init_db()
            await sqlite_manager.add_message(
                thread_id=doomed_thread["id"],
                role="user",
                content="待删消息",
                agent_id="user",
                sender_name="用户",
            )
        asyncio.run(_add_test_message())

        # 确认消息存在
        async def _verify_message_exists():
            return await sqlite_manager.get_messages(doomed_thread["id"])
        msgs_before = asyncio.run(_verify_message_exists())
        assert len(msgs_before) == 1

        # 调用 bulk delete
        response = client.delete(
            f"/api/threads?keep={keep_thread['id']}",
            headers=HEADERS,
        )
        assert response.status_code == 200

        # 验证被删会话的消息已被级联清空
        async def _verify_message_cascaded():
            return await sqlite_manager.get_messages(doomed_thread["id"])
        msgs_after = asyncio.run(_verify_message_cascaded())
        assert msgs_after == []
