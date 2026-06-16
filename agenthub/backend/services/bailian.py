"""阿里云百炼 API 服务封装 - 兼容 OpenAI 接口"""
import os
import time
import threading
from collections.abc import Generator
from typing import Optional
from openai import OpenAI


class BailianService:
    """百炼 API 服务封装 - 带重试和超时"""

    DEFAULT_MODEL = "qwen3.7-max-preview"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = model or self.DEFAULT_MODEL
        self.default_timeout = 60  # 秒

    @classmethod
    def get_default_model(cls) -> str:
        return cls.DEFAULT_MODEL

    async def send_message_with_retry(
        self,
        session_id: str,
        message: str,
        system_prompt: str = "",
        max_retries: int = 3,
        timeout: Optional[int] = None
    ) -> str:
        """发送消息到百炼 API，带重试机制

        Args:
            session_id: 会话ID
            message: 用户消息
            system_prompt: 系统提示
            max_retries: 最大重试次数
            timeout: 超时时间（秒）

        Returns:
            百炼的响应文本

        Raises:
            Exception: 重试耗尽后抛出
        """
        timeout = timeout or self.default_timeout

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    timeout=timeout
                )
                return response.choices[0].message.content

            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"百炼 API 调用失败，已重试{max_retries}次: {str(e)}") from e

                wait_time = 2 ** attempt  # 指数退避: 1, 2, 4秒
                await asyncio.sleep(wait_time)

        return ""  # 不会执行到这里

    def send_message(
        self,
        session_id: str,
        message: str,
        system_prompt: str = "",
        tools: list[dict] | None = None,
        tool_choice: str | None = None,
    ) -> str:
        """同步发送消息到百炼 API（无重试）

        Args:
            session_id: 会话ID
            message: 用户消息
            system_prompt: 系统提示
            tools: 工具定义列表（OpenAI function calling 格式）
            tool_choice: 工具选择策略

        Returns:
            百炼的响应文本
        """
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            "timeout": self.default_timeout,
        }
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice

        response = self.client.chat.completions.create(**kwargs)
        msg = response.choices[0].message
        return msg.content or ""

    def send_message_stream(
        self,
        session_id: str,
        message: str,
        system_prompt: str = "",
        tools: list[dict] | None = None,
        tool_choice: str | None = None,
        stream_timeout: int = 180,
    ) -> Generator:
        """流式发送消息到百炼 API

        Args:
            session_id: 会话ID
            message: 用户消息
            system_prompt: 系统提示
            tools: 工具定义列表
            tool_choice: 工具选择策略
            stream_timeout: 流式调用总超时（秒），默认 180 秒

        Yields:
            当无 tools 时: str（文本片段）
            当有 tools 时: ChatCompletionChunk 对象（需检查 .delta.tool_calls）

        Raises:
            TimeoutError: 超过 stream_timeout 时抛出
        """
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            "timeout": self.default_timeout,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice

        stream = self.client.chat.completions.create(**kwargs)
        start_time = time.monotonic()

        for chunk in stream:
            # 检查总超时
            elapsed = time.monotonic() - start_time
            if elapsed > stream_timeout:
                raise TimeoutError(
                    f"百炼流式调用超时: 已运行 {elapsed:.1f}s，超过限制 {stream_timeout}s"
                )

            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if tools:
                yield chunk
            elif delta.content:
                yield delta.content


# 全局百炼服务实例
bailian_service = BailianService()