"""A2ARouter 单元测试（含新行为：prompt 注入 + invocation 创建）

TDD 红灯阶段：
- TestExtractMentionsFromTools / TestEnqueueA2ATargets / TestCancelThread / TestStateQueries 应该通过（验证已有行为）
- TestInvokeAgentNewBehavior 应该失败（Task 6 才会实现 prompt_injector + invocation_registry 调用）
"""
import asyncio
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
)

from agenthub.backend.services.a2a_router import A2ARouter


# ──────────────────────────────────────────────
# TestExtractMentionsFromTools（验证已有行为）
# ──────────────────────────────────────────────


class TestExtractMentionsFromTools:
    """_extract_mentions_from_tools 的正则解析测试"""

    def setup_method(self):
        self.router = A2ARouter()

    def test_extracts_single_mention(self):
        response = '{"invocation_id": "x", "target_agent_id": "developer", "content": "hi"}'
        assert self.router._extract_mentions_from_tools(response) == ["developer"]

    def test_extracts_multiple_mentions(self):
        response = (
            '{"target_agent_id": "developer", "content": "a"}\n'
            '{"target_agent_id": "qa", "content": "b"}'
        )
        assert self.router._extract_mentions_from_tools(response) == ["developer", "qa"]

    def test_dedupes_repeated_mentions(self):
        response = (
            '{"target_agent_id": "developer", "content": "a"}\n'
            '{"target_agent_id": "developer", "content": "b"}'
        )
        assert self.router._extract_mentions_from_tools(response) == ["developer"]

    def test_handles_spaces_around_colon(self):
        response = '{"target_agent_id" :  "designer", "content": "x"}'
        assert self.router._extract_mentions_from_tools(response) == ["designer"]

    def test_no_mention_returns_empty(self):
        response = "这里没有任何工具调用"
        assert self.router._extract_mentions_from_tools(response) == []


# ──────────────────────────────────────────────
# TestEnqueueA2ATargets（验证已有行为）
# ──────────────────────────────────────────────


class TestEnqueueA2ATargets:
    def setup_method(self):
        self.router = A2ARouter()

    def test_appends_new_target_to_worklist(self):
        self.router.thread_worklists["t1"] = ["designer"]
        self.router.enqueue_a2a_targets("t1", ["developer"])
        assert "developer" in self.router.thread_worklists["t1"]

    def test_dedupes_existing_target(self):
        self.router.thread_worklists["t1"] = ["designer", "developer"]
        self.router.enqueue_a2a_targets("t1", ["developer"])
        assert self.router.thread_worklists["t1"].count("developer") == 1

    def test_unknown_thread_is_noop(self):
        # 不应抛异常，worklists 不变
        self.router.enqueue_a2a_targets("nonexistent", ["qa"])
        assert "nonexistent" not in self.router.thread_worklists


# ──────────────────────────────────────────────
# TestCancelThread（验证已有行为）
# ──────────────────────────────────────────────


class TestCancelThread:
    def setup_method(self):
        self.router = A2ARouter()

    def test_cancel_sets_signal(self):
        signal = asyncio.Event()
        self.router.thread_signals["t1"] = signal
        self.router.cancel_thread("t1")
        assert signal.is_set()

    def test_cancel_unknown_thread_is_noop(self):
        # 不应抛异常
        self.router.cancel_thread("nonexistent")


# ──────────────────────────────────────────────
# TestStateQueries（验证已有行为）
# ──────────────────────────────────────────────


class TestStateQueries:
    def setup_method(self):
        self.router = A2ARouter()

    def test_is_running_false_for_unknown_thread(self):
        assert self.router.is_running("nonexistent") is False

    def test_get_thread_state_returns_state(self):
        self.router.thread_states["t1"] = {"is_running": True, "current_agent": "designer", "depth": 1}
        state = self.router.get_thread_state("t1")
        assert state is not None
        assert state["is_running"] is True
        assert state["current_agent"] == "designer"

    def test_get_thread_state_none_for_unknown(self):
        assert self.router.get_thread_state("nonexistent") is None


# ──────────────────────────────────────────────
# TestInvokeAgentNewBehavior（验证新行为 —— 应该失败）
# ──────────────────────────────────────────────


def _make_mock_memory():
    """创建 mock memory_manager，get_context_for_agent 返回空上下文"""
    mock = AsyncMock()
    mock.get_context_for_agent = AsyncMock(return_value="")
    return mock


def _make_mock_llm():
    """创建 mock LLM，send_message_stream 返回一个简单 chunk"""
    mock = MagicMock()

    def stream(**kwargs):
        yield "hello from agent"

    mock.send_message_stream = MagicMock(side_effect=stream)
    return mock


class TestInvokeAgentNewBehavior:
    """验证 _invoke_agent 在 Task 6 中新增的行为

    这些测试在 TDD 红灯阶段应该 FAIL，因为当前实现没有调用
    invocation_registry.create 和 prompt_injector.inject_into_system_prompt。
    """

    def setup_method(self):
        self.router = A2ARouter()

    @pytest.mark.asyncio
    async def test_invoke_agent_creates_invocation_before_llm(self):
        """_invoke_agent 应在 LLM 调用前创建 invocation"""
        mock_registry = MagicMock()
        mock_registry.create = MagicMock(return_value=("inv-id-123", "tok-456"))

        mock_injector = MagicMock()
        mock_injector.inject_into_system_prompt = MagicMock(return_value="injected prompt")

        mock_memory = _make_mock_memory()
        mock_llm = _make_mock_llm()

        fake_config = {
            "designer": {
                "system_prompt": "You are a designer",
                "llm_provider": "bailian",
            }
        }

        with (
            patch.dict("sys.modules", {
                "agenthub.backend.services.session": MagicMock(
                    AGENT_CONFIGS=fake_config,
                    session_manager=MagicMock(),
                ),
                "agenthub.backend.services.llm_router": MagicMock(
                    get_llm_service_for_provider=MagicMock(return_value=mock_llm),
                ),
                "agenthub.backend.services.memory_manager": MagicMock(
                    memory_manager=mock_memory,
                    redis_memory_manager=mock_memory,
                ),
            }),
        ):
            # 模块级全局替换
            import agenthub.backend.services.a2a_router as router_mod

            original_registry = getattr(router_mod, "invocation_registry", None)
            original_injector = getattr(router_mod, "prompt_injector", None)

            try:
                # 注入 mock 到模块级全局（Task 6 会在 _invoke_agent 中使用它们）
                router_mod.invocation_registry = mock_registry
                router_mod.prompt_injector = mock_injector

                chunks = []
                async for chunk in self.router._invoke_agent("designer", "hi", "t1", "u1"):
                    chunks.append(chunk)

                # 断言：invocation_registry.create 应被调用
                mock_registry.create.assert_called_once_with("designer", "t1")
            finally:
                if original_registry is not None:
                    router_mod.invocation_registry = original_registry
                if original_injector is not None:
                    router_mod.prompt_injector = original_injector

    @pytest.mark.asyncio
    async def test_invoke_agent_injects_prompt_before_llm(self):
        """_invoke_agent 应在 LLM 调用前注入 callback 指令到 system_prompt"""
        mock_registry = MagicMock()
        mock_registry.create = MagicMock(return_value=("inv-id-789", "tok-abc"))

        mock_injector = MagicMock()
        injected_prompt = "You are a designer\n\n## callback instructions here"
        mock_injector.inject_into_system_prompt = MagicMock(return_value=injected_prompt)

        mock_memory = _make_mock_memory()
        mock_llm = _make_mock_llm()

        fake_config = {
            "designer": {
                "system_prompt": "You are a designer",
                "llm_provider": "bailian",
            }
        }

        with (
            patch.dict("sys.modules", {
                "agenthub.backend.services.session": MagicMock(
                    AGENT_CONFIGS=fake_config,
                    session_manager=MagicMock(),
                ),
                "agenthub.backend.services.llm_router": MagicMock(
                    get_llm_service_for_provider=MagicMock(return_value=mock_llm),
                ),
                "agenthub.backend.services.memory_manager": MagicMock(
                    memory_manager=mock_memory,
                    redis_memory_manager=mock_memory,
                ),
            }),
        ):
            import agenthub.backend.services.a2a_router as router_mod

            original_registry = getattr(router_mod, "invocation_registry", None)
            original_injector = getattr(router_mod, "prompt_injector", None)

            try:
                router_mod.invocation_registry = mock_registry
                router_mod.prompt_injector = mock_injector

                chunks = []
                async for chunk in self.router._invoke_agent("designer", "hi", "t1", "u1"):
                    chunks.append(chunk)

                # 断言：inject_into_system_prompt 应被调用
                mock_injector.inject_into_system_prompt.assert_called_once()

                # 断言：LLM 收到的 system_prompt 应包含注入内容
                call_kwargs = mock_llm.send_message_stream.call_args
                actual_prompt = call_kwargs.kwargs.get("system_prompt") or call_kwargs[1].get("system_prompt", "")
                assert "callback" in actual_prompt.lower() or injected_prompt == actual_prompt, (
                    f"Expected injected prompt, got: {actual_prompt}"
                )
            finally:
                if original_registry is not None:
                    router_mod.invocation_registry = original_registry
                if original_injector is not None:
                    router_mod.prompt_injector = original_injector
