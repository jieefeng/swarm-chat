"""阿里云百炼 API 服务封装 - 兼容 OpenAI 接口"""
import os
import asyncio
from collections.abc import Generator
from typing import Optional
from openai import OpenAI


class BailianService:
    """百炼 API 服务封装 - 带重试和超时"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = "qwen3.5-plus-2026-04-20"
        self.default_timeout = 60  # 秒

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
        system_prompt: str = ""
    ) -> str:
        """同步发送消息到百炼 API（无重试）

        Args:
            session_id: 会话ID
            message: 用户消息
            system_prompt: 系统提示

        Returns:
            百炼的响应文本
        """
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            timeout=self.default_timeout
        )
        return response.choices[0].message.content

    def send_message_stream(
        self,
        session_id: str,
        message: str,
        system_prompt: str = ""
    ) -> Generator[str, None, None]:
        """流式发送消息到百炼 API，逐个 yield 文本片段

        Yields:
            LLM 响应的文本片段
        """
        stream = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            timeout=self.default_timeout,
            stream=True
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# 全局百炼服务实例
bailian_service = BailianService()