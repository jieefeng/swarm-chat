"""messages 路由与 SQLite 存储的接口契约回归测试

背景：`_persist_message` 按 memory 接口调用 `memory.add_message(..., user_id=...)`，
但 STORAGE_BACKEND=sqlite（默认）时 memory 实际是 SQLiteManager。
两者签名/返回值不一致曾导致 POST /api/messages 必然 500。
此前的测试全部 mock 掉 memory，无法发现该问题 —— 因此这里使用真实
SQLiteManager 直接验证接口契约。
"""
import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
)

os.environ["STORAGE_BACKEND"] = "sqlite"


@pytest.fixture
async def real_db():
    """真实的模块级 sqlite_manager 单例（_persist_message 会与它做 identity 比较）"""
    from agenthub.backend.services.database import get_db

    db = await get_db()
    yield db


@pytest.fixture
async def sqlite_db(tmp_path):
    """独立的临时 SQLiteManager 实例"""
    from agenthub.backend.services.sqlite_manager import SQLiteManager

    db = SQLiteManager(str(tmp_path / "contract.db"))
    await db.init_db()
    yield db
    await db.close()


class TestPersistMessageContract:
    """_persist_message 在 sqlite 后端下的契约（使用真实 sqlite_manager 单例）"""

    async def test_add_message_accepts_user_id(self, sqlite_db):
        """SQLiteManager.add_message 必须接受 user_id（memory 接口兼容）"""
        thread_id = await sqlite_db.create_thread(title="t", user_id="default")
        result = await sqlite_db.add_message(
            role="user",
            content="hello",
            agent_id="user",
            sender_name="用户",
            user_id="default",
            thread_id=thread_id,
        )
        # SQLiteManager 返回 msg_id 字符串
        assert isinstance(result, str)
        assert result.startswith("msg_")

    async def test_persist_message_returns_dict_from_sqlite(self, real_db):
        """_persist_message 在 sqlite 后端下必须返回消息 dict（而非裸 msg_id）"""
        from agenthub.backend.routers import messages as messages_module

        thread_id = await real_db.create_thread(title="t", user_id="default")

        msg = await messages_module._persist_message(
            role="user",
            content="契约测试",
            agent_id="user",
            sender_name="用户",
            user_id="default",
            thread_id=thread_id,
        )

        assert isinstance(msg, dict), "必须返回 dict 供 SSE 广播使用"
        assert msg["id"].startswith("msg_")
        assert msg["content"] == "契约测试"
        assert msg["role"] == "user"
        assert msg["thread_id"] == thread_id
        assert msg["type"] == "user"

    async def test_persist_message_agent_role_type(self, real_db):
        """agent 角色的消息 type 必须是 agent"""
        from agenthub.backend.routers import messages as messages_module

        thread_id = await real_db.create_thread(title="t", user_id="default")

        msg = await messages_module._persist_message(
            role="designer",
            content="回复内容",
            agent_id="designer",
            sender_name="苍龙",
            user_id="default",
            thread_id=thread_id,
        )

        assert isinstance(msg, dict)
        assert msg["type"] == "agent"
        assert msg["sender_name"] == "苍龙"


class TestSqliteMemoryInterfaceParity:
    """SQLiteManager 需提供 messages 路由/ a2a_router 依赖的全部方法"""

    def test_has_get_context_for_agent(self):
        from agenthub.backend.services.sqlite_manager import SQLiteManager

        assert hasattr(SQLiteManager, "get_context_for_agent")

    async def test_get_context_for_agent_returns_text(self, sqlite_db):
        """get_context_for_agent 返回 [role]: content 形式文本"""
        thread_id = await sqlite_db.create_thread(title="t", user_id="default")
        await sqlite_db.add_message(thread_id=thread_id, role="user", content="你好")
        await sqlite_db.add_message(
            thread_id=thread_id, role="designer", content="你好，我是苍龙"
        )

        context = await sqlite_db.get_context_for_agent(
            "designer", user_id="default", thread_id=thread_id
        )

        assert "[user]: 你好" in context
        assert "[designer]: 你好，我是苍龙" in context

    async def test_get_messages_accepts_user_id(self, sqlite_db):
        """get_messages 必须接受 user_id（memory 接口兼容）"""
        thread_id = await sqlite_db.create_thread(title="t", user_id="default")
        await sqlite_db.add_message(thread_id=thread_id, role="user", content="hi")

        msgs = await sqlite_db.get_messages(
            user_id="default", thread_id=thread_id, limit=10
        )
        assert len(msgs) == 1
