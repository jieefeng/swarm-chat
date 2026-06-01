"""Thread 模型测试"""
import pytest
from datetime import timezone

from agenthub.backend.models.thread import Thread, ThreadMessage, ThreadStatus


def test_thread_default_values():
    """测试 Thread 默认值"""
    thread = Thread(title="测试线程")
    assert thread.title == "测试线程"
    assert thread.status == ThreadStatus.ACTIVE
    assert thread.participants == []
    assert thread.created_by == "user"
    assert thread.id is not None
    assert len(thread.id) == 36  # full UUID format


def test_thread_default_times_are_utc():
    """测试默认时间为 UTC"""
    thread = Thread(title="测试线程")
    assert thread.created_at.tzinfo == timezone.utc
    assert thread.updated_at.tzinfo == timezone.utc


def test_thread_status_enum():
    """测试 ThreadStatus 枚举值"""
    assert ThreadStatus.ACTIVE == "active"
    assert ThreadStatus.ARCHIVED == "archived"


def test_thread_message_default_values():
    """测试 ThreadMessage 默认值"""
    msg = ThreadMessage(
        thread_id="thread_001",
        sender_id="user",
        content="测试消息"
    )
    assert msg.thread_id == "thread_001"
    assert msg.sender_id == "user"
    assert msg.mentions == []
    assert msg.reply_to is None
    assert msg.id is not None
    assert len(msg.id) == 36  # full UUID format
    assert msg.created_at.tzinfo == timezone.utc


def test_thread_message_with_mentions():
    """测试带 mentions 的消息"""
    msg = ThreadMessage(
        thread_id="thread_001",
        sender_id="user",
        content="@architect 这个方案可行吗？",
        mentions=["architect"]
    )
    assert msg.mentions == ["architect"]
