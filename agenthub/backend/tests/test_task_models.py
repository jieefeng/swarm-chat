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
