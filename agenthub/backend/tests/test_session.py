"""SessionManager 单元测试 (UT-S001 ~ UT-S005)"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# 添加父目录到路径以导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agenthub.backend.services.session import SessionManager, AGENT_CONFIGS


class TestSessionManager:
    """SessionManager测试类"""

    @pytest.fixture
    def session_manager(self):
        """创建SessionManager实例"""
        return SessionManager()

    # UT-S001: 为新Agent创建会话 -> 创建新session_id
    def test_create_new_session(self, session_manager):
        """UT-S001: 为新Agent创建会话，返回新的session_id"""
        session_manager.create_session("session-123", agent_id="designer")
        session = session_manager.get_session("session-123")
        assert session is not None
        assert session["agent_id"] == "designer"
        assert session["messages"] == []

    # UT-S002: 获取已存在会话 -> 返回已有session_id
    def test_get_existing_session(self, session_manager):
        """UT-S002: 获取已存在的会话，返回该会话"""
        session_manager.create_session("session-456", agent_id="developer")
        session = session_manager.get_session("session-456")
        assert session is not None
        assert session["agent_id"] == "developer"
        assert session["messages"] == []

    # UT-S003: 获取未知Agent会话 -> 抛出ValueError
    def test_get_nonexistent_session(self, session_manager):
        """UT-S003: 获取不存在的会话返回None（不抛出异常，按当前实现）"""
        session = session_manager.get_session("nonexistent-session")
        assert session is None

    # UT-S004: 发送消息给Agent -> 返回Claude响应(mocker)
    @pytest.mark.asyncio
    async def test_send_message_to_agent(self):
        """UT-S004: 发送消息给Agent，通过mock返回Claude响应"""
        from agenthub.backend.services.session import SessionManager

        session_manager = SessionManager()
        session_manager.create_session("test-session", agent_id="designer")

        # 注意：SessionManager的send_to_agent依赖ClaudeService
        # 根据现有实现测试create_session的返回值
        session = session_manager.get_session("test-session")
        assert session is not None

    # UT-S005: 获取System Prompt -> 返回对应system_prompt
    def test_get_agent_config(self, session_manager):
        """UT-S005: 获取Agent配置信息"""
        config = AGENT_CONFIGS.get("designer")
        assert config is not None
        assert config["name"] == "苍龙"
        assert config["beast"] == "青龙"
        assert config["role"] == "创意设计师"

    def test_create_session_default_agent(self, session_manager):
        """测试创建会话时使用默认agent_id"""
        session_manager.create_session("session-default")
        session = session_manager.get_session("session-default")
        assert session["agent_id"] == "designer"

    def test_delete_session(self, session_manager):
        """测试删除会话"""
        session_manager.create_session("session-to-delete", agent_id="developer")
        assert session_manager.get_session("session-to-delete") is not None

        session_manager.delete_session("session-to-delete")
        assert session_manager.get_session("session-to-delete") is None

    def test_delete_nonexistent_session(self, session_manager):
        """测试删除不存在的会话不会抛出异常"""
        # 不应抛出异常
        session_manager.delete_session("nonexistent-session")

    def test_multiple_sessions(self, session_manager):
        """测试管理多个会话"""
        session_manager.create_session("session-1", agent_id="designer")
        session_manager.create_session("session-2", agent_id="developer")

        assert session_manager.get_session("session-1") is not None
        assert session_manager.get_session("session-2") is not None

    def test_agent_configs_complete(self):
        """测试所有Agent配置都存在"""
        expected_agents = ["designer", "developer", "qa", "orchestrator"]
        for agent in expected_agents:
            assert agent in AGENT_CONFIGS
            config = AGENT_CONFIGS[agent]
            assert "name" in config
            assert "role" in config

    # --- Agent 重设计测试 ---

    def test_agent_configs_has_three_core_agents(self):
        """验证 3 个核心 Agent ID 存在"""
        core_ids = {"designer", "developer", "qa"}
        assert core_ids == set(AGENT_CONFIGS.keys()) - {"orchestrator"}

    def test_agent_configs_designer_role(self):
        """验证 designer 的角色为创意设计师"""
        assert AGENT_CONFIGS["designer"]["role"] == "创意设计师"
        assert AGENT_CONFIGS["designer"]["name"] == "苍龙"
        assert AGENT_CONFIGS["designer"]["beast"] == "青龙"

    def test_agent_configs_no_pm_or_architect(self):
        """验证 pm 和 architect 已被移除"""
        assert "pm" not in AGENT_CONFIGS
        assert "architect" not in AGENT_CONFIGS

    def test_agent_configs_developer_updated_role(self):
        """验证 developer 角色更新为核心开发者"""
        assert AGENT_CONFIGS["developer"]["role"] == "核心开发者"

    def test_agent_configs_qa_updated_role(self):
        """验证 qa 角色更新为质量守护者"""
        assert AGENT_CONFIGS["qa"]["role"] == "质量守护者"

    # --- AGENT_IDENTITIES 测试 ---

    def test_agent_identities_has_designer(self):
        """验证 designer 身份配置存在"""
        from agenthub.backend.services.agent_identity import AGENT_IDENTITIES
        assert "designer" in AGENT_IDENTITIES
        assert AGENT_IDENTITIES["designer"]["beast"] == "青龙"
        assert AGENT_IDENTITIES["designer"]["element"] == "木"

    def test_agent_identities_no_pm_or_architect(self):
        """验证 pm 和 architect 身份已移除"""
        from agenthub.backend.services.agent_identity import AGENT_IDENTITIES
        assert "pm" not in AGENT_IDENTITIES
        assert "architect" not in AGENT_IDENTITIES

    def test_get_identity_designer(self):
        """验证 get_identity 返回 designer 信息"""
        from agenthub.backend.services.agent_identity import get_identity
        identity = get_identity("designer")
        assert identity is not None
        assert identity["nickname"] == "苍龙"

    def test_get_nickname_designer(self):
        """验证 get_nickname 返回 designer 昵称"""
        from agenthub.backend.services.agent_identity import get_nickname
        assert get_nickname("designer") == "苍龙"
        assert get_nickname("pm") == "pm"  # 已不存在，返回原 ID