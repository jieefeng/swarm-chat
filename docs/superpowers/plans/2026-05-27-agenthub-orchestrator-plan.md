# AgentHub Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Add Orchestrator-driven multi-agent task decomposition, DAG scheduling, streaming, HITL, Diff viewer, and TaskPanel to AgentHub.

**Architecture:** Orchestrator Agent (LLM) decomposes user requests into DAG tasks. TaskManager schedules tasks via topological sort. 5 Agent roles (PM/Architect/Developer/QA/Orchestrator) execute tasks through a unified adapter layer. Results stream to frontend via extended SSE protocol. Frontend renders TaskPanel, ClarificationCard, and DiffViewer inline in chat.

**Tech Stack:** FastAPI, Next.js 15, Zustand, SSE, Pydantic, react-diff-viewer-continued, Tailwind v4

---

## File Structure

### New Files
- `agenthub/backend/models/task.py` - Task, TaskStatus, OrchestratorOutput Pydantic models
- `agenthub/backend/services/agent_adapter.py` - IAgentAdapter protocol + BailianAdapter
- `agenthub/backend/services/task_manager.py` - TaskManager state machine + DAG scheduler
- `agenthub/backend/services/orchestrator.py` - OrchestratorAgent LLM task decomposition
- `agenthub/backend/services/shared_context.py` - SharedContext blackboard for inter-agent state
- `agenthub/backend/routers/tasks.py` - Tasks API router
- `agenthub/frontend/lib/stores/taskStore.ts` - Zustand store for tasks
- `agenthub/frontend/components/chat/TaskPanel.tsx` - Inline task progress panel
- `agenthub/frontend/components/chat/ClarificationCard.tsx` - HITL clarification card
- `agenthub/frontend/components/chat/DiffViewer.tsx` - Code diff viewer

### Modified Files
- `agenthub/backend/services/session.py` - Add 3 new agent configs
- `agenthub/backend/services/sse_manager.py` - Add new SSE event broadcast methods
- `agenthub/backend/routers/messages.py` - Integrate Orchestrator flow
- `agenthub/frontend/lib/types.ts` - Add Task, SSE event types
- `agenthub/frontend/lib/sse.ts` - Route new SSE event types
- `agenthub/frontend/lib/hooks/useChatStream.ts` - Handle new events
- `agenthub/frontend/components/chat/MessageBubble.tsx` - Render new message types
- `agenthub/frontend/app/page.tsx` - Wire up taskStore

---

### Task 1: Backend Agent Config Expansion

**Files:**
- Modify: `agenthub/backend/services/session.py`

- [ ] **Step 1: Read current AGENT_CONFIGS in session.py**

Read `agenthub/backend/services/session.py` to understand the existing PM and Architect config structure.

- [ ] **Step 2: Add developer, qa, orchestrator agent configs**

Add three new entries to `AGENT_CONFIGS`:

```python
"developer": {
    "name": "开发者",
    "role": "developer",
    "system_prompt": "你是一位资深全栈开发者。根据架构师的设计方案，编写高质量的代码实现。遵循 SOLID 原则，编写清晰、可维护的代码。输出代码时使用 markdown 代码块，标明文件路径和语言。"
},
"qa": {
    "name": "QA工程师",
    "role": "qa",
    "system_prompt": "你是一位专业的 QA 工程师。审查开发者提交的代码，验证功能正确性、边界情况和代码质量。输出验证报告，标明通过/失败及原因。"
},
"orchestrator": {
    "name": "协调器",
    "role": "orchestrator",
    "system_prompt": "你是任务协调器。分析用户需求，将其拆解为可执行的任务列表，以 JSON 格式输出。每个任务包含 title, description, assigned_to, depends_on, priority 字段。如果需求不清晰，设置 requires_clarification=true 并提供 clarification_question。"
}
```

- [ ] **Step 3: Run existing tests to verify no breakage**

Run: `cd agenthub/backend && python -m pytest -v`
Expected: All existing tests pass.

- [ ] **Step 4: Commit**

```bash
git add agenthub/backend/services/session.py
git commit -m "feat: add developer, qa, orchestrator agent configs"
```

---

### Task 2: Backend Agent Adapter Layer

**Files:**
- Create: `agenthub/backend/services/agent_adapter.py`
- Read: `agenthub/backend/services/llm_router.py`
- Read: `agenthub/backend/services/bailian.py`

- [ ] **Step 1: Read existing LLM service implementation**

Read `agenthub/backend/services/llm_router.py` and `agenthub/backend/services/bailian.py` to understand the current LLM call patterns.

- [ ] **Step 2: Create agent_adapter.py with IAgentAdapter protocol**

```python
"""统一 Agent 适配器层 - 屏蔽不同 LLM 提供商差异"""
from typing import Protocol, AsyncIterator
from .llm_router import get_llm_service


class IAgentAdapter(Protocol):
    """Agent 适配器协议"""
    async def send_message(self, system_prompt: str, user_message: str, history: list[dict] | None = None) -> str:
        """同步发送消息，返回完整回复"""
        ...

    async def send_message_stream(self, system_prompt: str, user_message: str, history: list[dict] | None = None) -> AsyncIterator[str]:
        """流式发送消息，yield 文本片段"""
        ...


class BailianAdapter:
    """百炼 API 适配器"""

    def __init__(self):
        self._service = get_llm_service()

    async def send_message(self, system_prompt: str, user_message: str, history: list[dict] | None = None) -> str:
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        return await self._service.send_message_with_retry(system_prompt, messages)

    async def send_message_stream(self, system_prompt: str, user_message: str, history: list[dict] | None = None) -> AsyncIterator[str]:
        """流式调用 - 当前百炼服务不支持流式，回退为完整返回后逐块发送"""
        full_response = await self.send_message(system_prompt, user_message, history)
        # 模拟流式：按段落切分
        for chunk in full_response.split("\n\n"):
            yield chunk + "\n\n"
            import asyncio
            await asyncio.sleep(0.05)


def get_agent_adapter() -> IAgentAdapter:
    """获取 Agent 适配器实例"""
    return BailianAdapter()
```

- [ ] **Step 3: Create test file for agent_adapter**

Create `agenthub/backend/tests/test_agent_adapter.py`:

```python
"""Agent 适配器测试"""
import pytest
from unittest.mock import AsyncMock, patch
from services.agent_adapter import BailianAdapter


@pytest.mark.asyncio
async def test_send_message_returns_string():
    adapter = BailianAdapter()
    with patch.object(adapter._service, 'send_message_with_retry', new_callable=AsyncMock, return_value="test response"):
        result = await adapter.send_message("system", "hello")
        assert result == "test response"


@pytest.mark.asyncio
async def test_send_message_stream_yields_chunks():
    adapter = BailianAdapter()
    with patch.object(adapter._service, 'send_message_with_retry', new_callable=AsyncMock, return_value="chunk1\n\nchunk2\n\n"):
        chunks = []
        async for chunk in adapter.send_message_stream("system", "hello"):
            chunks.append(chunk)
        assert len(chunks) >= 1
        assert "".join(chunks).strip() == "chunk1\n\nchunk2"
```

- [ ] **Step 4: Run tests**

Run: `cd agenthub/backend && python -m pytest tests/test_agent_adapter.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agenthub/backend/services/agent_adapter.py agenthub/backend/tests/test_agent_adapter.py
git commit -m "feat: add unified agent adapter layer"
```

---

### Task 3: Backend Task Models (Pydantic)

**Files:**
- Create: `agenthub/backend/models/__init__.py`
- Create: `agenthub/backend/models/task.py`

- [ ] **Step 1: Create models package**

Create `agenthub/backend/models/__init__.py`:

```python
"""数据模型包"""
```

- [ ] **Step 2: Create task.py with all Pydantic models**

```python
"""任务相关数据模型"""
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    REVIEWING = "reviewing"
    DONE = "done"
    FAILED = "failed"
    ESCALATE = "escalate"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class TaskCreate(BaseModel):
    title: str
    description: str
    assigned_to: str  # agent id: pm/architect/developer/qa
    depends_on: list[str] = Field(default_factory=list)
    priority: str = "medium"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    assigned_to: str
    depends_on: list[str] = Field(default_factory=list)  # task IDs (UUID)
    priority: str = "medium"
    status: TaskStatus = TaskStatus.PENDING
    result: str | None = None
    retry_count: int = 0

    def can_transition_to(self, new_status: TaskStatus) -> bool:
        """检查状态转换是否合法"""
        transitions = {
            TaskStatus.PENDING: {TaskStatus.RUNNING, TaskStatus.CANCELLED, TaskStatus.SKIPPED},
            TaskStatus.RUNNING: {TaskStatus.REVIEWING, TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.CANCELLED},
            TaskStatus.REVIEWING: {TaskStatus.DONE, TaskStatus.FAILED},
            TaskStatus.FAILED: {TaskStatus.RUNNING, TaskStatus.ESCALATE, TaskStatus.SKIPPED},
            TaskStatus.ESCALATE: {TaskStatus.RUNNING, TaskStatus.CANCELLED},
            TaskStatus.DONE: set(),
            TaskStatus.CANCELLED: set(),
            TaskStatus.SKIPPED: set(),
        }
        return new_status in transitions.get(self.status, set())


class UncertainPoint(BaseModel):
    question: str
    options: list[str]


class OrchestratorOutput(BaseModel):
    analysis: str
    tasks: list[TaskCreate]
    requires_clarification: bool = False
    clarification_question: str | None = None
    uncertain_points: list[UncertainPoint] = Field(default_factory=list)
```

- [ ] **Step 3: Create test for task models**

Create `agenthub/backend/tests/test_task_models.py`:

```python
"""任务模型测试"""
import pytest
from models.task import Task, TaskStatus, OrchestratorOutput


def test_task_default_status():
    task = Task(title="Test", description="Desc", assigned_to="pm")
    assert task.status == TaskStatus.PENDING


def test_task_valid_transition_pending_to_running():
    task = Task(title="Test", description="Desc", assigned_to="pm")
    assert task.can_transition_to(TaskStatus.RUNNING) is True


def test_task_invalid_transition_done_to_running():
    task = Task(title="Test", description="Desc", assigned_to="pm", status=TaskStatus.DONE)
    assert task.can_transition_to(TaskStatus.RUNNING) is False


def test_orchestrator_output_validation():
    output = OrchestratorOutput(
        analysis="Test analysis",
        tasks=[{"title": "T1", "description": "D1", "assigned_to": "pm"}]
    )
    assert len(output.tasks) == 1
    assert output.requires_clarification is False


def test_orchestrator_output_clarification():
    output = OrchestratorOutput(
        analysis="Uncertain",
        tasks=[],
        requires_clarification=True,
        clarification_question="Which framework?",
        uncertain_points=[{"question": "Framework?", "options": ["React", "Vue"]}]
    )
    assert output.requires_clarification is True
    assert len(output.uncertain_points) == 1
```

- [ ] **Step 4: Run tests**

Run: `cd agenthub/backend && python -m pytest tests/test_task_models.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add agenthub/backend/models/
git commit -m "feat: add Task and OrchestratorOutput Pydantic models"
```

---

### Task 4: Backend TaskManager State Machine

**Files:**
- Create: `agenthub/backend/services/task_manager.py`
- Read: `agenthub/backend/models/task.py`

- [ ] **Step 1: Read task models**

Read `agenthub/backend/models/task.py` to understand Task, TaskStatus, TaskCreate, OrchestratorOutput.

- [ ] **Step 2: Create task_manager.py**

```python
"""TaskManager - 任务状态机 + DAG 调度"""
import asyncio
from collections import defaultdict, deque
from models.task import Task, TaskCreate, TaskStatus, OrchestratorOutput
from services.agent_adapter import get_agent_adapter, IAgentAdapter
from services.sse_manager import sse_manager


MAX_RETRY = 3


class TaskManager:
    """管理任务生命周期、DAG 调度、执行"""

    def __init__(self):
        self._tasks: dict[str, Task] = {}  # id -> Task
        self._title_to_id: dict[str, str] = {}  # title -> task id (for depends_on resolution)
        self._lock = asyncio.Lock()

    def get_tasks(self) -> list[Task]:
        return list(self._tasks.values())

    def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def add_tasks_from_orchestrator(self, output: OrchestratorOutput) -> list[Task]:
        """从 Orchestrator 输出创建任务，解析 depends_on 为 UUID"""
        tasks = []
        # First pass: create tasks and build title->id mapping
        for tc in output.tasks:
            task = Task(
                title=tc.title,
                description=tc.description,
                assigned_to=tc.assigned_to,
                depends_on=[],  # resolve in second pass
                priority=tc.priority,
            )
            self._tasks[task.id] = task
            self._title_to_id[tc.title] = task.id
            tasks.append(task)
        # Second pass: resolve depends_on
        for tc, task in zip(output.tasks, tasks):
            for dep_title in tc.depends_on:
                dep_id = self._title_to_id.get(dep_title)
                if dep_id:
                    task.depends_on.append(dep_id)
        return tasks

    def get_ready_tasks(self) -> list[Task]:
        """获取可执行的任务（所有依赖已完成）"""
        ready = []
        for task in self._tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            all_deps_done = all(
                self._tasks[dep_id].status == TaskStatus.DONE
                for dep_id in task.depends_on
                if dep_id in self._tasks
            )
            if all_deps_done:
                ready.append(task)
        return ready

    def has_cycle(self) -> bool:
        """检测循环依赖（Kahn 算法）"""
        in_degree = defaultdict(int)
        graph = defaultdict(list)
        for task in self._tasks.values():
            if task.id not in in_degree:
                in_degree[task.id] = 0
            for dep_id in task.depends_on:
                graph[dep_id].append(task.id)
                in_degree[task.id] += 1
        queue = deque(tid for tid, deg in in_degree.items() if deg == 0)
        visited = 0
        while queue:
            tid = queue.popleft()
            visited += 1
            for neighbor in graph[tid]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        return visited != len(self._tasks)

    async def execute_task(self, task: Task, adapter: IAgentAdapter | None = None) -> None:
        """执行单个任务"""
        if adapter is None:
            adapter = get_agent_adapter()
        async with self._lock:
            task.status = TaskStatus.RUNNING
        await sse_manager.broadcast_task_update(task.id, task.status.value, task.title)
        try:
            # Get agent config for system prompt
            from services.session import AGENT_CONFIGS
            agent_config = AGENT_CONFIGS.get(task.assigned_to, {})
            system_prompt = agent_config.get("system_prompt", "你是一个 AI 助手。")
            result = await adapter.send_message(system_prompt, task.description)
            async with self._lock:
                task.result = result
                task.status = TaskStatus.DONE
            await sse_manager.broadcast_task_update(task.id, "done", task.title)
        except Exception as e:
            async with self._lock:
                task.retry_count += 1
                if task.retry_count >= MAX_RETRY:
                    task.status = TaskStatus.ESCALATE
                else:
                    task.status = TaskStatus.FAILED
            await sse_manager.broadcast_task_update(task.id, task.status.value, task.title)

    async def execute_ready_tasks(self, adapter: IAgentAdapter | None = None) -> None:
        """并行执行所有就绪任务"""
        ready = self.get_ready_tasks()
        if not ready:
            return
        await asyncio.gather(*(self.execute_task(t, adapter) for t in ready))

    async def run_all(self, adapter: IAgentAdapter | None = None) -> None:
        """执行所有任务直到完成或卡住"""
        if self.has_cycle():
            # 降级：按创建顺序串行执行
            for task in self._tasks.values():
                if task.status == TaskStatus.PENDING:
                    await self.execute_task(task, adapter)
            return
        # DAG 执行
        while True:
            ready = self.get_ready_tasks()
            if not ready:
                break
            await self.execute_ready_tasks(adapter)

    def reset(self):
        """重置所有任务状态"""
        for task in self._tasks.values():
            task.status = TaskStatus.PENDING
            task.result = None
            task.retry_count = 0
```

- [ ] **Step 3: Create test for task_manager**

Create `agenthub/backend/tests/test_task_manager.py`:

```python
"""TaskManager 测试"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from models.task import Task, TaskCreate, TaskStatus, OrchestratorOutput
from services.task_manager import TaskManager


def test_add_tasks_from_orchestrator():
    tm = TaskManager()
    output = OrchestratorOutput(
        analysis="Test",
        tasks=[
            TaskCreate(title="T1", description="D1", assigned_to="pm"),
            TaskCreate(title="T2", description="D2", assigned_to="dev", depends_on=["T1"]),
        ]
    )
    tasks = tm.add_tasks_from_orchestrator(output)
    assert len(tasks) == 2
    assert tasks[1].depends_on == [tasks[0].id]


def test_get_ready_tasks():
    tm = TaskManager()
    output = OrchestratorOutput(
        analysis="Test",
        tasks=[
            TaskCreate(title="T1", description="D1", assigned_to="pm"),
            TaskCreate(title="T2", description="D2", assigned_to="dev", depends_on=["T1"]),
        ]
    )
    tm.add_tasks_from_orchestrator(output)
    ready = tm.get_ready_tasks()
    assert len(ready) == 1
    assert ready[0].title == "T1"


def test_has_cycle_detection():
    tm = TaskManager()
    t1 = Task(title="T1", description="D1", assigned_to="pm")
    t2 = Task(title="T2", description="D2", assigned_to="pm", depends_on=[t1.id])
    t1.depends_on = [t2.id]  # circular
    tm._tasks = {t1.id: t1, t2.id: t2}
    assert tm.has_cycle() is True


def test_no_cycle():
    tm = TaskManager()
    t1 = Task(title="T1", description="D1", assigned_to="pm")
    t2 = Task(title="T2", description="D2", assigned_to="pm", depends_on=[t1.id])
    tm._tasks = {t1.id: t1, t2.id: t2}
    assert tm.has_cycle() is False


@pytest.mark.asyncio
async def test_execute_task_success():
    tm = TaskManager()
    task = Task(title="T1", description="D1", assigned_to="pm")
    tm._tasks[task.id] = task
    mock_adapter = AsyncMock()
    mock_adapter.send_message = AsyncMock(return_value="done")
    with patch("services.task_manager.sse_manager") as mock_sse, \
         patch("services.task_manager.AGENT_CONFIGS", {"pm": {"system_prompt": "test"}}):
        mock_sse.broadcast_task_update = AsyncMock()
        await tm.execute_task(task, mock_adapter)
    assert task.status == TaskStatus.DONE
    assert task.result == "done"
```

- [ ] **Step 4: Run tests**

Run: `cd agenthub/backend && python -m pytest tests/test_task_manager.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add agenthub/backend/services/task_manager.py agenthub/backend/tests/test_task_manager.py
git commit -m "feat: add TaskManager with state machine and DAG scheduling"
```

---

### Task 5: Backend Orchestrator Agent

**Files:**
- Create: `agenthub/backend/services/orchestrator.py`
- Read: `agenthub/backend/models/task.py`
- Read: `agenthub/backend/services/agent_adapter.py`

- [ ] **Step 1: Create orchestrator.py**

```python
"""Orchestrator Agent - LLM 驱动任务拆解 + Self-Correction"""
import json
import logging
from models.task import OrchestratorOutput
from services.agent_adapter import get_agent_adapter, IAgentAdapter

logger = logging.getLogger(__name__)

ORCHESTRATOR_SYSTEM_PROMPT = """你是任务协调器。分析用户需求，将其拆解为可执行的任务列表。

你必须以 JSON 格式输出，schema 如下：
{
  "analysis": "对用户需求的理解和分析",
  "tasks": [
    {
      "title": "任务标题（必须唯一）",
      "description": "任务详细描述",
      "assigned_to": "Agent ID: pm/architect/developer/qa",
      "depends_on": ["依赖的任务标题"],
      "priority": "high/medium/low"
    }
  ],
  "requires_clarification": false,
  "clarification_question": null,
  "uncertain_points": []
}

规则：
1. 任务标题必须唯一
2. assigned_to 必须是 pm/architect/developer/qa 之一
3. depends_on 引用其他任务的 title
4. 如果需求不清晰，设置 requires_clarification=true
5. 只输出 JSON，不要输出其他内容"""

MAX_SELF_CORRECTION_RETRIES = 2


class OrchestratorAgent:
    """Orchestrator Agent - 负责任务拆解"""

    def __init__(self, adapter: IAgentAdapter | None = None):
        self._adapter = adapter or get_agent_adapter()

    async def decompose(self, user_message: str) -> OrchestratorOutput:
        """拆解用户需求为任务列表，内置 Self-Correction"""
        error_context = ""
        for attempt in range(MAX_SELF_CORRECTION_RETRIES + 1):
            prompt = user_message
            if error_context:
                prompt = f"{user_message}\n\n[系统提示：上次输出有误，请修正。错误信息：{error_context}]"
            raw = await self._adapter.send_message(ORCHESTRATOR_SYSTEM_PROMPT, prompt)
            try:
                # 提取 JSON（兼容 markdown code block）
                json_str = raw.strip()
                if json_str.startswith("```"):
                    lines = json_str.split("\n")
                    json_str = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
                output = OrchestratorOutput.model_validate_json(json_str)
                return output
            except Exception as e:
                logger.warning(f"Orchestrator output validation failed (attempt {attempt+1}): {e}")
                error_context = str(e)
        # 降级：返回广播模式
        return OrchestratorOutput(
            analysis=f"需求拆解失败，降级为广播模式。原始需求：{user_message}",
            tasks=[],
            requires_clarification=False,
        )
```

- [ ] **Step 2: Create test for orchestrator**

Create `agenthub/backend/tests/test_orchestrator.py`:

```python
"""Orchestrator Agent 测试"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock
from models.task import OrchestratorOutput
from services.orchestrator import OrchestratorAgent


@pytest.mark.asyncio
async def test_decompose_valid_json():
    mock_adapter = AsyncMock()
    mock_adapter.send_message = AsyncMock(return_value='''```json
{
  "analysis": "用户要建一个登录页面",
  "tasks": [
    {"title": "设计登录页面", "description": "设计UI", "assigned_to": "pm", "depends_on": [], "priority": "high"},
    {"title": "实现登录API", "description": "写后端", "assigned_to": "developer", "depends_on": ["设计登录页面"], "priority": "high"}
  ],
  "requires_clarification": false,
  "clarification_question": null,
  "uncertain_points": []
}
```''')
    agent = OrchestratorAgent(adapter=mock_adapter)
    output = await agent.decompose("我要一个登录页面")
    assert isinstance(output, OrchestratorOutput)
    assert len(output.tasks) == 2
    assert output.tasks[1].depends_on == ["设计登录页面"]


@pytest.mark.asyncio
async def test_decompose_self_correction():
    mock_adapter = AsyncMock()
    mock_adapter.send_message = AsyncMock(side_effect=[
        "invalid json here",
        '{"analysis":"ok","tasks":[{"title":"T1","description":"D1","assigned_to":"pm"}],"requires_clarification":false,"clarification_question":null,"uncertain_points":[]}'
    ])
    agent = OrchestratorAgent(adapter=mock_adapter)
    output = await agent.decompose("test")
    assert len(output.tasks) == 1


@pytest.mark.asyncio
async def test_decompose_fallback_on_repeated_failure():
    mock_adapter = AsyncMock()
    mock_adapter.send_message = AsyncMock(return_value="always invalid")
    agent = OrchestratorAgent(adapter=mock_adapter)
    output = await agent.decompose("test")
    assert output.tasks == []
    assert "降级" in output.analysis
```

- [ ] **Step 3: Run tests**

Run: `cd agenthub/backend && python -m pytest tests/test_orchestrator.py -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add agenthub/backend/services/orchestrator.py agenthub/backend/tests/test_orchestrator.py
git commit -m "feat: add OrchestratorAgent with LLM decomposition and self-correction"
```

---

### Task 6: Backend SharedContext

**Files:**
- Create: `agenthub/backend/services/shared_context.py`

- [ ] **Step 1: Create shared_context.py**

```python
"""SharedContext - Agent 间共享状态（黑板模式）"""
import asyncio


class SharedContext:
    """Agent 间共享上下文，支持写锁"""

    def __init__(self):
        self._data: dict[str, object] = {}
        self._task_locks: dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def get(self, key: str) -> object | None:
        return self._data.get(key)

    async def set(self, key: str, value: object, task_id: str | None = None) -> None:
        """写入共享状态，task_id 用于细粒度锁"""
        if task_id:
            async with self._global_lock:
                if task_id not in self._task_locks:
                    self._task_locks[task_id] = asyncio.Lock()
            async with self._task_locks[task_id]:
                self._data[key] = value
        else:
            async with self._global_lock:
                self._data[key] = value

    async def get_task_artifacts(self, task_id: str) -> dict[str, object]:
        """获取某任务的所有产出物"""
        prefix = f"task:{task_id}:"
        return {k[len(prefix):]: v for k, v in self._data.items() if k.startswith(prefix)}

    async def set_task_artifact(self, task_id: str, artifact_key: str, value: object) -> None:
        """设置任务产出物"""
        await self.set(f"task:{task_id}:{artifact_key}", value, task_id=task_id)

    def clear(self):
        self._data.clear()
        self._task_locks.clear()


# 全局单例
shared_context = SharedContext()
```

- [ ] **Step 2: Create test for shared_context**

Create `agenthub/backend/tests/test_shared_context.py`:

```python
"""SharedContext 测试"""
import pytest
import pytest_asyncio
from services.shared_context import SharedContext


@pytest.mark.asyncio
async def test_set_and_get():
    ctx = SharedContext()
    await ctx.set("key1", "value1")
    assert await ctx.get("key1") == "value1"


@pytest.mark.asyncio
async def test_get_missing_key():
    ctx = SharedContext()
    assert await ctx.get("nonexistent") is None


@pytest.mark.asyncio
async def test_task_artifacts():
    ctx = SharedContext()
    await ctx.set_task_artifact("task1", "code", "print('hello')")
    await ctx.set_task_artifact("task1", "review", "LGTM")
    artifacts = await ctx.get_task_artifacts("task1")
    assert artifacts == {"code": "print('hello')", "review": "LGTM"}


@pytest.mark.asyncio
async def test_task_isolation():
    ctx = SharedContext()
    await ctx.set_task_artifact("task1", "code", "a=1")
    await ctx.set_task_artifact("task2", "code", "b=2")
    a1 = await ctx.get_task_artifacts("task1")
    a2 = await ctx.get_task_artifacts("task2")
    assert a1["code"] == "a=1"
    assert a2["code"] == "b=2"
```

- [ ] **Step 3: Run tests**

Run: `cd agenthub/backend && python -m pytest tests/test_shared_context.py -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add agenthub/backend/services/shared_context.py agenthub/backend/tests/test_shared_context.py
git commit -m "feat: add SharedContext blackboard for inter-agent state"
```

---

### Task 7: Backend SSE Protocol Extension

**Files:**
- Modify: `agenthub/backend/services/sse_manager.py`

- [ ] **Step 1: Read current sse_manager.py**

Read `agenthub/backend/services/sse_manager.py` to understand existing broadcast() and subscribe() methods.

- [ ] **Step 2: Add new broadcast methods**

Add these methods to the `SSEManager` class:

```python
async def broadcast_stream_chunk(self, message_id: str, chunk: str, seq: int) -> None:
    """广播流式文本片段"""
    event = {
        "event": "stream_chunk",
        "data": {
            "message_id": message_id,
            "chunk": chunk,
            "seq": seq,
        }
    }
    await self.broadcast(event)

async def broadcast_task_created(self, task_id: str, title: str, assigned_to: str) -> None:
    """广播任务创建事件"""
    event = {
        "event": "task_created",
        "data": {
            "task_id": task_id,
            "title": title,
            "assigned_to": assigned_to,
        }
    }
    await self.broadcast(event)

async def broadcast_task_update(self, task_id: str, status: str, title: str) -> None:
    """广播任务状态变更"""
    event = {
        "event": "task_update",
        "data": {
            "task_id": task_id,
            "status": status,
            "title": title,
        }
    }
    await self.broadcast(event)

async def broadcast_clarification_request(self, message_id: str, question: str, options: list[str]) -> None:
    """广播 HITL 澄清请求"""
    event = {
        "event": "clarification_request",
        "data": {
            "message_id": message_id,
            "question": question,
            "options": options,
        }
    }
    await self.broadcast(event)

async def broadcast_artifact_diff(self, task_id: str, file_path: str, old_content: str, new_content: str) -> None:
    """广播代码 Diff"""
    event = {
        "event": "artifact_diff",
        "data": {
            "task_id": task_id,
            "file_path": file_path,
            "old_content": old_content,
            "new_content": new_content,
        }
    }
    await self.broadcast(event)
```

- [ ] **Step 3: Verify existing tests still pass**

Run: `cd agenthub/backend && python -m pytest -v`
Expected: All existing tests pass.

- [ ] **Step 4: Commit**

```bash
git add agenthub/backend/services/sse_manager.py
git commit -m "feat: extend SSE protocol with task, stream, diff, and clarification events"
```

---

### Task 8: Backend Tasks API Router

**Files:**
- Create: `agenthub/backend/routers/tasks.py`
- Modify: `agenthub/backend/main.py`

- [ ] **Step 1: Create tasks.py router**

```python
"""任务 API 路由"""
from fastapi import APIRouter, HTTPException
from models.task import TaskStatus
from services.task_manager import TaskManager

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# 全局 TaskManager 实例
task_manager = TaskManager()


@router.get("")
async def get_tasks():
    """获取所有任务"""
    tasks = task_manager.get_tasks()
    return {"tasks": [t.model_dump() for t in tasks]}


@router.get("/{task_id}")
async def get_task(task_id: str):
    """获取单个任务"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.model_dump()


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    """取消任务"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if not task.can_transition_to(TaskStatus.CANCELLED):
        raise HTTPException(status_code=400, detail=f"Cannot cancel task in {task.status} state")
    task.status = TaskStatus.CANCELLED
    return {"status": "cancelled"}
```

- [ ] **Step 2: Register router in main.py**

Read `agenthub/backend/main.py`, then add:

```python
from routers.tasks import router as tasks_router
app.include_router(tasks_router)
```

- [ ] **Step 3: Run backend to verify**

Run: `cd agenthub/backend && python main.py` (verify startup without errors)
Expected: Server starts, `/api/tasks` endpoint accessible.

- [ ] **Step 4: Commit**

```bash
git add agenthub/backend/routers/tasks.py agenthub/backend/main.py
git commit -m "feat: add tasks API router with get and cancel endpoints"
```

---

### Task 9: Frontend Types and taskStore

**Files:**
- Modify: `agenthub/frontend/lib/types.ts`
- Create: `agenthub/frontend/lib/stores/taskStore.ts`

- [ ] **Step 1: Read current types.ts**

Read `agenthub/frontend/lib/types.ts` to understand existing type definitions.

- [ ] **Step 2: Add new types to types.ts**

Append to the file:

```typescript
// Task types
export type TaskStatus = 'pending' | 'running' | 'reviewing' | 'done' | 'failed' | 'escalate' | 'cancelled' | 'skipped'

export interface Task {
  id: string
  title: string
  description: string
  assigned_to: string
  depends_on: string[]
  priority: string
  status: TaskStatus
  result: string | null
  retry_count: number
}

// SSE extended event types
export interface StreamChunkEvent {
  message_id: string
  chunk: string
  seq: number
}

export interface TaskCreatedEvent {
  task_id: string
  title: string
  assigned_to: string
}

export interface TaskUpdateEvent {
  task_id: string
  status: TaskStatus
  title: string
}

export interface ClarificationRequestEvent {
  message_id: string
  question: string
  options: string[]
}

export interface ArtifactDiffEvent {
  task_id: string
  file_path: string
  old_content: string
  new_content: string
}
```

- [ ] **Step 3: Create taskStore.ts**

```typescript
import { create } from 'zustand'
import type { Task, TaskStatus } from '@/lib/types'

interface TaskStore {
  tasks: Task[]
  setTasks: (tasks: Task[]) => void
  addTask: (task: Task) => void
  updateTaskStatus: (taskId: string, status: TaskStatus) => void
  getTasksByStatus: (status: TaskStatus) => Task[]
}

export const useTaskStore = create<TaskStore>((set, get) => ({
  tasks: [],
  setTasks: (tasks) => set({ tasks }),
  addTask: (task) => set((state) => ({ tasks: [...state.tasks, task] })),
  updateTaskStatus: (taskId, status) =>
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.id === taskId ? { ...t, status } : t
      ),
    })),
  getTasksByStatus: (status) => get().tasks.filter((t) => t.status === status),
}))
```

- [ ] **Step 4: Run frontend check**

Run: `cd agenthub/frontend && npm run check`
Expected: No type errors.

- [ ] **Step 5: Commit**

```bash
git add agenthub/frontend/lib/types.ts agenthub/frontend/lib/stores/taskStore.ts
git commit -m "feat: add Task types and taskStore for frontend"
```

---

### Task 10: Frontend SSE Event Routing

**Files:**
- Modify: `agenthub/frontend/lib/sse.ts`
- Modify: `agenthub/frontend/lib/hooks/useChatStream.ts`

- [ ] **Step 1: Read current sse.ts and useChatStream.ts**

Read both files to understand existing SSE connection and event handling patterns.

- [ ] **Step 2: Add event type constants and handler type to sse.ts**

Add to `agenthub/frontend/lib/sse.ts`:

```typescript
// New SSE event types
export const SSE_EVENT_STREAM_CHUNK = 'stream_chunk'
export const SSE_EVENT_TASK_CREATED = 'task_created'
export const SSE_EVENT_TASK_UPDATE = 'task_update'
export const SSE_EVENT_CLARIFICATION_REQUEST = 'clarification_request'
export const SSE_EVENT_ARTIFACT_DIFF = 'artifact_diff'
```

Update `SSEMessage` interface to include `event` field if not present.

Update the SSE connection handler to route events by type:

```typescript
// In the SSE message handler, add routing for new event types
if (parsed.event === SSE_EVENT_STREAM_CHUNK) {
  onStreamChunk?.(parsed.data)
} else if (parsed.event === SSE_EVENT_TASK_CREATED) {
  onTaskCreated?.(parsed.data)
} else if (parsed.event === SSE_EVENT_TASK_UPDATE) {
  onTaskUpdate?.(parsed.data)
} else if (parsed.event === SSE_EVENT_CLARIFICATION_REQUEST) {
  onClarification?.(parsed.data)
} else if (parsed.event === SSE_EVENT_ARTIFACT_DIFF) {
  onDiff?.(parsed.data)
}
```

- [ ] **Step 3: Update useChatStream.ts to handle new events**

Add handlers for task and clarification events:

```typescript
import { useTaskStore } from '@/lib/stores/taskStore'

// In the hook:
const { addTask, updateTaskStatus } = useTaskStore()

// In SSE event handlers:
onTaskCreated: (data) => {
  addTask({
    id: data.task_id,
    title: data.title,
    assigned_to: data.assigned_to,
    status: 'pending',
    // ... other defaults
  })
},
onTaskUpdate: (data) => {
  updateTaskStatus(data.task_id, data.status)
},
onClarification: (data) => {
  // Add clarification as a special message type
  addMessage({
    id: data.message_id,
    type: 'clarification',
    content: data.question,
    sender: 'orchestrator',
    // ... options stored in metadata
  })
},
```

- [ ] **Step 4: Run frontend check**

Run: `cd agenthub/frontend && npm run check`
Expected: No type errors.

- [ ] **Step 5: Commit**

```bash
git add agenthub/frontend/lib/sse.ts agenthub/frontend/lib/hooks/useChatStream.ts
git commit -m "feat: route new SSE event types (task, stream, clarification, diff)"
```

---

### Task 11: Frontend TaskPanel Component

**Files:**
- Create: `agenthub/frontend/components/chat/TaskPanel.tsx`

- [ ] **Step 1: Create TaskPanel.tsx**

```tsx
'use client'

import type { Task } from '@/lib/types'

interface TaskPanelProps {
  tasks: Task[]
}

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  pending: { label: '等待中', color: 'bg-gray-100 text-gray-600' },
  running: { label: '执行中', color: 'bg-blue-100 text-blue-700' },
  reviewing: { label: '审查中', color: 'bg-yellow-100 text-yellow-700' },
  done: { label: '已完成', color: 'bg-green-100 text-green-700' },
  failed: { label: '失败', color: 'bg-red-100 text-red-700' },
  escalate: { label: '需介入', color: 'bg-orange-100 text-orange-700' },
  cancelled: { label: '已取消', color: 'bg-gray-100 text-gray-400' },
  skipped: { label: '已跳过', color: 'bg-gray-100 text-gray-400' },
}

export function TaskPanel({ tasks }: TaskPanelProps) {
  const completedCount = tasks.filter((t) => t.status === 'done').length
  const progress = tasks.length > 0 ? (completedCount / tasks.length) * 100 : 0

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-800">任务进度</h3>
        <span className="text-xs text-gray-500">
          {completedCount}/{tasks.length}
        </span>
      </div>
      {/* Progress bar */}
      <div className="mb-4 h-2 w-full overflow-hidden rounded-full bg-gray-100">
        <div
          className="h-full rounded-full bg-blue-500 transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
      {/* Task list */}
      <div className="space-y-2">
        {tasks.map((task) => {
          const config = STATUS_CONFIG[task.status] ?? STATUS_CONFIG.pending
          return (
            <div key={task.id} className="flex items-center gap-2 text-sm">
              <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${config.color}`}>
                {config.label}
              </span>
              <span className="truncate text-gray-700">{task.title}</span>
              <span className="ml-auto text-xs text-gray-400">{task.assigned_to}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Run frontend check**

Run: `cd agenthub/frontend && npm run check`
Expected: No type errors.

- [ ] **Step 3: Commit**

```bash
git add agenthub/frontend/components/chat/TaskPanel.tsx
git commit -m "feat: add TaskPanel component for inline task progress"
```

---

### Task 12: Frontend ClarificationCard Component

**Files:**
- Create: `agenthub/frontend/components/chat/ClarificationCard.tsx`

- [ ] **Step 1: Create ClarificationCard.tsx**

```tsx
'use client'

interface ClarificationCardProps {
  question: string
  options: string[]
  onSelect: (option: string) => void
}

export function ClarificationCard({ question, options, onSelect }: ClarificationCardProps) {
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 shadow-sm">
      <div className="mb-3 flex items-center gap-2">
        <span className="text-amber-600">?</span>
        <h3 className="text-sm font-semibold text-amber-800">需要澄清</h3>
      </div>
      <p className="mb-3 text-sm text-amber-900">{question}</p>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <button
            key={option}
            onClick={() => onSelect(option)}
            className="rounded-md border border-amber-300 bg-white px-3 py-1.5 text-sm text-amber-700 transition-colors hover:bg-amber-100"
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Run frontend check**

Run: `cd agenthub/frontend && npm run check`
Expected: No type errors.

- [ ] **Step 3: Commit**

```bash
git add agenthub/frontend/components/chat/ClarificationCard.tsx
git commit -m "feat: add ClarificationCard for HITL interaction"
```

---

### Task 13: Frontend DiffViewer Component

**Files:**
- Create: `agenthub/frontend/components/chat/DiffViewer.tsx`
- Modify: `agenthub/frontend/package.json` (add react-diff-viewer-continued)

- [ ] **Step 1: Install dependency**

Run: `cd agenthub/frontend && npm install react-diff-viewer-continued`
Expected: Package installed successfully.

- [ ] **Step 2: Create DiffViewer.tsx**

```tsx
'use client'

import { useState } from 'react'
import DiffViewerLib from 'react-diff-viewer-continued'

interface DiffViewerProps {
  filePath: string
  oldContent: string
  newContent: string
  onAccept?: () => void
  onReject?: () => void
}

export function DiffViewer({ filePath, oldContent, newContent, onAccept, onReject }: DiffViewerProps) {
  const [expanded, setExpanded] = useState(true)

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between bg-gray-50 px-4 py-2">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-gray-500 hover:text-gray-700"
          >
            {expanded ? '▼' : '▶'}
          </button>
          <span className="font-mono text-sm text-gray-700">{filePath}</span>
        </div>
        <div className="flex gap-2">
          {onReject && (
            <button
              onClick={onReject}
              className="rounded border border-red-300 px-2 py-1 text-xs text-red-600 hover:bg-red-50"
            >
              Reject
            </button>
          )}
          {onAccept && (
            <button
              onClick={onAccept}
              className="rounded border border-green-300 px-2 py-1 text-xs text-green-600 hover:bg-green-50"
            >
              Accept
            </button>
          )}
        </div>
      </div>
      {/* Diff content */}
      {expanded && (
        <div className="max-h-96 overflow-auto">
          <DiffViewerLib
            oldValue={oldContent}
            newValue={newContent}
            splitView={false}
            useDarkTheme={false}
          />
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 3: Run frontend check**

Run: `cd agenthub/frontend && npm run check`
Expected: No type errors.

- [ ] **Step 4: Commit**

```bash
git add agenthub/frontend/components/chat/DiffViewer.tsx agenthub/frontend/package.json agenthub/frontend/package-lock.json
git commit -m "feat: add DiffViewer component with react-diff-viewer-continued"
```

---

### Task 14: Frontend MessageBubble Extension

**Files:**
- Modify: `agenthub/frontend/components/chat/MessageBubble.tsx`
- Read: `agenthub/frontend/lib/types.ts`

- [ ] **Step 1: Read current MessageBubble.tsx and types.ts**

Read both files to understand existing message rendering.

- [ ] **Step 2: Add 'type' field support to Message interface if missing**

In `types.ts`, ensure Message has:
```typescript
type?: 'text' | 'task_panel' | 'clarification' | 'diff'
```

- [ ] **Step 3: Update MessageBubble to render special message types**

Add rendering logic for non-text message types:

```tsx
import { TaskPanel } from '@/components/chat/TaskPanel'
import { ClarificationCard } from '@/components/chat/ClarificationCard'
import { DiffViewer } from '@/components/chat/DiffViewer'
import { useTaskStore } from '@/lib/stores/taskStore'

// Inside MessageBubble component, before the default text rendering:
if (message.type === 'task_panel') {
  const tasks = useTaskStore.getState().tasks
  return (
    <div className={bubbleClasses}>
      <TaskPanel tasks={tasks} />
    </div>
  )
}

if (message.type === 'clarification') {
  return (
    <div className={bubbleClasses}>
      <ClarificationCard
        question={message.content}
        options={message.metadata?.options ?? []}
        onSelect={(option) => {
          // Send option as user message
          sendMessage(option)
        }}
      />
    </div>
  )
}

if (message.type === 'diff') {
  const { file_path, old_content, new_content } = message.metadata ?? {}
  return (
    <div className={bubbleClasses}>
      <DiffViewer
        filePath={file_path ?? ''}
        oldContent={old_content ?? ''}
        newContent={new_content ?? ''}
      />
    </div>
  )
}
```

- [ ] **Step 4: Run frontend check**

Run: `cd agenthub/frontend && npm run check`
Expected: No type errors.

- [ ] **Step 5: Commit**

```bash
git add agenthub/frontend/components/chat/MessageBubble.tsx agenthub/frontend/lib/types.ts
git commit -m "feat: extend MessageBubble to render task_panel, clarification, and diff types"
```

---

### Task 15: Backend Message Routing Integration

**Files:**
- Modify: `agenthub/backend/routers/messages.py`
- Read: `agenthub/backend/services/orchestrator.py`
- Read: `agenthub/backend/services/task_manager.py`
- Read: `agenthub/backend/routers/tasks.py`

- [ ] **Step 1: Read current messages.py and new services**

Read all files to understand integration points.

- [ ] **Step 2: Integrate Orchestrator flow into POST /api/messages**

Modify the message handling to detect orchestrator-bound messages and trigger task decomposition:

```python
from services.orchestrator import OrchestratorAgent
from routers.tasks import task_manager

# In the send_message endpoint, after detecting @orchestrator:
if target_agent == "orchestrator":
    orchestrator = OrchestratorAgent()
    output = await orchestrator.decompose(message.content)
    
    if output.requires_clarification:
        # Send clarification request via SSE
        await sse_manager.broadcast_clarification_request(
            message_id=str(uuid.uuid4()),
            question=output.clarification_question,
            options=output.uncertain_points[0].options if output.uncertain_points else []
        )
    elif output.tasks:
        # Create tasks and broadcast
        tasks = task_manager.add_tasks_from_orchestrator(output)
        for task in tasks:
            await sse_manager.broadcast_task_created(task.id, task.title, task.assigned_to)
        # Execute tasks in background
        asyncio.create_task(task_manager.run_all())
    else:
        # Fallback: broadcast to all agents
        pass
```

- [ ] **Step 3: Verify integration**

Run: `cd agenthub/backend && python main.py`
Test: Send a message with `@orchestrator` prefix.
Expected: Orchestrator decomposes tasks, tasks appear via SSE.

- [ ] **Step 4: Commit**

```bash
git add agenthub/backend/routers/messages.py
git commit -m "feat: integrate Orchestrator flow into message handling"
```

---

### Task 16: End-to-End Integration Verification

**Files:**
- Read: All modified and created files
- Test: Manual E2E verification

- [ ] **Step 1: Start backend and frontend**

Terminal 1:
```bash
cd agenthub/backend && python main.py
```

Terminal 2:
```bash
cd agenthub/frontend && npm run dev
```

- [ ] **Step 2: Verify Agent list includes all 5 agents**

Open `http://localhost:7000/agents` and verify: PM, 架构师, 开发者, QA工程师, 协调器.

- [ ] **Step 3: Test Orchestrator flow**

1. Open chat at `http://localhost:7000`
2. Send `@orchestrator 帮我创建一个简单的登录页面`
3. Verify:
   - Orchestrator decomposes into tasks
   - TaskPanel appears in chat showing task progress
   - Tasks transition from pending → running → done
   - If HITL triggered, ClarificationCard appears with options

- [ ] **Step 4: Test direct agent messaging**

1. Send `@pm 分析一下登录功能的需求`
2. Verify PM responds with analysis
3. Send `@architect 设计登录模块架构`
4. Verify Architect responds

- [ ] **Step 5: Verify SSE streaming**

1. Open browser DevTools → Network → EventStream
2. Verify new event types appear: `task_created`, `task_update`, `stream_chunk`

- [ ] **Step 6: Run all backend tests**

Run: `cd agenthub/backend && python -m pytest -v`
Expected: All tests pass.

- [ ] **Step 7: Run frontend checks**

Run: `cd agenthub/frontend && npm run check`
Expected: No type errors.

- [ ] **Step 8: Final commit**

```bash
git add -A
git commit -m "chore: e2e integration verification complete"
```

---

## Self-Review Checklist

- [ ] All 15+ tasks cover the 7 P0/P1 features from the spec
- [ ] No placeholders (TBD, TODO, implement later)
- [ ] Type names consistent across tasks (Task, TaskStatus, OrchestratorOutput, etc.)
- [ ] Each task has exact file paths and complete code
- [ ] Tests included for all backend services
- [ ] Frontend components use Tailwind v4 (kebab-case classes)
- [ ] SSE event types match between backend broadcast and frontend handler
- [ ] Agent IDs (pm/architect/developer/qa/orchestrator) consistent throughout

