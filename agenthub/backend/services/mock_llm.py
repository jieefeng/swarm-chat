"""模拟 LLM 服务 - 不发起任何真实网络调用，不读取/使用任何 API Key

所有原真实 LLM 提供商（百炼 / MiniMax / Claude）统一替换为本模拟实现。
接口签名与原服务保持一致，调用方（session / a2a_router / agent_adapter）
无需任何改动。
"""
import asyncio
import os
import time
from collections.abc import Generator


class MockLLMService:
    """模拟 LLM 服务：返回确定性的模拟回复，支持与真实服务相同的调用方式"""

    DEFAULT_MODEL = "mock-model"
    # 流式输出时每个片段之间的间隔（秒），用于模拟打字机效果
    STREAM_CHUNK_DELAY = 0.02

    def __init__(self, api_key: str | None = None, model: str | None = None, provider: str = "mock"):
        # api_key 参数仅为兼容旧签名保留；任何传入的 key 都不会被使用或转发
        self.api_key = "mock-not-used"
        self.provider = provider
        self.model = model or os.getenv("MOCK_LLM_MODEL") or self.DEFAULT_MODEL
        self.default_timeout = 60  # 秒
        # 测试里通过 conftest 设 MOCK_LLM_STREAM_DELAY=0 跳过打字机延迟
        self.stream_chunk_delay = float(
            os.getenv("MOCK_LLM_STREAM_DELAY", str(self.STREAM_CHUNK_DELAY))
        )

    @classmethod
    def get_default_model(cls) -> str:
        return cls.DEFAULT_MODEL

    def _build_reply(self, message: str) -> str:
        """根据用户消息生成确定性的模拟回复"""
        preview = " ".join((message or "").split())
        if len(preview) > 80:
            preview = preview[:77] + "..."
        if preview:
            echo = f'已收到消息: "{preview}"。'
        else:
            echo = "已收到空消息。"
        return (
            f"[模拟回复 | {self.provider}:{self.model}] {echo}\n\n"
            f"当前系统处于模拟模式，未调用任何真实 LLM API，也未使用任何 API Key。"
        )

    async def send_message_with_retry(
        self,
        session_id: str,
        message: str,
        system_prompt: str = "",
        max_retries: int = 3,
        timeout: int | None = None,
    ) -> str:
        """模拟带重试的异步发送（实际直接返回模拟回复，不会失败）"""
        await asyncio.sleep(0)
        return self._build_reply(message)

    def send_message(
        self,
        session_id: str,
        message: str,
        system_prompt: str = "",
        tools: list[dict] | None = None,
        tool_choice: str | None = None,
    ) -> str:
        """同步发送消息，返回模拟回复（忽略 tools，不会产生 tool_calls）"""
        return self._build_reply(message)

    def send_message_stream(
        self,
        session_id: str,
        message: str,
        system_prompt: str = "",
        tools: list[dict] | None = None,
        tool_choice: str | None = None,
        stream_timeout: int = 180,
    ) -> Generator[str, None, None]:
        """流式发送消息，逐段 yield 模拟回复文本

        始终 yield str 片段；即使传入 tools 也不会产生 tool_calls，
        因此下游的 tool 执行循环（如 Claude Code 子进程）不会被触发。
        """
        reply = self._build_reply(message)
        # 按固定长度切片，保留换行符
        chunks = [reply[i:i + 8] for i in range(0, len(reply), 8)]
        for chunk in chunks:
            if self.stream_chunk_delay > 0:
                time.sleep(self.stream_chunk_delay)
            yield chunk
