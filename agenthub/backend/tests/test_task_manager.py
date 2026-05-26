"""TaskManager 测试"""
import pytest
from unittest.mock import AsyncMock, patch
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
    t1.depends_on = [t2.id]
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
         patch("services.task_manager.AGENT_CONFIGS", {"pm": {"system_prompt": "test"}}, create=True):
        mock_sse.broadcast = AsyncMock()
        with patch.dict("sys.modules", {"services.session": type("M", (), {"AGENT_CONFIGS": {"pm": {"system_prompt": "test"}}})}):
            await tm.execute_task(task, mock_adapter)
    assert task.status == TaskStatus.DONE
    assert task.result == "done"


@pytest.mark.asyncio
async def test_execute_task_failure_retries():
    tm = TaskManager()
    task = Task(title="T1", description="D1", assigned_to="pm")
    tm._tasks[task.id] = task
    mock_adapter = AsyncMock()
    mock_adapter.send_message = AsyncMock(side_effect=Exception("LLM error"))
    with patch("services.task_manager.sse_manager") as mock_sse:
        mock_sse.broadcast = AsyncMock()
        with patch.dict("sys.modules", {"services.session": type("M", (), {"AGENT_CONFIGS": {"pm": {"system_prompt": "test"}}})}):
            await tm.execute_task(task, mock_adapter)
    assert task.status == TaskStatus.FAILED
    assert task.retry_count == 1


@pytest.mark.asyncio
async def test_execute_task_escalate_after_max_retry():
    tm = TaskManager()
    task = Task(title="T1", description="D1", assigned_to="pm")
    task.retry_count = 2  # Already retried twice
    tm._tasks[task.id] = task
    mock_adapter = AsyncMock()
    mock_adapter.send_message = AsyncMock(side_effect=Exception("LLM error"))
    with patch("services.task_manager.sse_manager") as mock_sse:
        mock_sse.broadcast = AsyncMock()
        with patch.dict("sys.modules", {"services.session": type("M", (), {"AGENT_CONFIGS": {"pm": {"system_prompt": "test"}}})}):
            await tm.execute_task(task, mock_adapter)
    assert task.status == TaskStatus.ESCALATE
    assert task.retry_count == 3


def test_reset_tasks():
    tm = TaskManager()
    t1 = Task(title="T1", description="D1", assigned_to="pm")
    t1.status = TaskStatus.DONE
    t1.result = "some result"
    t1.retry_count = 2
    tm._tasks[t1.id] = t1
    tm.reset()
    assert t1.status == TaskStatus.PENDING
    assert t1.result is None
    assert t1.retry_count == 0
