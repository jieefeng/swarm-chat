"""Claude API 服务（模拟实现） - 已移除真实 API 调用

原实现通过 Anthropic SDK 调用 Claude 端点（使用 ANTHROPIC_API_KEY），
现全部替换为本地模拟回复，不发起网络请求，不读取任何 API Key。
"""
from collections.abc import Generator

from .mock_llm import MockLLMService


class ClaudeService(MockLLMService):
    """Claude 服务模拟实现 - 接口与原真实服务一致"""

    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, api_key: str | None = None):
        super().__init__(api_key=api_key, provider="anthropic")

    def send_message(
        self,
        session_id: str,
        message: str,
        system_prompt: str = "",
        tools: list[dict] | None = None,
        tool_choice: str | None = None,
    ) -> str:
        """兼容原 ClaudeService 的三参签名"""
        return super().send_message(
            session_id=session_id,
            message=message,
            system_prompt=system_prompt,
            tools=tools,
            tool_choice=tool_choice,
        )

    def send_message_stream(
        self,
        session_id: str,
        message: str,
        system_prompt: str = "",
        tools: list[dict] | None = None,
        tool_choice: str | None = None,
        stream_timeout: int = 180,
    ) -> Generator[str, None, None]:
        """兼容原 ClaudeService 的五参签名"""
        return super().send_message_stream(
            session_id=session_id,
            message=message,
            system_prompt=system_prompt,
            tools=tools,
            tool_choice=tool_choice,
            stream_timeout=stream_timeout,
        )


# 全局 Claude 服务实例（模拟）
claude_service = ClaudeService()
