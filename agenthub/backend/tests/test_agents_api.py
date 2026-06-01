"""Agent LLM 配置 API 测试"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agenthub.backend.main import app


client = TestClient(app)
API_KEY = "dev-secret-key"
HEADERS = {"X-API-Key": API_KEY}


class TestAgentsLLMConfigAPI:
    """Agent LLM 配置 API 测试类"""

    def test_get_all_llm_config(self):
        """GET /api/agents/llm-config 返回所有配置"""
        response = client.get("/api/agents/llm-config", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "pm" in data
        assert "llm_provider" in data["pm"]

    def test_update_llm_config(self):
        """PUT /api/agents/pm/llm-config 更新配置"""
        response = client.put(
            "/api/agents/pm/llm-config",
            headers=HEADERS,
            json={"llm_provider": "anthropic"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["llm_provider"] == "anthropic"

    def test_update_invalid_provider(self):
        """PUT 无效 provider 返回 422"""
        response = client.put(
            "/api/agents/pm/llm-config",
            headers=HEADERS,
            json={"llm_provider": "invalid"}
        )
        assert response.status_code == 422

    def test_update_unknown_agent(self):
        """PUT 不存在的 agent 返回 404"""
        response = client.put(
            "/api/agents/unknown/llm-config",
            headers=HEADERS,
            json={"llm_provider": "bailian"}
        )
        assert response.status_code == 404
