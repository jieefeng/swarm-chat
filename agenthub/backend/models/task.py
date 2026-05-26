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
