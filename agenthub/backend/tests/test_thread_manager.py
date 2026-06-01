"""ThreadManager 测试"""
import pytest

from agenthub.backend.models.thread import ThreadStatus
from agenthub.backend.services.thread_manager import ThreadManager


@pytest.fixture
def manager():
    return ThreadManager()


@pytest.mark.asyncio
async def test_create_thread(manager):
    thread = await manager.create_thread("测试线程", created_by="user")
    assert thread.title == "测试线程"
    assert thread.status == "active"
    assert await manager.get_thread(thread.id) is not None


@pytest.mark.asyncio
async def test_get_thread(manager):
    thread = await manager.create_thread("测试线程")
    result = await manager.get_thread(thread.id)
    assert result is not None
    assert result.id == thread.id


@pytest.mark.asyncio
async def test_get_nonexistent_thread(manager):
    result = await manager.get_thread("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_list_threads(manager):
    await manager.create_thread("线程1")
    await manager.create_thread("线程2")
    await manager.create_thread("线程3")
    threads = await manager.list_threads()
    assert len(threads) == 3


@pytest.mark.asyncio
async def test_list_threads_with_archived(manager):
    thread1 = await manager.create_thread("活跃线程")
    thread2 = await manager.create_thread("归档线程")
    await manager.archive_thread(thread2.id)
    active_threads = await manager.list_threads(status=ThreadStatus.ACTIVE)
    assert len(active_threads) == 1
    assert active_threads[0].id == thread1.id


@pytest.mark.asyncio
async def test_archive_thread(manager):
    thread = await manager.create_thread("测试线程")
    result = await manager.archive_thread(thread.id)
    assert result is True
    archived = await manager.get_thread(thread.id)
    assert archived.status == "archived"


@pytest.mark.asyncio
async def test_archive_nonexistent_thread(manager):
    result = await manager.archive_thread("nonexistent")
    assert result is False


@pytest.mark.asyncio
async def test_add_message(manager):
    thread = await manager.create_thread("测试线程")
    msg = await manager.add_message(
        thread_id=thread.id,
        sender_id="user",
        content="测试消息"
    )
    assert msg is not None
    assert msg.content == "测试消息"
    assert msg.thread_id == thread.id


@pytest.mark.asyncio
async def test_add_message_to_nonexistent_thread(manager):
    msg = await manager.add_message(
        thread_id="nonexistent",
        sender_id="user",
        content="测试消息"
    )
    assert msg is None


@pytest.mark.asyncio
async def test_add_message_with_mentions(manager):
    thread = await manager.create_thread("测试线程")
    msg = await manager.add_message(
        thread_id=thread.id,
        sender_id="user",
        content="@architect 这个方案可行吗？",
        mentions=["architect"]
    )
    assert msg.mentions == ["architect"]
    updated_thread = await manager.get_thread(thread.id)
    assert "architect" in updated_thread.participants


@pytest.mark.asyncio
async def test_get_messages(manager):
    thread = await manager.create_thread("测试线程")
    await manager.add_message(thread.id, "user", "消息1")
    await manager.add_message(thread.id, "pm", "消息2")
    await manager.add_message(thread.id, "user", "消息3")
    messages = await manager.get_messages(thread.id)
    assert len(messages) == 3
    assert messages[0].content == "消息1"
    assert messages[2].content == "消息3"


@pytest.mark.asyncio
async def test_get_messages_with_limit(manager):
    thread = await manager.create_thread("测试线程")
    for i in range(10):
        await manager.add_message(thread.id, "user", f"消息{i}")
    messages = await manager.get_messages(thread.id, limit=5)
    assert len(messages) == 5
    assert messages[0].content == "消息5"


@pytest.mark.asyncio
async def test_get_thread_context(manager):
    thread = await manager.create_thread("测试线程")
    await manager.add_message(thread.id, "user", "用 JWT 还是 session？")
    await manager.add_message(thread.id, "architect", "建议用 JWT")
    context = await manager.get_thread_context(thread.id)
    assert "用户: 用 JWT 还是 session？" in context
    assert "architect: 建议用 JWT" in context


@pytest.mark.asyncio
async def test_get_thread_context_empty(manager):
    thread = await manager.create_thread("测试线程")
    context = await manager.get_thread_context(thread.id)
    assert context == ""
