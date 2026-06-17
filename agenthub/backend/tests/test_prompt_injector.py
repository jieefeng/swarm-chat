"""PromptInjector 单元测试（验证已存在实现 + 3-agent 适配）"""
import os
import pytest
import sys

# 添加项目根目录到路径（backend/tests/ → 项目根）
sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
)

from agenthub.backend.services.prompt_injector import PromptInjector


class TestPromptInjector:
    @pytest.fixture
    def injector(self):
        return PromptInjector(api_url="http://test:7010")

    def test_inject_appends_instructions_after_original_prompt(self, injector):
        original = "你是设计师"
        result = injector.inject_into_system_prompt(
            original, "inv-1", "tok-1", "designer"
        )
        assert result.startswith(original)
        assert "## 团队协作工具" in result
        assert "inv-1" in result
        assert "tok-1" in result

    def test_curl_contains_post_message_url(self, injector):
        result = injector.inject_into_system_prompt(
            "p", "inv-2", "tok-2", "designer"
        )
        assert "http://test:7010/api/callbacks/post-message" in result
        assert "thread-context" in result
        assert "pending-mentions" in result

    def test_curl_payload_contains_credentials(self, injector):
        result = injector.inject_into_system_prompt(
            "p", "my-inv-id", "my-cb-token", "developer"
        )
        assert '"invocation_id": "my-inv-id"' in result
        assert '"callback_token": "my-cb-token"' in result
        assert '"target_agent_id"' in result

    def test_designer_workflow_triggers_mention_developer(self, injector):
        result = injector.inject_into_system_prompt(
            "p", "i", "t", "designer"
        )
        assert "@developer" in result
        # "完成设计方案" contains "设计", "@developer（开发者）" contains "开发者"
        assert "设计" in result and "开发者" in result

    def test_developer_workflow_triggers_mention_qa(self, injector):
        result = injector.inject_into_system_prompt(
            "p", "i", "t", "developer"
        )
        assert "@qa" in result
        assert "测试" in result or "qa" in result

    def test_qa_workflow_triggers_mention_developer(self, injector):
        result = injector.inject_into_system_prompt(
            "p", "i", "t", "qa"
        )
        assert "@developer" in result

    def test_unknown_agent_returns_only_common_triggers(self, injector):
        result = injector.inject_into_system_prompt(
            "p", "i", "t", "unknown_agent"
        )
        assert "完成任务后" in result
        assert "@developer" not in result
        assert "@qa" not in result

    def test_api_url_from_env_when_not_provided(self, monkeypatch):
        monkeypatch.setenv("API_URL", "http://from-env:9000")
        injector = PromptInjector()
        result = injector.inject_into_system_prompt("p", "i", "t", "designer")
        assert "http://from-env:9000" in result

    def test_api_url_default_when_no_env(self, monkeypatch):
        monkeypatch.delenv("API_URL", raising=False)
        injector = PromptInjector()
        result = injector.inject_into_system_prompt("p", "i", "t", "designer")
        assert "http://localhost:7010" in result

    def test_create_invocation_returns_pair(self, injector):
        inv_id, token = injector.create_invocation_for_agent(
            "designer", "thread-1"
        )
        assert isinstance(inv_id, str) and len(inv_id) == 36
        assert isinstance(token, str) and len(token) == 36
        assert inv_id != token

    def test_workflow_triggers_uses_simplified_chinese_names(self, injector):
        """3-agent 适配：designer/developer/qa 用中文别名"""
        designer = injector.inject_into_system_prompt("p", "i", "t", "designer")
        developer = injector.inject_into_system_prompt("p", "i", "t", "developer")
        qa = injector.inject_into_system_prompt("p", "i", "t", "qa")
        assert "开发者" in designer
        assert "测试" in developer
        assert "开发者" in qa
