"""SessionManager tool_calls 循环测试"""
from unittest.mock import patch, MagicMock
import pytest

from agenthub.backend.services.session import SessionManager


class TestToolCallsLoop:

    def test_no_tools_when_claude_code_unavailable(self):
        """Claude Code 不可用时不传 tools 参数"""
        sm = SessionManager()
        with patch("agenthub.backend.services.session.claude_code_service") as mock_cc:
            mock_cc.is_available.return_value = False
            with patch("agenthub.backend.services.llm_router.get_llm_service_for_provider") as mock_get:
                mock_llm = MagicMock()
                mock_llm.send_message_stream.return_value = iter(["普通回复"])
                mock_get.return_value = mock_llm

                chunks = list(sm.send_to_agent_stream("pm", "你好"))
                assert "".join(chunks) == "普通回复"
                call_kwargs = mock_llm.send_message_stream.call_args
                assert call_kwargs[1].get("tools") is None

    def test_tool_calls_triggers_claude_code_execution(self):
        """LLM 返回 tool_calls 时触发 Claude Code 执行"""
        sm = SessionManager()

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = None
        mock_chunk.choices[0].delta.tool_calls = [MagicMock()]
        mock_chunk.choices[0].delta.tool_calls[0].id = "call_123"
        mock_chunk.choices[0].delta.tool_calls[0].function.name = "claude_code"
        mock_chunk.choices[0].delta.tool_calls[0].function.arguments = '{"prompt": "读取 main.py"}'

        with patch("agenthub.backend.services.session.claude_code_service") as mock_cc:
            mock_cc.is_available.return_value = True
            mock_cc.execute.return_value = MagicMock(
                success=True, output="文件内容", error=""
            )

            with patch("agenthub.backend.services.llm_router.get_llm_service_for_provider") as mock_get:
                mock_llm = MagicMock()
                mock_llm.send_message_stream.side_effect = [
                    iter([mock_chunk]),
                    iter(["最终回复"]),
                ]
                mock_get.return_value = mock_llm

                results = []
                for chunk in sm.send_to_agent_stream("pm", "读取 main.py"):
                    results.append(chunk)

                mock_cc.execute.assert_called_once()
                assert mock_llm.send_message_stream.call_count == 2


class TestToolCallsEdgeCases:

    def test_tools_parameter_passed_when_available(self):
        """Claude Code 可用时传递 tools 参数"""
        sm = SessionManager()
        with patch("agenthub.backend.services.session.claude_code_service") as mock_cc:
            mock_cc.is_available.return_value = True
            with patch("agenthub.backend.services.llm_router.get_llm_service_for_provider") as mock_get:
                mock_llm = MagicMock()
                mock_llm.send_message_stream.return_value = iter(["回复"])
                mock_get.return_value = mock_llm

                list(sm.send_to_agent_stream("pm", "你好"))
                call_kwargs = mock_llm.send_message_stream.call_args
                assert call_kwargs[1].get("tools") is not None

    def test_unknown_agent_returns_error(self):
        """未知 agent 返回错误信息"""
        sm = SessionManager()
        chunks = list(sm.send_to_agent_stream("nonexistent", "你好"))
        assert any("Error" in c for c in chunks)

    def test_max_rounds_prevents_infinite_loop(self):
        """超过最大轮次后停止循环"""
        sm = SessionManager()

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = None
        mock_chunk.choices[0].delta.tool_calls = [MagicMock()]
        mock_chunk.choices[0].delta.tool_calls[0].id = "call_loop"
        mock_chunk.choices[0].delta.tool_calls[0].function.name = "claude_code"
        mock_chunk.choices[0].delta.tool_calls[0].function.arguments = '{"prompt": "loop"}'

        with patch("agenthub.backend.services.session.claude_code_service") as mock_cc:
            mock_cc.is_available.return_value = True
            mock_cc.execute.return_value = MagicMock(
                success=True, output="ok", error=""
            )

            with patch("agenthub.backend.services.llm_router.get_llm_service_for_provider") as mock_get:
                mock_llm = MagicMock()
                mock_llm.send_message_stream.side_effect = [iter([mock_chunk]) for _ in range(4)]
                mock_get.return_value = mock_llm

                list(sm.send_to_agent_stream("pm", "loop"))

                # max_rounds=3, so range(3+1) = 4 calls
                assert mock_llm.send_message_stream.call_count == 4

    def test_callbacks_invoked_on_tool_execution(self):
        """工具执行时回调被调用"""
        sm = SessionManager()

        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock()]
        mock_chunk.choices[0].delta.content = None
        mock_chunk.choices[0].delta.tool_calls = [MagicMock()]
        mock_chunk.choices[0].delta.tool_calls[0].id = "call_cb"
        mock_chunk.choices[0].delta.tool_calls[0].function.name = "claude_code"
        mock_chunk.choices[0].delta.tool_calls[0].function.arguments = '{"prompt": "test"}'

        on_tool_start = MagicMock()
        on_tool_result = MagicMock()

        with patch("agenthub.backend.services.session.claude_code_service") as mock_cc:
            mock_cc.is_available.return_value = True
            mock_cc.execute.return_value = MagicMock(
                success=True, output="result", error=""
            )

            with patch("agenthub.backend.services.llm_router.get_llm_service_for_provider") as mock_get:
                mock_llm = MagicMock()
                mock_llm.send_message_stream.side_effect = [
                    iter([mock_chunk]),
                    iter(["done"]),
                ]
                mock_get.return_value = mock_llm

                list(sm.send_to_agent_stream(
                    "pm", "test",
                    on_tool_start=on_tool_start,
                    on_tool_result=on_tool_result,
                ))

                on_tool_start.assert_called_once()
                on_tool_result.assert_called_once()
