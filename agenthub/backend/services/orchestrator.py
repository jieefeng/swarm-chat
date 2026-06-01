"""Orchestrator Agent - LLM 驱动任务拆解 + Self-Correction"""
import json
import logging
from agenthub.backend.models.task import OrchestratorOutput
from agenthub.backend.services.agent_adapter import get_agent_adapter, IAgentAdapter

logger = logging.getLogger(__name__)

ORCHESTRATOR_SYSTEM_PROMPT = """你是任务协调器。分析用户需求，将其拆解为可执行的任务列表。

你必须以 JSON 格式输出，schema 如下：
{
  "analysis": "对用户需求的理解和分析",
  "tasks": [
    {
      "title": "任务标题（必须唯一）",
      "description": "任务详细描述",
      "assigned_to": "Agent ID: pm/architect/developer/qa",
      "depends_on": ["依赖的任务标题"],
      "priority": "high/medium/low"
    }
  ],
  "requires_clarification": false,
  "clarification_question": null,
  "uncertain_points": []
}

规则：
1. 任务标题必须唯一
2. assigned_to 必须是 pm/architect/developer/qa 之一
3. depends_on 引用其他任务的 title
4. 如果需求不清晰，设置 requires_clarification=true
5. 只输出 JSON，不要输出其他内容"""

MAX_SELF_CORRECTION_RETRIES = 2


class OrchestratorAgent:
    """Orchestrator Agent - 负责任务拆解"""

    def __init__(self, adapter: IAgentAdapter | None = None):
        self._adapter = adapter or get_agent_adapter()

    async def decompose(self, user_message: str) -> OrchestratorOutput:
        """拆解用户需求为任务列表，内置 Self-Correction"""
        error_context = ""
        for attempt in range(MAX_SELF_CORRECTION_RETRIES + 1):
            prompt = user_message
            if error_context:
                prompt = f"{user_message}\n\n[系统提示：上次输出有误，请修正。错误信息：{error_context}]"
            raw = await self._adapter.send_message(ORCHESTRATOR_SYSTEM_PROMPT, prompt)
            try:
                json_str = raw.strip()
                if json_str.startswith("```"):
                    lines = json_str.split("\n")
                    json_str = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
                output = OrchestratorOutput.model_validate_json(json_str)
                return output
            except Exception as e:
                logger.warning(f"Orchestrator output validation failed (attempt {attempt+1}): {e}")
                error_context = str(e)
        return OrchestratorOutput(
            analysis=f"需求拆解失败，降级为广播模式。原始需求：{user_message}",
            tasks=[],
            requires_clarification=False,
        )
