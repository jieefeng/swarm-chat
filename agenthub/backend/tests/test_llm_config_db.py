"""LLM 配置数据库模块测试"""
import pytest
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm_config_db import LLMConfigDB


class TestLLMConfigDB:
    """LLMConfigDB 测试类"""

    @pytest.fixture
    def db(self, tmp_path):
        """创建临时数据库实例"""
        db_path = str(tmp_path / "test.db")
        return LLMConfigDB(db_path)

    def test_init_creates_table(self, db):
        """初始化时创建表"""
        conn = sqlite3.connect(db.db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='agent_llm_config'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_init_seeds_default_data(self, db):
        """表为空时插入默认配置"""
        config = db.get_all_config()
        assert "pm" in config
        assert "architect" in config
        assert config["pm"]["llm_provider"] == "bailian"

    def test_get_provider_returns_default(self, db):
        """获取存在的 agent provider"""
        assert db.get_provider("pm") == "bailian"

    def test_get_provider_returns_none_for_unknown(self, db):
        """获取不存在的 agent 返回 None"""
        assert db.get_provider("unknown") is None

    def test_update_provider(self, db):
        """更新 provider"""
        db.update_provider("pm", "anthropic")
        assert db.get_provider("pm") == "anthropic"

    def test_get_all_config(self, db):
        """获取所有配置"""
        config = db.get_all_config()
        assert isinstance(config, dict)
        assert len(config) >= 2  # pm, architect
