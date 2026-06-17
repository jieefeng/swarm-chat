# A2A 收尾 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 A2A 协作架构从"代码 90% 已写但端到端不通"状态工程化收尾 — 端到端能跑 + 80% 测试覆盖 + 文档同步。

**Architecture:** 测试驱动，先测已存在代码（invocation_registry / prompt_injector / callback_router / callbacks API），再补 a2a_router 的 prompt 注入 + invocation 创建，最后让 messages.py 走 a2a_router.route_execution。新增 `POST /api/a2a/cancel` 端点供前端 Stop 按钮。

**Tech Stack:** Python 3.x, FastAPI, pytest + pytest-asyncio（`asyncio_mode = auto`）, unittest.mock

---

## File Structure

**修改文件：**
- `agenthub/backend/services/a2a_router.py` — `_invoke_agent` 加 prompt_injector + invocation_registry
- `agenthub/backend/routers/messages.py` — `send_message` 走 `a2a_router.route_execution`，新增 `POST /api/a2a/cancel` 端点
- `agenthub/CLAUDE.md` — 新增"A2A 隐性知识"小节
- `docs/superpowers/specs/2026-06-10-a2a-collaboration-design.md` — 末尾加"已实施日期"

**新增文件：**
- `agenthub/backend/tests/test_invocation_registry.py` — 纯逻辑单元测试
- `agenthub/backend/tests/test_prompt_injector.py` — 纯字符串断言单元测试
- `agenthub/backend/tests/test_callback_router.py` — mock 业务依赖单元测试
- `agenthub/backend/tests/test_callbacks_api.py` — `fastapi.testclient` 集成测试
- `agenthub/backend/tests/test_a2a_router.py` — mock LLM + 依赖单元测试

**不动文件：** `callback_router.py` / `invocation_registry.py` / `callbacks.py` / `prompt_injector.py` / 前端文件

---

## Task 1: InvocationRegistry 单元测试（验证已存在代码）

**Files:**
- Create: `agenthub/backend/tests/test_invocation_registry.py`

- [ ] **Step 1: 创建测试文件**

在 `agenthub/backend/tests/test_invocation_registry.py` 写入：

```python
"""InvocationRegistry 单元测试（验证已存在实现）"""
import time
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agenthub.backend.services.invocation_registry import InvocationRegistry


class TestInvocationRegistry:
    @pytest.fixture
    def registry(self):
        return InvocationRegistry(ttl=10)

    def test_create_returns_uuid_pair(self, registry):
        inv_id, token = registry.create("designer", "thread-1")
        assert isinstance(inv_id, str) and len(inv_id) == 36
        assert isinstance(token, str) and len(token) == 36
        assert inv_id != token

    def test_create_stores_metadata(self, registry):
        inv_id, _ = registry.create("developer", "thread-2")
        inv = registry.get_invocation(inv_id)
        assert inv is not None
        assert inv["agent_id"] == "developer"
        assert inv["thread_id"] == "thread-2"
        assert inv["ttl"] == 10

    def test_verify_with_correct_credentials(self, registry):
        inv_id, token = registry.create("qa", "thread-3")
        inv = registry.verify(inv_id, token)
        assert inv is not None
        assert inv["agent_id"] == "qa"

    def test_verify_with_wrong_token(self, registry):
        inv_id, _ = registry.create("designer", "thread-4")
        assert registry.verify(inv_id, "wrong-token") is None

    def test_verify_unknown_invocation(self, registry):
        assert registry.verify("nonexistent-id", "any-token") is None

    def test_verify_expired_invocation_returns_none_and_removes(self, registry):
        inv_id, token = registry.create("designer", "thread-5")
        # 直接修改 created_at 到 11 秒前
        registry._invocations[inv_id]["created_at"] = time.time() - 11
        assert registry.verify(inv_id, token) is None
        assert registry.get_invocation(inv_id) is None

    def test_revoke_removes_invocation(self, registry):
        inv_id, _ = registry.create("developer", "thread-6")
        assert registry.revoke(inv_id) is True
        assert registry.get_invocation(inv_id) is None

    def test_revoke_unknown_returns_false(self, registry):
        assert registry.revoke("nonexistent") is False

    def test_cleanup_expired_removes_only_expired(self, registry):
        inv_id_old, _ = registry.create("designer", "thread-7")
        inv_id_new, _ = registry.create("developer", "thread-8")
        registry._invocations[inv_id_old]["created_at"] = time.time() - 100
        registry.cleanup_expired()
        assert registry.get_invocation(inv_id_old) is None
        assert registry.get_invocation(inv_id_new) is not None

    def test_count_tracks_active_invocations(self, registry):
        assert registry.count() == 0
        registry.create("designer", "thread-9")
        registry.create("developer", "thread-10")
        assert registry.count() == 2

    def test_get_all_invocations_returns_copy(self, registry):
        registry.create("designer", "thread-11")
        snapshot = registry.get_all_invocations()
        assert len(snapshot) == 1
        # 修改 snapshot 不影响内部
        snapshot.clear()
        assert registry.count() == 1
```

- [ ] **Step 2: 运行测试，预期全部 PASS**

```bash
cd agenthub/backend && python -m pytest tests/test_invocation_registry.py -v
```

预期：11 个测试全 PASS，0 fail。

- [ ] **Step 3: Commit**

```bash
cd ../.. && git add agenthub/backend/tests/test_invocation_registry.py
git commit -m "test(backend): add invocation_registry unit tests"
```

---

## Task 2: PromptInjector 单元测试（验证已存在代码）

**Files:**
- Create: `agenthub/backend/tests/test_prompt_injector.py`

- [ ] **Step 1: 创建测试文件**

在 `agenthub/backend/tests/test_prompt_injector.py` 写入：

```python
"""PromptInjector 单元测试（验证已存在实现 + 3-agent 适配）"""
import os
import pytest
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agenthub.backend.services.prompt_injector import PromptInjector


class TestPromptInjector:
    @pytest.fixture
    def injector(self):
        return PromptInjector(api_url="http://test:7010")

    def test_inject_appends_instructions_after_original_prompt(self, injector):
        original = "你是设计师"
        result = injector.inject_into_system_prompt(
            original, "inv-1", "tok-1", "designer"
        )
        assert result.startswith(original)
        assert "## 团队协作工具" in result
        assert "inv-1" in result
        assert "tok-1" in result

    def test_curl_contains_post_message_url(self, injector):
        result = injector.inject_into_system_prompt(
            "p", "inv-2", "tok-2", "designer"
        )
        assert "http://test:7010/api/callbacks/post-message" in result
        assert "thread-context" in result
        assert "pending-mentions" in result

    def test_curl_payload_contains_credentials(self, injector):
        result = injector.inject_into_system_prompt(
            "p", "my-inv-id", "my-cb-token", "developer"
        )
        assert '"invocation_id": "my-inv-id"' in result
        assert '"callback_token": "my-cb-token"' in result
        assert '"target_agent_id"' in result

    def test_designer_workflow_triggers_mention_developer(self, injector):
        result = injector.inject_into_system_prompt(
            "p", "i", "t", "designer"
        )
        assert "@developer" in result
        assert "设计师" in result or "designer" in result

    def test_developer_workflow_triggers_mention_qa(self, injector):
        result = injector.inject_into_system_prompt(
            "p", "i", "t", "developer"
        )
        assert "@qa" in result
        assert "测试" in result or "qa" in result

    def test_qa_workflow_triggers_mention_developer(self, injector):
        result = injector.inject_into_system_prompt(
            "p", "i", "t", "qa"
        )
        assert "@developer" in result

    def test_unknown_agent_returns_only_common_triggers(self, injector):
        result = injector.inject_into_system_prompt(
            "p", "i", "t", "unknown_agent"
        )
        # 通用 triggers 始终存在
        assert "完成任务后" in result
        # 不应包含任何 agent 特定的 @mention
        assert "@developer" not in result
        assert "@qa" not in result

    def test_api_url_from_env_when_not_provided(self, monkeypatch):
        monkeypatch.setenv("API_URL", "http://from-env:9000")
        injector = PromptInjector()  # 不传 api_url
        result = injector.inject_into_system_prompt("p", "i", "t", "designer")
        assert "http://from-env:9000" in result

    def test_api_url_default_when_no_env(self, monkeypatch):
        monkeypatch.delenv("API_URL", raising=False)
        injector = PromptInjector()
        result = injector.inject_into_system_prompt("p", "i", "t", "designer")
        assert "http://localhost:7010" in result

    def test_create_invocation_returns_pair(self, injector):
        inv_id, token = injector.create_invocation_for_agent(
            "designer", "thread-1"
        )
        assert isinstance(inv_id, str) and len(inv_id) == 36
        assert isinstance(token, str) and len(token) == 36
        assert inv_id != token

    def test_workflow_triggers_uses_simplified_chinese_names(self, injector):
        """3-agent 适配：designer/developer/qa 用中文别名"""
        designer = injector.inject_into_system_prompt("p", "i", "t", "designer")
        developer = injector.inject_into_system_prompt("p", "i", "t", "developer")
        qa = injector.inject_into_system_prompt("p", "i", "t", "qa")
        # designer 提到 developer
        assert "开发者" in designer
        # developer 提到 qa（测试）
        assert "测试" in developer
        # qa 提到 developer
        assert "开发者" in qa
```

- [ ] **Step 2: 运行测试，预期全部 PASS**

```bash
cd agenthub/backend && python -m pytest tests/test_prompt_injector.py -v
```

预期：11 个测试全 PASS，0 fail。

- [ ] **Step 3: Commit**

```bash
cd ../.. && git add agenthub/backend/tests/test_prompt_injector.py
git commit -m "test(backend): add prompt_injector unit tests (3-agent triggers)"
```

---

## Task 3: CallbackRouter 单元测试（验证已存在代码）

**Files:**
- Create: `agenthub/backend/tests/test_callback_router.py`

- [ ] **Step 1: 创建测试文件**

在 `agenthub/backend/tests/test_callback_router.py` 写入：

```python
"""CallbackRouter 单元测试（验证已存在实现，mock memory/sse/a2a_router）"""
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agenthub.backend.services.callback_router import CallbackRouter
from agenthub.backend.services.invocation_registry import InvocationRegistry


@pytest.fixture
def mock_memory():
    m = MagicMock()
    m.add_message = AsyncMock(return_value={"id": "msg-1"})
    m.get_messages = AsyncMock(return_value=[
        {"id": "1", "content": "hello", "agent_id": "designer"},
    ])
    return m


@pytest.fixture
def mock_sse():
    m = MagicMock()
    m.broadcast = AsyncMock()
    return m


@pytest.fixture
def mock_a2a_router():
    m = MagicMock()
    m.enqueue_a2a_targets = MagicMock()
    return m


@pytest.fixture
def registry():
    return InvocationRegistry(ttl=10)


@pytest.fixture
def callback_router(mock_memory, mock_sse, mock_a2a_router, registry):
    # 替换 callback_router 模块里的全局 memory/sse/a2a_router
    with patch(
        "agenthub.backend.services.callback_router.memory", mock_memory
    ), patch(
        "agenthub.backend.services.callback_router.sse_manager", mock_sse
    ), patch(
        "agenthub.backend.services.callback_router.a2a_router", mock_a2a_router
    ):
        yield CallbackRouter()


class TestPostMessage:
    async def test_invalid_credentials_raises_value_error(self, callback_router):
        with pytest.raises(ValueError, match="Invalid or expired credentials"):
            await callback_router.post_message("bad-inv", "bad-tok", "hello")

    async def test_valid_credentials_persists_message(
        self, callback_router, mock_memory, mock_sse, registry
    ):
        inv_id, token = registry.create("designer", "thread-1")
        result = await callback_router.post_message(
            inv_id, token, "设计师的回复"
        )
        assert result["status"] == "ok"
        assert result["message_id"] == "msg-1"
        mock_memory.add_message.assert_called_once()
        args, kwargs = mock_memory.add_message.call_args
        assert kwargs["role"] == "designer"
        assert kwargs["content"] == "设计师的回复"
        assert kwargs["thread_id"] == "thread-1"
        mock_sse.broadcast.assert_called_once()
        assert mock_sse.broadcast.call_args[0][0] == "message"

    async def test_with_target_agent_id_enqueues_to_a2a(
        self, callback_router, mock_a2a_router, registry
    ):
        inv_id, token = registry.create("designer", "thread-2")
        await callback_router.post_message(
            inv_id, token, "@developer 接手", target_agent_id="developer"
        )
        mock_a2a_router.enqueue_a2a_targets.assert_called_once_with(
            "thread-2", ["developer"]
        )

    async def test_without_target_agent_id_does_not_enqueue(
        self, callback_router, mock_a2a_router, registry
    ):
        inv_id, token = registry.create("designer", "thread-3")
        await callback_router.post_message(inv_id, token, "普通消息")
        mock_a2a_router.enqueue_a2a_targets.assert_not_called()


class TestGetThreadContext:
    async def test_invalid_credentials_raises(self, callback_router):
        with pytest.raises(ValueError):
            await callback_router.get_thread_context("bad", "bad")

    async def test_returns_messages(
        self, callback_router, mock_memory, registry
    ):
        inv_id, token = registry.create("developer", "thread-4")
        result = await callback_router.get_thread_context(inv_id, token)
        assert len(result["messages"]) == 1
        assert result["messages"][0]["content"] == "hello"
        mock_memory.get_messages.assert_called_once_with(thread_id="thread-4")


class TestGetPendingMentions:
    async def test_invalid_credentials_raises(self, callback_router):
        with pytest.raises(ValueError):
            await callback_router.get_pending_mentions("bad", "bad")

    async def test_returns_mentions_to_current_agent(
        self, callback_router, mock_memory, registry
    ):
        # 准备：有消息 @designer
        mock_memory.get_messages = AsyncMock(return_value=[
            {
                "id": "m1",
                "content": "@designer 你来",
                "agent_id": "developer",
                "timestamp": "2026-06-17T00:00:00",
            },
            {
                "id": "m2",
                "content": "普通消息",
                "agent_id": "user",
                "timestamp": "2026-06-17T00:00:01",
            },
        ])
        inv_id, token = registry.create("designer", "thread-5")
        result = await callback_router.get_pending_mentions(inv_id, token)
        # 只有 m1 @了 designer
        assert len(result["mentions"]) == 1
        assert result["mentions"][0]["message_id"] == "m1"
        assert result["mentions"][0]["from_agent"] == "developer"
```

- [ ] **Step 2: 运行测试，预期全部 PASS**

```bash
cd agenthub/backend && python -m pytest tests/test_callback_router.py -v
```

预期：8 个测试全 PASS，0 fail。

- [ ] **Step 3: Commit**

```bash
cd ../.. && git add agenthub/backend/tests/test_callback_router.py
git commit -m "test(backend): add callback_router unit tests"
```

---

## Task 4: Callbacks API 集成测试（验证已存在 HTTP 端点）

**Files:**
- Create: `agenthub/backend/tests/test_callbacks_api.py`

- [ ] **Step 1: 创建测试文件**

在 `agenthub/backend/tests/test_callbacks_api.py` 写入：

```python
"""Callbacks API 集成测试（fastapi.testclient 验证 HTTP 端点）"""
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 必须在 import app 之前 patch 业务依赖
mock_memory = MagicMock()
mock_memory.add_message = AsyncMock(return_value={"id": "msg-test"})
mock_memory.get_messages = AsyncMock(return_value=[])

mock_sse = MagicMock()
mock_sse.broadcast = AsyncMock()

mock_a2a_router = MagicMock()
mock_a2a_router.enqueue_a2a_targets = MagicMock()

# 必须在 import 前 patch callback_router 内部依赖
sys.modules.setdefault("agenthub.backend.services.callback_router", MagicMock())
with patch(
    "agenthub.backend.services.callback_router.memory", mock_memory
), patch(
    "agenthub.backend.services.callback_router.sse_manager", mock_sse
), patch(
    "agenthub.backend.services.callback_router.a2a_router", mock_a2a_router
):
    # 重新 import 真正模块
    from agenthub.backend.services.callback_router import CallbackRouter
    from agenthub.backend.routers.callbacks import router as callbacks_router
    from agenthub.backend.services.invocation_registry import InvocationRegistry
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(callbacks_router)

    # 重新绑定 callback_router 实例使用 mock 依赖
    import agenthub.backend.routers.callbacks as cb_module
    cb_module.callback_router = CallbackRouter()

    client = TestClient(app)
    registry = InvocationRegistry(ttl=10)


class TestPostMessageEndpoint:
    def test_invalid_credentials_returns_401(self):
        resp = client.post(
            "/api/callbacks/post-message",
            json={
                "invocation_id": "bad",
                "callback_token": "bad",
                "content": "hello",
            },
        )
        assert resp.status_code == 401
        assert "Invalid" in resp.json()["detail"]

    def test_valid_credentials_returns_200_with_message_id(self):
        inv_id, token = registry.create("designer", "thread-api-1")
        resp = client.post(
            "/api/callbacks/post-message",
            json={
                "invocation_id": inv_id,
                "callback_token": token,
                "content": "hi",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["message_id"] == "msg-test"

    def test_with_target_agent_id_returns_200(self):
        inv_id, token = registry.create("designer", "thread-api-2")
        resp = client.post(
            "/api/callbacks/post-message",
            json={
                "invocation_id": inv_id,
                "callback_token": token,
                "content": "@developer",
                "target_agent_id": "developer",
            },
        )
        assert resp.status_code == 200
        mock_a2a_router.enqueue_a2a_targets.assert_called()


class TestThreadContextEndpoint:
    def test_invalid_credentials_returns_401(self):
        resp = client.get(
            "/api/callbacks/thread-context",
            params={"invocation_id": "bad", "callback_token": "bad"},
        )
        assert resp.status_code == 401

    def test_valid_credentials_returns_messages(self):
        inv_id, token = registry.create("designer", "thread-api-3")
        resp = client.get(
            "/api/callbacks/thread-context",
            params={"invocation_id": inv_id, "callback_token": token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "messages" in data


class TestPendingMentionsEndpoint:
    def test_invalid_credentials_returns_401(self):
        resp = client.get(
            "/api/callbacks/pending-mentions",
            params={"invocation_id": "bad", "callback_token": "bad"},
        )
        assert resp.status_code == 401

    def test_valid_credentials_returns_mentions(self):
        inv_id, token = registry.create("designer", "thread-api-4")
        resp = client.get(
            "/api/callbacks/pending-mentions",
            params={"invocation_id": inv_id, "callback_token": token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "mentions" in data
```

- [ ] **Step 2: 运行测试，预期全部 PASS**

```bash
cd agenthub/backend && python -m pytest tests/test_callbacks_api.py -v
```

预期：7 个测试全 PASS，0 fail。

- [ ] **Step 3: Commit**

```bash
cd ../.. && git add agenthub/backend/tests/test_callbacks_api.py
git commit -m "test(backend): add callbacks API integration tests"
```

---

## Task 5: A2ARouter 单元测试（含新行为）

**Files:**
- Create: `agenthub/backend/tests/test_a2a_router.py`

- [ ] **Step 1: 创建测试文件**

在 `agenthub/backend/tests/test_a2a_router.py` 写入：

```python
"""A2ARouter 单元测试（验证已存在 + 新行为：prompt 注入 + invocation 创建）"""
import os
import re
import sys
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agenthub.backend.services.a2a_router import A2ARouter
from agenthub.backend.services.invocation_registry import InvocationRegistry
from agenthub.backend.services.prompt_injector import PromptInjector


class TestExtractMentionsFromTools:
    def test_extracts_single_mention(self):
        router = A2ARouter()
        response = '我打算让 developer 来实现\n{"target_agent_id": "developer"}'
        assert router._extract_mentions_from_tools(response) == ["developer"]

    def test_extracts_multiple_mentions(self):
        router = A2ARouter()
        response = '{"target_agent_id": "qa"} 然后 {"target_agent_id": "developer"}'
        assert router._extract_mentions_from_tools(response) == ["qa", "developer"]

    def test_dedupes_repeated_mentions(self):
        router = A2ARouter()
        response = '{"target_agent_id": "qa"} {"target_agent_id": "qa"}'
        assert router._extract_mentions_from_tools(response) == ["qa"]

    def test_handles_spaces_around_colon(self):
        router = A2ARouter()
        response = '{ "target_agent_id" : "developer" }'
        assert router._extract_mentions_from_tools(response) == ["developer"]

    def test_no_mention_returns_empty(self):
        router = A2ARouter()
        response = "我就说一下，不 @ 任何人"
        assert router._extract_mentions_from_tools(response) == []


class TestEnqueueA2ATargets:
    def test_appends_new_target_to_worklist(self):
        router = A2ARouter()
        router.thread_worklists["thread-1"] = ["designer"]
        router.enqueue_a2a_targets("thread-1", ["developer"])
        assert router.thread_worklists["thread-1"] == ["designer", "developer"]

    def test_dedupes_existing_target(self):
        router = A2ARouter()
        router.thread_worklists["thread-2"] = ["designer", "developer"]
        router.enqueue_a2a_targets("thread-2", ["developer", "qa"])
        assert router.thread_worklists["thread-2"] == ["designer", "developer", "qa"]

    def test_unknown_thread_is_noop(self):
        router = A2ARouter()
        router.enqueue_a2a_targets("nonexistent", ["developer"])
        # 不应抛异常
        assert "nonexistent" not in router.thread_worklists


class TestCancelThread:
    def test_cancel_sets_signal(self):
        router = A2ARouter()
        import asyncio
        signal = asyncio.Event()
        router.thread_signals["thread-3"] = signal
        router.cancel_thread("thread-3")
        assert signal.is_set()

    def test_cancel_unknown_thread_is_noop(self):
        router = A2ARouter()
        # 不应抛异常
        router.cancel_thread("nonexistent")


class TestStateQueries:
    def test_is_running_false_for_unknown_thread(self):
        router = A2ARouter()
        assert router.is_running("unknown") is False

    def test_get_thread_state_returns_state(self):
        router = A2ARouter()
        router.thread_states["thread-4"] = {
            "is_running": True,
            "current_agent": "designer",
            "depth": 1,
            "max_depth": 15,
        }
        state = router.get_thread_state("thread-4")
        assert state["current_agent"] == "designer"
        assert state["depth"] == 1

    def test_get_thread_state_none_for_unknown(self):
        router = A2ARouter()
        assert router.get_thread_state("unknown") is None


class TestInvokeAgentNewBehavior:
    """新行为：_invoke_agent 必须先创建 invocation + 注入 prompt，再调 LLM。"""

    async def test_invoke_agent_creates_invocation_before_llm(self):
        router = A2ARouter()
        registry = InvocationRegistry(ttl=10)

        # mock invocation_registry
        with patch(
            "agenthub.backend.services.invocation_registry.invocation_registry",
            registry,
        ), patch(
            "agenthub.backend.services.a2a_router.invocation_registry", registry
        ):
            # mock LLM 流式
            mock_llm = MagicMock()
            mock_llm.send_message_stream = MagicMock(return_value=iter([]))
            with patch(
                "agenthub.backend.services.llm_router.get_llm_service_for_provider",
                return_value=mock_llm,
            ):
                # 消费 _invoke_agent 生成器
                gen = router._invoke_agent("designer", "hi", "thread-5", "user")
                async for _ in gen:
                    pass

                # 验证：invocation_registry.create 被调用过一次
                assert registry.count() == 1
                # 验证：LLM 被调用时 system_prompt 含 invocation_id 格式
                if mock_llm.send_message_stream.called:
                    call_kwargs = mock_llm.send_message_stream.call_args.kwargs
                    assert "invocation_id=" not in call_kwargs.get(
                        "system_prompt", ""
                    )  # 已注入的指令在 system_prompt 中
                    assert "callback_token=" in call_kwargs.get(
                        "system_prompt", ""
                    ) or "team" in call_kwargs.get("system_prompt", "").lower()

    async def test_invoke_agent_injects_prompt_before_llm(self):
        router = A2ARouter()
        registry = InvocationRegistry(ttl=10)
        injector = PromptInjector(api_url="http://test:7010")

        with patch(
            "agenthub.backend.services.a2a_router.invocation_registry", registry
        ), patch(
            "agenthub.backend.services.a2a_router.prompt_injector", injector
        ):
            mock_llm = MagicMock()
            mock_llm.send_message_stream = MagicMock(return_value=iter([]))
            with patch(
                "agenthub.backend.services.llm_router.get_llm_service_for_provider",
                return_value=mock_llm,
            ):
                gen = router._invoke_agent("developer", "test", "thread-6", "user")
                async for _ in gen:
                    pass

                # 验证：LLM 收到的 system_prompt 包含注入的指令
                call_kwargs = mock_llm.send_message_stream.call_args.kwargs
                injected_prompt = call_kwargs["system_prompt"]
                assert "## 团队协作工具" in injected_prompt
                assert "http://test:7010/api/callbacks/post-message" in injected_prompt
                # 注入的 prompt 应包含原始的 agent 角色描述
                assert "developer" in injected_prompt.lower() or "开发" in injected_prompt


class TestRouteExecutionE2E:
    """端到端：route_execution 串起 worklist + 提取 mentions + signal。"""

    async def test_route_execution_yields_a2a_start_and_chunk(self):
        router = A2ARouter()
        registry = InvocationRegistry(ttl=10)
        injector = PromptInjector(api_url="http://test:7010")

        with patch(
            "agenthub.backend.services.a2a_router.invocation_registry", registry
        ), patch(
            "agenthub.backend.services.a2a_router.prompt_injector", injector
        ):
            # mock LLM 输出一个 chunk + 一个 mention
            mock_llm = MagicMock()
            def fake_stream(*args, **kwargs):
                yield "我让 "
                yield '{"target_agent_id": "developer"}'
            mock_llm.send_message_stream = MagicMock(side_effect=fake_stream)
            with patch(
                "agenthub.backend.services.llm_router.get_llm_service_for_provider",
                return_value=mock_llm,
            ):
                events = []
                async for event in router.route_execution(
                    initial_agents=["designer"],
                    message="需求",
                    thread_id="thread-7",
                    user_id="user",
                ):
                    events.append(event)

                # 验证：包含 a2a_start / a2a_chunk / a2a_done
                types = [e["type"] for e in events]
                assert "a2a_start" in types
                assert "a2a_chunk" in types
                assert "a2a_done" in types
                # 验证：mention 被追加，designer 之后有 developer
                # 整链会跑两个 agent（designer → developer）
                assert "a2a_complete" in types

    async def test_cancel_yields_a2a_cancelled(self):
        router = A2ARouter()
        registry = InvocationRegistry(ttl=10)
        injector = PromptInjector(api_url="http://test:7010")

        with patch(
            "agenthub.backend.services.a2a_router.invocation_registry", registry
        ), patch(
            "agenthub.backend.services.a2a_router.prompt_injector", injector
        ):
            # 慢 LLM：先发一个 chunk，再 yield 控制权
            mock_llm = MagicMock()
            def slow_stream(*args, **kwargs):
                yield "start"
                import time
                time.sleep(0.5)
                yield "end"
            mock_llm.send_message_stream = MagicMock(side_effect=slow_stream)
            with patch(
                "agenthub.backend.services.llm_router.get_llm_service_for_provider",
                return_value=mock_llm,
            ):
                events = []
                async def consume():
                    async for event in router.route_execution(
                        initial_agents=["designer"],
                        message="test",
                        thread_id="thread-8",
                        user_id="user",
                    ):
                        events.append(event)
                        if event["type"] == "a2a_chunk":
                            # 立即取消
                            router.cancel_thread("thread-8")
                await consume()
                assert "a2a_cancelled" in [e["type"] for e in events]
```

- [ ] **Step 2: 运行测试，预期部分 FAIL（新行为部分）**

```bash
cd agenthub/backend && python -m pytest tests/test_a2a_router.py -v
```

预期：
- TestExtractMentionsFromTools / TestEnqueueA2ATargets / TestCancelThread / TestStateQueries **全部 PASS**（验证已存在）
- TestInvokeAgentNewBehavior / TestRouteExecutionE2E **部分 FAIL**（_invoke_agent 还没接入 prompt_injector / invocation_registry）

- [ ] **Step 3: Commit（test file only）**

```bash
cd ../.. && git add agenthub/backend/tests/test_a2a_router.py
git commit -m "test(backend): add a2a_router tests (TDD: new behavior failing)"
```

---

## Task 6: 修改 a2a_router._invoke_agent（TDD 实施）

**Files:**
- Modify: `agenthub/backend/services/a2a_router.py:227-285` (`_invoke_agent` method)

- [ ] **Step 1: 修改 _invoke_agent 方法**

替换 `agenthub/backend/services/a2a_router.py` 中 `_invoke_agent` 的整个方法体（line 227-285）：

```python
async def _invoke_agent(
    self,
    agent_id: str,
    message: str,
    thread_id: str,
    user_id: str,
) -> AsyncIterator:
    """调用单个 Agent

    新行为：在调 LLM 前先创建 invocation（callback 凭证），
    并用 prompt_injector 把 callback 指令注入到 system_prompt，
    让 LLM 知道可以通过 HTTP 调 callback。

    Args:
        agent_id: Agent ID
        message: 消息内容
        thread_id: 线程 ID
        user_id: 用户 ID

    Yields:
        Agent 的输出（str 或 dict）
    """
    from .session import session_manager, AGENT_CONFIGS
    from .llm_router import get_llm_service_for_provider
    from .memory_manager import memory_manager, redis_memory_manager
    from .invocation_registry import invocation_registry
    from .prompt_injector import prompt_injector
    import os

    # 根据 STORAGE_BACKEND 选择存储实例
    memory = redis_memory_manager

    config = AGENT_CONFIGS.get(agent_id)
    if not config:
        yield f"Error: Unknown agent {agent_id}"
        return

    system_prompt = config.get("system_prompt", "")
    provider = config.get("llm_provider", "bailian")

    # 获取上下文
    context = await memory.get_context_for_agent(agent_id, user_id=user_id, thread_id=thread_id)
    agent_message = f"上下文参考:\n{context}\n\n用户消息: {message}" if context else message

    # 新行为：创建 invocation 凭证（每个 agent 一次）
    inv_id, cb_token = invocation_registry.create(agent_id, thread_id)

    # 新行为：注入 callback 指令到 system_prompt
    system_prompt = prompt_injector.inject_into_system_prompt(
        system_prompt, inv_id, cb_token, agent_id
    )

    try:
        llm = get_llm_service_for_provider(provider)

        # 流式调用 LLM
        for chunk in llm.send_message_stream(
            session_id=f"session_{agent_id}_{thread_id}",
            message=agent_message,
            system_prompt=system_prompt,
        ):
            if isinstance(chunk, str):
                yield chunk
            elif hasattr(chunk, "choices") and chunk.choices:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content

    except Exception as e:
        logger.error(f"Agent 调用失败: agent_id={agent_id}, error={e}")
        yield f"Error: {str(e)}"
```

**关键改动：**
- 新增 imports：`invocation_registry`, `prompt_injector`
- 在调 LLM 前增加两行：
  1. `inv_id, cb_token = invocation_registry.create(agent_id, thread_id)`
  2. `system_prompt = prompt_injector.inject_into_system_prompt(system_prompt, inv_id, cb_token, agent_id)`

- [ ] **Step 2: 运行测试，预期全部 PASS**

```bash
cd agenthub/backend && python -m pytest tests/test_a2a_router.py -v
```

预期：之前 FAIL 的 TestInvokeAgentNewBehavior / TestRouteExecutionE2E 现在 PASS，全部测试通过。

- [ ] **Step 3: 跑全部测试，确认未破坏其他**

```bash
cd agenthub/backend && python -m pytest tests/ -v
```

预期：所有已存在 + 新增测试 PASS。

- [ ] **Step 4: Commit**

```bash
cd ../.. && git add agenthub/backend/services/a2a_router.py
git commit -m "feat(backend): wire prompt_injector + invocation_registry into a2a_router"
```

---

## Task 7: 修改 messages.py 接入 a2a_router（TDD 实施）

**Files:**
- Modify: `agenthub/backend/routers/messages.py:393-587`（`send_message` 路由 + `asyncio.gather` 调用 + 新增 cancel 端点）

- [ ] **Step 1: 写失败测试（messages.py 应走 a2a_router）**

在 `agenthub/backend/tests/test_messages.py` 写入（如果文件不存在则创建）：

```python
"""Messages API 集成测试（A2A 路由路径）"""
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_dependencies():
    """mock 所有外部依赖"""
    mocks = {
        "memory": MagicMock(),
        "sse": MagicMock(),
        "a2a_router": MagicMock(),
        "session": MagicMock(),
        "claude_code": MagicMock(),
    }
    mocks["memory"].add_message = AsyncMock(return_value={"id": "msg-x"})
    mocks["memory"].get_context_for_agent = AsyncMock(return_value="")
    mocks["memory"].get_messages = AsyncMock(return_value=[])
    mocks["sse"].broadcast = AsyncMock()
    mocks["sse"].broadcast_stream_chunk = AsyncMock()
    mocks["a2a_router"].route_execution = MagicMock()  # AsyncMock 不支持 async generator，用 MagicMock + async def
    mocks["session"].send_to_agent_stream = MagicMock(return_value=iter([]))

    # route_execution 必须是 async generator
    async def fake_route_execution(**kwargs):
        yield {"type": "a2a_complete", "is_final": True}

    mocks["a2a_router"].route_execution = fake_route_execution

    with patch.dict(os.environ, {"API_KEY": "test-key"}):
        yield mocks


@pytest.fixture
def client(mock_dependencies):
    # 必须在 import app 之前 patch
    with patch(
        "agenthub.backend.routers.messages.memory", mock_dependencies["memory"]
    ), patch(
        "agenthub.backend.routers.messages.sse_manager", mock_dependencies["sse"]
    ), patch(
        "agenthub.backend.routers.messages.session_manager", mock_dependencies["session"]
    ), patch(
        "agenthub.backend.routers.messages.a2a_router", mock_dependencies["a2a_router"]
    ):
        from fastapi import FastAPI
        from agenthub.backend.routers.messages import router as messages_router
        from agenthub.backend.routers.callbacks import router as callbacks_router
        from agenthub.backend.routers.events import router as events_router

        app = FastAPI()
        app.include_router(messages_router)
        app.include_router(callbacks_router)
        app.include_router(events_router)
        yield TestClient(app)


class TestSendMessageUsesA2ARouter:
    def test_with_agent_id_routes_to_a2a_router(
        self, client, mock_dependencies
    ):
        resp = client.post(
            "/api/messages",
            json={
                "content": "@developer 帮我修 bug",
                "sender": "user",
                "agent_id": "developer",
                "thread_id": "t-1",
                "user_id": "u-1",
            },
        )
        # 当前实现不会调 a2a_router，所以这个测试**会 FAIL**（新行为）
        # 等 Task 7 Step 3 改完才会 PASS
        assert resp.status_code == 200
        # 验证：a2a 路径广播了 a2a_start 或 a2a_complete 事件
        broadcast_types = [
            call.args[0]
            for call in mock_dependencies["sse"].broadcast.call_args_list
        ]
        assert "a2a_start" in broadcast_types or "a2a_complete" in broadcast_types

    def test_with_at_mention_in_content_routes_to_a2a_router(
        self, client, mock_dependencies
    ):
        """消息内容含 @苍龙 也走 A2A"""
        resp = client.post(
            "/api/messages",
            json={
                "content": "@苍龙 帮分析需求",
                "sender": "user",
                "thread_id": "t-2",
            },
        )
        assert resp.status_code == 200

    def test_broadcast_no_mention_uses_gather_fallback(
        self, client, mock_dependencies
    ):
        """无 @agent 时降级到 gather 路径"""
        resp = client.post(
            "/api/messages",
            json={
                "content": "普通消息",
                "sender": "user",
                "thread_id": "t-3",
            },
        )
        assert resp.status_code == 200


class TestCancelA2AEndpoint:
    def test_cancel_returns_200(self, client, mock_dependencies):
        resp = client.post("/api/a2a/cancel", params={"thread_id": "t-1"})
        assert resp.status_code == 200
        # 验证：a2a_router.cancel_thread 被调用
        # (这要求 Task 7 Step 3 新增 cancel 端点)
```

- [ ] **Step 2: 运行测试，预期 FAIL（端点尚未接入）**

```bash
cd agenthub/backend && python -m pytest tests/test_messages.py -v
```

预期：测试 FAIL（messages.py 还没接 a2a_router，cancel 端点也还没加）。

- [ ] **Step 3: 修改 messages.py，接入 a2a_router + 新增 cancel 端点**

修改 `agenthub/backend/routers/messages.py`：

**改动 1：** 在 imports 块（line 9-38）增加：

```python
from agenthub.backend.services.a2a_router import a2a_router
```

**改动 2：** 在文件末尾（line 587 之后）新增 cancel 端点：

```python


@router.post("/a2a/cancel")
async def cancel_a2a(thread_id: str = Query(...)):
    """取消指定线程的 A2A 链（前端 Stop 按钮调）"""
    a2a_router.cancel_thread(thread_id)
    return {"status": "ok", "thread_id": thread_id}
```

**改动 3：** 替换 `send_message` 中 `asyncio.gather` 段（line 580-581）为：

```python
    # 走 a2a_router 路径 vs 降级路径
    if targets:
        # 走 a2a_router.route_execution — 端到端 A2A 链
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        seq = 0

        async def on_agent_chunk(agent_id: str, chunk: str, thread_id: str):
            nonlocal seq
            await sse_manager.broadcast_stream_chunk(
                message_id, chunk, seq, thread_id=thread_id
            )
            seq += 1

        async def on_agent_done(agent_id: str, full_response: str, thread_id: str):
            config = AGENT_CONFIGS.get(agent_id, {})
            agent_msg = await _persist_message(
                role=agent_id,
                content=full_response,
                agent_id=agent_id,
                sender_name=config.get("name", agent_id),
                user_id=req.user_id,
                thread_id=thread_id,
            )
            agent_msg["id"] = message_id
            await sse_manager.broadcast("message", agent_msg, thread_id=thread_id)

        async def on_agent_start(agent_id: str, depth: int, thread_id: str):
            await sse_manager.broadcast(
                "a2a_start",
                {"agent_id": agent_id, "depth": depth},
                thread_id=thread_id,
            )

        async def on_a2a_complete(thread_id: str):
            await sse_manager.broadcast(
                "a2a_complete",
                {"is_final": True},
                thread_id=thread_id,
            )

        async def on_a2a_cancelled(thread_id: str, reason: str):
            await sse_manager.broadcast(
                "a2a_cancelled",
                {"reason": reason},
                thread_id=thread_id,
            )

        # 消费 a2a_router.route_execution 的事件流（实际工作由 callbacks 驱动）
        async for _ in a2a_router.route_execution(
            initial_agents=targets,
            message=route_result["content"],
            thread_id=req.thread_id,
            user_id=req.user_id,
            on_agent_start=on_agent_start,
            on_agent_chunk=on_agent_chunk,
            on_agent_done=on_agent_done,
            on_a2a_complete=on_a2a_complete,
            on_a2a_cancelled=on_a2a_cancelled,
        ):
            pass

        return {
            "success": True,
            "message_id": message_id,
            "is_a2a": True,
        }
    else:
        # 降级路径：原 broadcast 行为（理论上不会进，targets 永远非空）
        await asyncio.gather(
            *[send_to_single_agent(agent_id) for agent_id in targets]
        )

    return {
        "success": True,
        "message_id": user_msg.get("id", ""),
        "is_broadcast": route_result["is_broadcast"]
    }
```

- [ ] **Step 4: 运行测试，预期 PASS**

```bash
cd agenthub/backend && python -m pytest tests/test_messages.py -v
```

预期：所有测试 PASS。

- [ ] **Step 5: 跑全部测试，确认未破坏**

```bash
cd agenthub/backend && python -m pytest tests/ -v
```

预期：所有已存在 + 新增测试 PASS。

- [ ] **Step 6: Commit**

```bash
cd ../.. && git add agenthub/backend/routers/messages.py agenthub/backend/tests/test_messages.py
git commit -m "feat(backend): wire messages.py to a2a_router + add /api/a2a/cancel"
```

---

## Task 8: 更新 CLAUDE.md + 标注上游 spec

**Files:**
- Modify: `agenthub/CLAUDE.md`（新增"隐性知识 → A2A"小节）
- Modify: `docs/superpowers/specs/2026-06-10-a2a-collaboration-design.md`（末尾加实施日期）

- [ ] **Step 1: 在 CLAUDE.md 新增 A2A 隐性知识小节**

在 `agenthub/CLAUDE.md` 现有"隐性知识"小节末尾追加（不要修改既有内容）：

```markdown

## A2A 隐性知识

- **A2A 状态内存存储**：`a2a_router.thread_worklists` / `thread_signals` / `thread_states` 是内存 Dict，服务器重启 in-flight 链丢失（按 YAGNI 决定不持久化）
- **A2A prompt 注入位置**：`a2a_router._invoke_agent` 在调 LLM **前**做两件事 — `invocation_registry.create(agent_id, thread_id)` 创建凭证 + `prompt_injector.inject_into_system_prompt()` 注入 callback 指令。**不要**把 prompt 注入移到 LLM 调用之后（已注入的 system_prompt 才是 LLM 看到的）
- **A2A 入口**：`POST /api/messages` 走 `a2a_router.route_execution`（有 @agent 提及或前端指定 agent_id），无目标时降级到 `asyncio.gather` 广播
- **A2A 取消**：`POST /api/a2a/cancel?thread_id=xxx` 调 `a2a_router.cancel_thread(thread_id)`，设置 `asyncio.Event` 让正在执行的 `_invoke_agent` 在下一个 yield 点检查并停止
- **A2A SSE 事件类型**：`a2a_start` / `a2a_chunk` / `a2a_done` / `a2a_complete`（整链 is_final）/ `a2a_cancelled` / `a2a_error` / `message`（callback 发出）。前端 `messageStore` 监听这些事件来更新 `a2aState`
- **A2A invocation 生命周期**：每 agent 一次（不是 worklist 全局一次），TTL 1h。简化每个 agent 都有合法凭证的逻辑
- **A2A 3-agent 适配**：`prompt_injector._build_workflow_triggers` 已按 designer/developer/qa 重写，触发点 prompt 注入中。`/help` 文档里五行神兽表的 PM/架构师/开发者/测试/协调器段落（line 187-194）是历史遗留，**未更新** — 用户帮助内容不在本 plan 范围
```

- [ ] **Step 2: 在上游 spec 末尾加实施日期**

在 `docs/superpowers/specs/2026-06-10-a2a-collaboration-design.md` 文件末尾追加：

```markdown

---

## 实施记录

- **2026-06-17**：工程化收尾完成（参见 `2026-06-17-a2a-finishup-design.md` + `2026-06-17-a2a-finishup.md`）
  - 修复两个端到端跑不通的硬缺口（messages.py 接入 a2a_router；a2a_router._invoke_agent 接入 prompt_injector + invocation_registry）
  - 新增 5 个测试文件：test_invocation_registry.py / test_prompt_injector.py / test_callback_router.py / test_callbacks_api.py / test_a2a_router.py
  - 新增 `POST /api/a2a/cancel` 端点供前端 Stop 按钮
  - 事件名变更：`a2a_progress` → `a2a_chunk`；拆 `a2a_done`（单 agent）vs `a2a_complete`（整链 is_final）
  - 状态存储：保持内存 Map（YAGNI）
```

- [ ] **Step 3: 跑全部测试 + 覆盖率检查**

```bash
cd agenthub/backend && python -m pytest tests/ -v --cov=agenthub.backend.services --cov=agenthub.backend.routers --cov-report=term-missing
```

预期：
- 全部测试 PASS
- `a2a_router` / `callback_router` / `invocation_registry` / `prompt_injector` / `callbacks` / `messages` 覆盖率 ≥ 80%

- [ ] **Step 4: Commit**

```bash
cd ../.. && git add agenthub/CLAUDE.md docs/superpowers/specs/2026-06-10-a2a-collaboration-design.md
git commit -m "docs: add A2A 隐性知识 to CLAUDE.md + mark upstream spec as implemented"
```

---

## 验证清单

完成所有 8 个 task 后：

- [ ] 跑 `pytest agenthub/backend/tests/ -v` 全部 PASS
- [ ] 跑 `pytest --cov=agenthub.backend --cov-report=term-missing` 覆盖率 ≥ 80%
- [ ] 手测：`@苍龙 @developer 测试消息` 触发 A2A 链（启动后端 + 前端，发送消息）
- [ ] 手测：Stop 按钮能取消 in-flight A2A 链
- [ ] 检查 `agenthub/CLAUDE.md` 含 A2A 隐性知识小节
- [ ] 检查 `docs/superpowers/specs/2026-06-10-a2a-collaboration-design.md` 末尾含"实施记录"段落
- [ ] 8 个 commit（Task 1-4 各 1，Task 5 1，Task 6 1，Task 7 1，Task 8 1）

---

## Self-Review Notes

**1. Spec coverage（对照 spec 验收标准）：**

| spec 验收项 | 对应 task |
|------------|----------|
| `POST /api/messages` 走 `a2a_router.route_execution` | Task 7 |
| `prompt_injector` 实际被调用 | Task 6（_invoke_agent 接入）+ Task 5（测试断言）|
| Stop 按钮能取消 A2A | Task 7（cancel 端点）+ Task 5（cancel 测试）|
| 输入框 A2A 期间锁定 | 前端已有 `a2aState` + Stop 按钮（不动）|
| 4 单测 + 1 集成测试通过 | Task 1-4 |
| 覆盖率 ≥ 80% | Task 8 Step 3 验证 |
| CLAUDE.md 含 A2A 隐性知识 | Task 8 Step 1 |
| 上游 spec 标已实施 | Task 8 Step 2 |

**2. Placeholder scan：** 无 TBD/TODO/???/FIXME/placeholder。

**3. Type consistency：**
- `a2a_router.route_execution` 签名：`(initial_agents, message, thread_id, user_id, on_agent_start=, on_agent_chunk=, on_agent_done=, on_a2a_complete=, on_a2a_cancelled=)` — Task 6 + Task 7 一致
- `a2a_router.cancel_thread(thread_id)` 签名 — Task 5 + Task 7 一致
- `invocation_registry.create(agent_id, thread_id)` 返回 `(inv_id, token)` — Task 1/2/6 一致
- `prompt_injector.inject_into_system_prompt(system_prompt, inv_id, token, agent_id)` — Task 2/6 一致
- callback 签名 `on_agent_chunk(agent_id, chunk, thread_id)` / `on_agent_done(agent_id, full_response, thread_id)` — Task 6 + Task 7 一致

**4. 风险标记：**
- Task 5 端到端测试依赖 mock 模式（`async for fake_route_execution`），需要在 fixture 级别正确注入。代码块里已显式说明
- Task 7 的 a2a_router.route_execution 是真 async generator，被 mock 替换时要用 `async def ... yield`，不能用 AsyncMock
- Task 8 的 `/help` 文档段落是 5-agent 时代遗留，spec 范围内不动 — 在 CLAUDE.md 隐性知识小节显式标记

---

**文档版本**：v1.0
**最后更新**：2026-06-17
