"""Tests for SQLiteManager chat persistence."""

import pytest
import pytest_asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.sqlite_manager import SQLiteManager


@pytest_asyncio.fixture
async def db():
    """Create in-memory database for testing."""
    manager = SQLiteManager(":memory:")
    await manager.init_db()
    yield manager
    await manager.close()


@pytest.mark.asyncio
async def test_create_thread(db):
    """Thread creation returns valid ID and stores title/user_id."""
    thread_id = await db.create_thread(title="Test Chat", user_id="user123")

    assert thread_id.startswith("thread_")
    assert len(thread_id) == 15  # thread_ + 8 chars

    thread = await db.get_thread(thread_id)
    assert thread is not None
    assert thread["title"] == "Test Chat"
    assert thread["user_id"] == "user123"
    assert thread["is_pinned"] == 0
    assert thread["is_archived"] == 0


@pytest.mark.asyncio
async def test_get_threads(db):
    """Threads returned in descending updated_at order."""
    id1 = await db.create_thread(title="First", user_id="user1")
    id2 = await db.create_thread(title="Second", user_id="user1")
    id3 = await db.create_thread(title="Third", user_id="user1")

    threads = await db.get_threads(user_id="user1")
    assert len(threads) == 3
    # Most recent first
    assert threads[0]["id"] == id3
    assert threads[1]["id"] == id2
    assert threads[2]["id"] == id1


@pytest.mark.asyncio
async def test_get_threads_with_limit(db):
    """Limit parameter restricts number of threads returned."""
    for i in range(5):
        await db.create_thread(title=f"Thread {i}", user_id="user1")

    threads = await db.get_threads(user_id="user1", limit=3)
    assert len(threads) == 3


@pytest.mark.asyncio
async def test_get_threads_user_isolation(db):
    """Users only see their own threads."""
    await db.create_thread(title="User1 Thread", user_id="user1")
    await db.create_thread(title="User2 Thread", user_id="user2")

    threads = await db.get_threads(user_id="user1")
    assert len(threads) == 1
    assert threads[0]["title"] == "User1 Thread"


@pytest.mark.asyncio
async def test_add_message(db):
    """Message stores all fields correctly."""
    thread_id = await db.create_thread(title="Test", user_id="user1")
    msg_id = await db.add_message(
        thread_id=thread_id,
        role="assistant",
        content="Hello!",
        agent_id="pm",
        sender_name="PM Agent",
    )

    assert msg_id.startswith("msg_")
    assert len(msg_id) == 12  # msg_ + 8 chars

    messages = await db.get_messages(thread_id)
    assert len(messages) == 1
    msg = messages[0]
    assert msg["role"] == "assistant"
    assert msg["content"] == "Hello!"
    assert msg["agent_id"] == "pm"
    assert msg["sender_name"] == "PM Agent"


@pytest.mark.asyncio
async def test_get_messages_order(db):
    """Messages returned in chronological order (oldest first)."""
    thread_id = await db.create_thread(title="Test", user_id="user1")

    msg1 = await db.add_message(thread_id, "user", "First message")
    msg2 = await db.add_message(thread_id, "assistant", "Second message")
    msg3 = await db.add_message(thread_id, "user", "Third message")

    messages = await db.get_messages(thread_id)
    assert len(messages) == 3
    assert messages[0]["content"] == "First message"
    assert messages[1]["content"] == "Second message"
    assert messages[2]["content"] == "Third message"


@pytest.mark.asyncio
async def test_get_messages_with_limit(db):
    """Limit returns only the most recent N messages."""
    thread_id = await db.create_thread(title="Test", user_id="user1")

    for i in range(5):
        await db.add_message(thread_id, "user", f"Message {i}")

    messages = await db.get_messages(thread_id, limit=2)
    assert len(messages) == 2
    assert messages[0]["content"] == "Message 3"
    assert messages[1]["content"] == "Message 4"


@pytest.mark.asyncio
async def test_delete_thread_cascades_messages(db):
    """Deleting thread also deletes all its messages."""
    thread_id = await db.create_thread(title="To Delete", user_id="user1")
    await db.add_message(thread_id, "user", "Msg 1")
    await db.add_message(thread_id, "assistant", "Msg 2")

    assert await db.get_message_count(thread_id) == 2

    result = await db.delete_thread(thread_id)
    assert result is True

    thread = await db.get_thread(thread_id)
    assert thread is None

    messages = await db.get_messages(thread_id)
    assert len(messages) == 0


@pytest.mark.asyncio
async def test_delete_nonexistent_thread(db):
    """Deleting non-existent thread returns False."""
    result = await db.delete_thread("thread_nonexist")
    assert result is False


@pytest.mark.asyncio
async def test_update_thread_title(db):
    """Thread title can be updated."""
    thread_id = await db.create_thread(title="Old Title", user_id="user1")

    result = await db.update_thread(thread_id, title="New Title")
    assert result is True

    thread = await db.get_thread(thread_id)
    assert thread["title"] == "New Title"


@pytest.mark.asyncio
async def test_update_thread_pins(db):
    """Thread pin/archive status can be toggled."""
    thread_id = await db.create_thread(title="Test", user_id="user1")

    await db.update_thread(thread_id, is_pinned=1)
    thread = await db.get_thread(thread_id)
    assert thread["is_pinned"] == 1

    await db.update_thread(thread_id, is_archived=1)
    thread = await db.get_thread(thread_id)
    assert thread["is_archived"] == 1


@pytest.mark.asyncio
async def test_update_thread_sets_updated_at(db):
    """Updating thread refreshes updated_at timestamp."""
    thread_id = await db.create_thread(title="Test", user_id="user1")
    thread_before = await db.get_thread(thread_id)
    original_updated = thread_before["updated_at"]

    # Small delay to ensure timestamp difference
    import asyncio
    await asyncio.sleep(0.01)

    await db.update_thread(thread_id, title="Updated")
    thread_after = await db.get_thread(thread_id)
    assert thread_after["updated_at"] >= original_updated


@pytest.mark.asyncio
async def test_update_nonexistent_thread(db):
    """Updating non-existent thread returns False."""
    result = await db.update_thread("thread_nonexist", title="X")
    assert result is False


@pytest.mark.asyncio
async def test_message_count(db):
    """get_message_count returns correct count."""
    thread_id = await db.create_thread(title="Test", user_id="user1")

    assert await db.get_message_count(thread_id) == 0

    await db.add_message(thread_id, "user", "Hello")
    assert await db.get_message_count(thread_id) == 1

    await db.add_message(thread_id, "assistant", "Hi")
    assert await db.get_message_count(thread_id) == 2


@pytest.mark.asyncio
async def test_default_optional_fields(db):
    """Messages with minimal fields use sensible defaults."""
    thread_id = await db.create_thread(title="Test", user_id="user1")
    await db.add_message(thread_id, "user", "Plain message")

    messages = await db.get_messages(thread_id)
    msg = messages[0]
    assert msg["agent_id"] is None
    assert msg["sender_name"] is None


@pytest.mark.asyncio
async def test_thread_not_found(db):
    """get_thread returns None for non-existent ID."""
    result = await db.get_thread("thread_nonexist")
    assert result is None


@pytest.mark.asyncio
async def test_delete_all_except_keeps_specified_thread(db):
    """delete_all_except 删除除指定会话外的所有会话"""
    id1 = await db.create_thread(title="Keep", user_id="user1")
    id2 = await db.create_thread(title="Delete 1", user_id="user1")
    id3 = await db.create_thread(title="Delete 2", user_id="user1")

    deleted_count = await db.delete_all_except(id1)

    assert deleted_count == 2
    assert await db.get_thread(id1) is not None
    assert await db.get_thread(id2) is None
    assert await db.get_thread(id3) is None


@pytest.mark.asyncio
async def test_delete_all_except_returns_zero_when_only_keep_exists(db):
    """只有一个会话时 delete_all_except 返回 0"""
    id1 = await db.create_thread(title="Only", user_id="user1")

    deleted_count = await db.delete_all_except(id1)

    assert deleted_count == 0
    assert await db.get_thread(id1) is not None


@pytest.mark.asyncio
async def test_delete_all_except_cascades_messages(db):
    """delete_all_except 级联删除被删会话的消息"""
    keep_id = await db.create_thread(title="Keep", user_id="user1")
    del_id = await db.create_thread(title="Delete", user_id="user1")
    await db.add_message(thread_id=del_id, role="user", content="bye")

    # 确认消息存在
    msgs_before = await db.get_messages(del_id)
    assert len(msgs_before) == 1

    await db.delete_all_except(keep_id)

    # 消息应被级联删除
    msgs_after = await db.get_messages(del_id)
    assert msgs_after == []
    assert await db.get_thread(keep_id) is not None
