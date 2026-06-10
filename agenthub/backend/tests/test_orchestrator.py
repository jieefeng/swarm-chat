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
    {"title": "设计登录页面", "description": "设计UI", "assigned_to": "designer", "depends_on": [], "priority": "high"},
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
        '{"analysis":"ok","tasks":[{"title":"T1","description":"D1","assigned_to":"designer"}],"requires_clarification":false,"clarification_question":null,"uncertain_points":[]}'
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


def test_orchestrator_prompt_references_three_agents():
    """验证 orchestrator prompt 引用 3 个核心 agent"""
    from agenthub.backend.services.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
    assert "designer" in ORCHESTRATOR_SYSTEM_PROMPT
    assert "developer" in ORCHESTRATOR_SYSTEM_PROMPT
    assert "qa" in ORCHESTRATOR_SYSTEM_PROMPT
    assert "pm" not in ORCHESTRATOR_SYSTEM_PROMPT
    assert "architect" not in ORCHESTRATOR_SYSTEM_PROMPT


def test_orchestrator_prompt_assigned_to_values():
    """验证 assigned_to 提示值为 designer/developer/qa"""
    from agenthub.backend.services.orchestrator import ORCHESTRATOR_SYSTEM_PROMPT
    assert "designer/developer/qa" in ORCHESTRATOR_SYSTEM_PROMPT
