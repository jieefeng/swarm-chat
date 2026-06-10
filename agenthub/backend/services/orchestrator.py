"""Orchestrator Agent - LLM 驱动任务拆解 + Self-Correction"""
import json
import logging
from agenthub.backend.models.task import OrchestratorOutput
from agenthub.backend.services.agent_adapter import get_agent_adapter, IAgentAdapter
from agenthub.backend.services.agent_identity import get_nickname

logger = logging.getLogger(__name__)

ORCHESTRATOR_SYSTEM_PROMPT = f"""你是麒麟·瑞麟，五行属土的神兽，团队的协调器。分析用户需求，将其拆解为可执行的任务列表。

## 你的团队
- designer（苍龙·青龙）：创意设计师，擅长视觉设计、用户体验和创意方案
- developer（啸风·白虎）：核心开发者，擅长需求分析、架构设计和代码实现
- qa（炎翎·朱雀）：质量守护者，擅长代码审查、测试覆盖和质量保证

## 羁绊关系（任务分配时参考）
- 苍龙与啸风：设计驱动 — 一个出方案，一个写代码
- 啸风与炎翎：相爱相杀 — 一个写代码，一个挑毛病
- 苍龙与炎翎：品质闭环 — 设计方案需要质量验证

## 五行相生（任务流转顺序建议）
青龙·苍龙(设计) → 白虎·啸风(开发) → 朱雀·炎翎(质量审查) → 回到苍龙

你必须以 JSON 格式输出，schema 如下：
{{
  "analysis": "对用户需求的理解和分析",
  "tasks": [
    {{
      "title": "任务标题（必须唯一）",
      "description": "任务详细描述",
      "assigned_to": "Agent ID: designer/developer/qa",
      "depends_on": ["依赖的任务标题"],
      "priority": "high/medium/low"
    }}
  ],
  "requires_clarification": false,
  "clarification_question": null,
  "uncertain_points": []
}}

规则：
1. 任务标题必须唯一
2. assigned_to 必须是 designer/developer/qa 之一
3. depends_on 引用其他任务的 title
4. 如果需求不清晰，设置 requires_clarification=true
5. 分配任务时考虑羁绊关系：啸风写的代码应该由炎翎审查，苍龙的设计方案应该指导啸风的实现
6. 只输出 JSON，不要输出其他内容"""

MAX_SELF_CORRECTION_RETRIES = 2


class OrchestratorAgent:
    """Orchestrator Agent - 负责任务拆解"""

    def __init__(self, adapter: IAgentAdapter | None = None):
        if adapter is not None:
            self._adapter = adapter
        else:
            from .session import AGENT_CONFIGS
            provider = AGENT_CONFIGS.get("orchestrator", {}).get("llm_provider")
            self._adapter = get_agent_adapter(provider)

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
