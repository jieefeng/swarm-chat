"""Agent 适配器测试"""
import pytest
from unittest.mock import AsyncMock, patch

from services.agent_adapter import BailianAdapter


@pytest.mark.asyncio
async def test_send_message_returns_string():
    adapter = BailianAdapter()
    with patch.object(
        adapter._service,
        "send_message_with_retry",
        new_callable=AsyncMock,
        return_value="test response",
    ):
        result = await adapter.send_message("system", "hello")
        assert result == "test response"


@pytest.mark.asyncio
async def test_send_message_passes_params():
    adapter = BailianAdapter()
    with patch.object(
        adapter._service,
        "send_message_with_retry",
        new_callable=AsyncMock,
        return_value="ok",
    ) as mock:
        await adapter.send_message("sys prompt", "user msg")
        mock.assert_called_once_with(
            session_id="agent-adapter",
            message="user msg",
            system_prompt="sys prompt",
        )


@pytest.mark.asyncio
async def test_send_message_stream_yields_chunks():
    adapter = BailianAdapter()
    with patch.object(
        adapter._service,
        "send_message_with_retry",
        new_callable=AsyncMock,
        return_value="chunk1\n\nchunk2\n\n",
    ):
        chunks = []
        async for chunk in adapter.send_message_stream("system", "hello"):
            chunks.append(chunk)
        assert len(chunks) >= 1
        assert "".join(chunks).strip() == "chunk1\n\nchunk2"
