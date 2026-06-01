"""Orchestrator Agent 测试"""
import pytest
from unittest.mock import AsyncMock
from agenthub.backend.models.task import OrchestratorOutput
from agenthub.backend.services.orchestrator import OrchestratorAgent


@pytest.mark.asyncio
async def test_decompose_valid_json():
    mock_adapter = AsyncMock()
    mock_adapter.send_message = AsyncMock(return_value='''```json
{
  "analysis": "用户要建一个登录页面",
  "tasks": [
    {"title": "设计登录页面", "description": "设计UI", "assigned_to": "pm", "depends_on": [], "priority": "high"},
    {"title": "实现登录API", "description": "写后端", "assigned_to": "developer", "depends_on": ["设计登录页面"], "priority": "high"}
  ],
  "requires_clarification": false,
  "clarification_question": null,
  "uncertain_points": []
}
```''')
    agent = OrchestratorAgent(adapter=mock_adapter)
    output = await agent.decompose("我要一个登录页面")
    assert isinstance(output, OrchestratorOutput)
    assert len(output.tasks) == 2
    assert output.tasks[1].depends_on == ["设计登录页面"]


@pytest.mark.asyncio
async def test_decompose_self_correction():
    mock_adapter = AsyncMock()
    mock_adapter.send_message = AsyncMock(side_effect=[
        "invalid json here",
        '{"analysis":"ok","tasks":[{"title":"T1","description":"D1","assigned_to":"pm"}],"requires_clarification":false,"clarification_question":null,"uncertain_points":[]}'
    ])
    agent = OrchestratorAgent(adapter=mock_adapter)
    output = await agent.decompose("test")
    assert len(output.tasks) == 1


@pytest.mark.asyncio
async def test_decompose_fallback_on_repeated_failure():
    mock_adapter = AsyncMock()
    mock_adapter.send_message = AsyncMock(return_value="always invalid")
    agent = OrchestratorAgent(adapter=mock_adapter)
    output = await agent.decompose("test")
    assert output.tasks == []
    assert "降级" in output.analysis
