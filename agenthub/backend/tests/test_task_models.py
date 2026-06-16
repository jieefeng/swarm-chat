"""任务模型测试"""
import pytest
from agenthub.backend.models.task import Task, TaskStatus


def test_task_default_status():
    task = Task(title="Test", description="Desc", assigned_to="designer")
    assert task.status == TaskStatus.PENDING


def test_task_valid_transition_pending_to_running():
    task = Task(title="Test", description="Desc", assigned_to="designer")
    assert task.can_transition_to(TaskStatus.RUNNING) is True


def test_task_invalid_transition_done_to_running():
    task = Task(title="Test", description="Desc", assigned_to="designer", status=TaskStatus.DONE)
    assert task.can_transition_to(TaskStatus.RUNNING) is False
