"""统一 Agent 适配器层 - 屏蔽不同 LLM 提供商差异"""
import asyncio
from typing import AsyncIterator, Protocol

from .llm_router import get_llm_service


class IAgentAdapter(Protocol):
    """Agent 适配器协议"""

    async def send_message(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict] | None = None,
    ) -> str:
        """同步发送消息，返回完整回复"""
        ...

    async def send_message_stream(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict] | None = None,
    ) -> AsyncIterator[str]:
        """流式发送消息，yield 文本片段"""
        ...


class BailianAdapter:
    """百炼 API 适配器"""

    def __init__(self):
        self._service = get_llm_service()

    async def send_message(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict] | None = None,
    ) -> str:
        # 历史消息暂不拼接，当前 BailianService.send_message_with_retry
        # 只接收单条 user message + system_prompt
        return await self._service.send_message_with_retry(
            session_id="agent-adapter",
            message=user_message,
            system_prompt=system_prompt,
        )

    async def send_message_stream(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict] | None = None,
    ) -> AsyncIterator[str]:
        """流式调用 - 当前百炼服务不支持流式，回退为完整返回后逐块发送"""
        full_response = await self.send_message(system_prompt, user_message, history)
        # 模拟流式：按段落切分
        for chunk in full_response.split("\n\n"):
            yield chunk + "\n\n"
            await asyncio.sleep(0.05)


def get_agent_adapter() -> IAgentAdapter:
    """获取 Agent 适配器实例"""
    return BailianAdapter()
