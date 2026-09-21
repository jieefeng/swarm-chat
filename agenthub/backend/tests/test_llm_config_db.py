"""LLM 配置数据库模块测试（异步版，匹配连接注入式 LLMConfigDB）"""
import pytest
import aiosqlite
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm_config_db import LLMConfigDB


@pytest.fixture
def db_path(tmp_path):
    """临时数据库文件路径"""
    return str(tmp_path / "test.db")


class TestLLMConfigDB:
    """LLMConfigDB 测试类"""

    async def test_init_creates_table(self, db_path):
        """初始化时创建表"""
        async with aiosqlite.connect(db_path) as conn:
            db = LLMConfigDB(conn)
            await db.ensure_schema()
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='agent_llm_config'"
            )
            assert await cursor.fetchone() is not None

    async def test_init_seeds_default_data(self, db_path):
        """表为空时插入默认配置"""
        async with aiosqlite.connect(db_path) as conn:
            db = LLMConfigDB(conn)
            await db.ensure_schema()
            config = await db.get_all_config()
            assert "designer" in config
            assert "developer" in config
            assert config["designer"]["llm_provider"] == "bailian"

    async def test_get_provider_returns_default(self, db_path):
        """获取存在的 agent provider"""
        async with aiosqlite.connect(db_path) as conn:
            db = LLMConfigDB(conn)
            await db.ensure_schema()
            assert await db.get_provider("designer") == "bailian"

    async def test_get_provider_returns_none_for_unknown(self, db_path):
        """获取不存在的 agent 返回 None"""
        async with aiosqlite.connect(db_path) as conn:
            db = LLMConfigDB(conn)
            await db.ensure_schema()
            assert await db.get_provider("unknown") is None

    async def test_update_provider(self, db_path):
        """更新 provider"""
        async with aiosqlite.connect(db_path) as conn:
            db = LLMConfigDB(conn)
            await db.ensure_schema()
            await db.update_provider("designer", "minimax")
            assert await db.get_provider("designer") == "minimax"

    async def test_get_all_config(self, db_path):
        """获取所有配置"""
        async with aiosqlite.connect(db_path) as conn:
            db = LLMConfigDB(conn)
            await db.ensure_schema()
            config = await db.get_all_config()
            assert isinstance(config, dict)
            assert len(config) >= 2  # designer, developer
