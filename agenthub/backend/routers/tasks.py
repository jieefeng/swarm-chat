"""任务 API 路由"""
from fastapi import APIRouter, HTTPException
from agenthub.backend.models.task import TaskStatus
from agenthub.backend.services.task_manager import TaskManager

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
