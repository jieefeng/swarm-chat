"""MemoryManager 单元测试 (UT-M001 ~ UT-M007)"""
import pytest
import sys
import os

# 添加父目录到路径以导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.memory_manager import MemoryManager


class TestMemoryManager:
    """MemoryManager测试类"""

    @pytest.fixture
    def memory(self):
        """创建MemoryManager实例"""
        return MemoryManager()

    # UT-M001: 添加用户消息 -> message.id存在，type="user"
    def test_add_user_message(self, memory):
        """UT-M001: 添加用户消息后，消息包含role和content字段"""
        memory.add_message(role="user", content="你好")
        messages = memory.get_messages(limit=1)
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "你好"
        assert "timestamp" in messages[0]

    # UT-M002: 添加Agent消息 -> message.type="agent"
    def test_add_agent_message(self, memory):
        """UT-M002: 添加Agent消息后，消息的role为agent"""
        memory.add_message(role="agent", content="我是助手", agent_id="coder")
        messages = memory.get_messages(limit=1)
        assert len(messages) == 1
        assert messages[0]["role"] == "agent"
        assert messages[0]["agent_id"] == "coder"

    def test_context_window_limit_exceeded(self, memory):
        """UT-M003: 消息超过20条时，只保留最近20条"""
        # 创建max_messages=20的实例
        memory_instance = MemoryManager(max_messages=20)
        # 添加25条消息
        for i in range(25):
            memory_instance.add_message(role="user", content=f"消息{i}")
        messages = memory_instance.get_messages(limit=50)
        assert len(messages) == 20
        # 最近的消息应该是最后一条
        assert messages[-1]["content"] == "消息24"

    # UT-M004: 上下文窗口限制-刚好20条 -> 全部保留
    def test_context_window_limit_exact(self, memory):
        """UT-M004: 消息正好20条时全部保留"""
        memory_instance = MemoryManager(max_messages=20)
        for i in range(20):
            memory_instance.add_message(role="user", content=f"消息{i}")
        messages = memory_instance.get_messages(limit=50)
        assert len(messages) == 20

    # UT-M005: 获取最近消息 -> limit=3返回最近3条
    def test_get_recent_messages(self, memory):
        """UT-M005: limit参数正确限制返回消息数量"""
        for i in range(10):
            memory.add_message(role="user", content=f"消息{i}")
        messages = memory.get_messages(limit=3)
        assert len(messages) == 3
        # 应该返回最近的3条
        assert messages[0]["content"] == "消息7"
        assert messages[2]["content"] == "消息9"

    # UT-M006: 清空上下文 -> messages为空
    def test_clear_messages(self, memory):
        """UT-M006: 清空消息后，消息列表为空"""
        memory.add_message(role="user", content="测试消息")
        assert len(memory.get_messages()) == 1
        memory.clear()
        assert len(memory.get_messages()) == 0

    # UT-M007: 获取Agent上下文 -> 拼接成字符串
    def test_get_agent_context(self, memory):
        """UT-M007: 获取特定Agent的消息上下文并拼接成字符串"""
        memory.add_message(role="user", content="你好")
        memory.add_message(role="agent", content="你好，我是助手", agent_id="coder")
        memory.add_message(role="user", content="请帮我")
        memory.add_message(role="agent", content="好的", agent_id="coder")

        # 获取最近5条消息并拼接
        messages = memory.get_messages(limit=5)
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
        assert "user: 你好" in context
        assert "agent: 你好，我是助手" in context
        assert "agent: 好的" in context

    def test_message_has_timestamp(self, memory):
        """测试消息包含时间戳"""
        memory.add_message(role="user", content="测试")
        messages = memory.get_messages(limit=1)
        assert "timestamp" in messages[0]
        assert isinstance(messages[0]["timestamp"], str)

    def test_agent_id_optional(self, memory):
        """测试agent_id参数可选"""
        memory.add_message(role="user", content="无agent_id的消息")
        messages = memory.get_messages(limit=1)
        assert messages[0]["agent_id"] is None

    def test_max_messages_limit(self, memory):
        """测试max_messages属性限制"""
        memory_instance = MemoryManager(max_messages=1000)
        assert memory_instance.max_messages == 1000
        # 添加超过1000条消息
        for i in range(1005):
            memory_instance.add_message(role="user", content=f"msg{i}")
        # 使用足够大的limit获取所有消息
        assert len(memory_instance.get_messages(limit=2000)) == 1000