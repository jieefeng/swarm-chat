"""Thread 模型测试"""
import pytest
from agenthub.backend.models.thread import Thread, ThreadMessage


def test_thread_default_values():
    """测试 Thread 默认值"""
    thread = Thread(title="测试线程")
    assert thread.title == "测试线程"
    assert thread.status == "active"
    assert thread.participants == []
    assert thread.created_by == "user"
    assert thread.id is not None
    assert len(thread.id) == 12


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


def test_thread_message_with_mentions():
    """测试带 mentions 的消息"""
    msg = ThreadMessage(
        thread_id="thread_001",
        sender_id="user",
        content="@architect 这个方案可行吗？",
        mentions=["architect"]
    )
    assert msg.mentions == ["architect"]
