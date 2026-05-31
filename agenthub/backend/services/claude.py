"""Claude API服务 - 带有重试机制"""
import os
import asyncio
from collections.abc import Generator
from typing import Optional
from anthropic import Anthropic


class ClaudeService:
    """Claude API服务封装 - 带重试和超时"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.client = Anthropic(api_key=self.api_key)
        self.default_timeout = 60  # 秒

    async def send_message_with_retry(
        self,
        session_id: str,
        message: str,
        system_prompt: str = "",
        max_retries: int = 3,
        timeout: Optional[int] = None
    ) -> str:
        """发送消息到Claude API，带重试机制

        Args:
            session_id: 会话ID
            message: 用户消息
            system_prompt: 系统提示
            max_retries: 最大重试次数
            timeout: 超时时间（秒）

        Returns:
            Claude的响应文本

        Raises:
            Exception: 重试耗尽后抛出
        """
        timeout = timeout or self.default_timeout

        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1024,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": message}
                    ],
                    timeout=timeout
                )
                return response.content[0].text

            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Claude API调用失败，已重试{max_retries}次: {str(e)}") from e

                wait_time = 2 ** attempt  # 指数退避: 1, 2, 4秒
                await asyncio.sleep(wait_time)

        return ""  # 不会执行到这里

    def send_message(
        self,
        session_id: str,
        message: str,
        system_prompt: str = ""
    ) -> str:
        """同步发送消息到Claude API（无重试）

        Args:
            session_id: 会话ID
            message: 用户消息
            system_prompt: 系统提示

        Returns:
            Claude的响应文本
        """
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": message}
            ]
        )
        return response.content[0].text

    def send_message_stream(
        self,
        session_id: str,
        message: str,
        system_prompt: str = ""
    ) -> Generator[str, None, None]:
        """流式发送消息到Claude API，逐个 yield 文本片段

        Yields:
            LLM 响应的文本片段
        """
        with self.client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=[
                {"role": "user", "content": message}
            ]
        ) as stream:
            for text in stream.text_stream:
                yield text


# 全局Claude服务实例
claude_service = ClaudeService()