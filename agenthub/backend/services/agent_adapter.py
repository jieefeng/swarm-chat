"""统一 Agent 适配器层 - 屏蔽不同 LLM 提供商差异"""
import asyncio
import os
from typing import AsyncIterator, Protocol

from .llm_router import get_llm_service_for_provider


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
        self._service = get_llm_service_for_provider("bailian")

    async def send_message(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict] | None = None,
    ) -> str:
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
        for chunk in full_response.split("\n\n"):
            yield chunk + "\n\n"
            await asyncio.sleep(0.05)


class ClaudeAdapter:
    """Anthropic Claude API 适配器"""

    def __init__(self):
        self._service = get_llm_service_for_provider("anthropic")

    async def send_message(
        self,
        system_prompt: str,
        user_message: str,
        history: list[dict] | None = None,
    ) -> str:
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
        """流式调用 Claude API"""
        loop = asyncio.get_event_loop()
        def _sync_stream():
            yield from self._service.send_message_stream(
                session_id="agent-adapter",
                message=user_message,
                system_prompt=system_prompt,
            )
        for chunk in await loop.run_in_executor(None, lambda: list(_sync_stream())):
            yield chunk


def get_agent_adapter(provider: str | None = None) -> IAgentAdapter:
    """获取 Agent 适配器实例

    Args:
        provider: LLM provider 名称 ("bailian" / "anthropic")。
                  为 None 时使用环境变量 LLM_PROVIDER（默认 bailian）。
    """
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "bailian")

    if provider == "anthropic":
        return ClaudeAdapter()
    return BailianAdapter()
