"""线程 API 集成测试"""
import pytest
from httpx import AsyncClient, ASGITransport
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from agenthub.backend.main import app

API_KEY = "dev-secret-key"
HEADERS = {"X-API-Key": API_KEY}


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_thread(client):
    """测试创建线程"""
    response = await client.post("/api/threads", json={
        "title": "测试线程",
        "description": "这是一个测试线程"
    }, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "测试线程"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_list_threads(client):
    """测试获取线程列表"""
    await client.post("/api/threads", json={"title": "线程1"}, headers=HEADERS)
    response = await client.get("/api/threads", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert len(data["threads"]) >= 1


@pytest.mark.asyncio
async def test_get_thread(client):
    """测试获取线程详情"""
    create_response = await client.post("/api/threads", json={"title": "测试线程"}, headers=HEADERS)
    thread_id = create_response.json()["id"]
    response = await client.get(f"/api/threads/{thread_id}", headers=HEADERS)
    assert response.status_code == 200
    assert response.json()["id"] == thread_id


@pytest.mark.asyncio
async def test_get_nonexistent_thread(client):
    """测试获取不存在的线程"""
    response = await client.get("/api/threads/nonexistent", headers=HEADERS)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_archive_thread(client):
    """测试归档线程"""
    create_response = await client.post("/api/threads", json={"title": "测试线程"}, headers=HEADERS)
    thread_id = create_response.json()["id"]
    response = await client.delete(f"/api/threads/{thread_id}", headers=HEADERS)
    assert response.status_code == 200
    get_response = await client.get(f"/api/threads/{thread_id}", headers=HEADERS)
    assert get_response.json()["status"] == "archived"


@pytest.mark.asyncio
async def test_send_message(client):
    """测试发送消息"""
    create_response = await client.post("/api/threads", json={"title": "测试线程"}, headers=HEADERS)
    thread_id = create_response.json()["id"]
    response = await client.post(f"/api/threads/{thread_id}/messages", json={
        "content": "@architect 这个方案可行吗？"
    }, headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "routed_to" in data
    assert "architect" in data["routed_to"]


@pytest.mark.asyncio
async def test_get_messages(client):
    """测试获取消息历史"""
    create_response = await client.post("/api/threads", json={"title": "测试线程"}, headers=HEADERS)
    thread_id = create_response.json()["id"]
    await client.post(f"/api/threads/{thread_id}/messages", json={
        "content": "测试消息"
    }, headers=HEADERS)
    response = await client.get(f"/api/threads/{thread_id}/messages", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) >= 1
