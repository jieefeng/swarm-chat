"""TaskManager - 任务状态机 + DAG 调度 + SOP 守护"""
import asyncio
from collections import defaultdict, deque

from agenthub.backend.models.task import Task, TaskCreate, TaskStatus, OrchestratorOutput
from agenthub.backend.services.agent_adapter import get_agent_adapter, IAgentAdapter
from agenthub.backend.services.sse_manager import sse_manager


MAX_RETRY = 3

# SOP 规则：任务完成后自动触发的后续任务
# key = 完成任务的 assigned_to，value = 自动创建的审查任务配置
SOP_RULES: dict[str, dict] = {
    "developer": {
        "assigned_to": "qa",
        "title_template": "审查: {original_title}",
        "description_template": "请审查以下开发任务的代码质量和功能正确性：\n\n任务: {original_title}\n结果:\n{result}",
    },
}


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
        for tc in output.tasks:
            task = Task(
                title=tc.title,
                description=tc.description,
                assigned_to=tc.assigned_to,
                depends_on=[],
                priority=tc.priority,
            )
            self._tasks[task.id] = task
            self._title_to_id[tc.title] = task.id
            tasks.append(task)
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
        in_degree: dict[str, int] = defaultdict(int)
        graph: dict[str, list[str]] = defaultdict(list)
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
        """执行单个任务（按 assigned_to agent 的 llm_provider 选择 LLM）"""
        if adapter is None:
            from .session import AGENT_CONFIGS
            provider = AGENT_CONFIGS.get(task.assigned_to, {}).get("llm_provider")
            adapter = get_agent_adapter(provider)
        async with self._lock:
            task.status = TaskStatus.RUNNING
        await sse_manager.broadcast("task_update", {"task_id": task.id, "status": task.status.value, "title": task.title})
        try:
            from services.session import AGENT_CONFIGS
            agent_config = AGENT_CONFIGS.get(task.assigned_to, {})
            system_prompt = agent_config.get("system_prompt", "你是一个 AI 助手。")
            result = await adapter.send_message(system_prompt, task.description)
            async with self._lock:
                task.result = result
                task.status = TaskStatus.DONE
            await sse_manager.broadcast("task_update", {"task_id": task.id, "status": "done", "title": task.title})
            # SOP 守护：任务完成后自动触发后续审查任务
            await self._apply_sop(task)
        except Exception as e:
            async with self._lock:
                task.retry_count += 1
                if task.retry_count >= MAX_RETRY:
                    task.status = TaskStatus.ESCALATE
                else:
                    task.status = TaskStatus.FAILED
            await sse_manager.broadcast("task_update", {"task_id": task.id, "status": task.status.value, "title": task.title})

    async def _apply_sop(self, completed_task: Task) -> None:
        """SOP 守护：根据规则自动创建后续任务"""
        rule = SOP_RULES.get(completed_task.assigned_to)
        if rule is None:
            return
        # 避免重复触发：检查是否已有同名审查任务
        follow_title = rule["title_template"].format(original_title=completed_task.title)
        if follow_title in self._title_to_id:
            return
        follow_task = Task(
            title=follow_title,
            description=rule["description_template"].format(
                original_title=completed_task.title,
                result=(completed_task.result or "")[:2000],
            ),
            assigned_to=rule["assigned_to"],
            depends_on=[completed_task.id],
            priority=completed_task.priority,
        )
        async with self._lock:
            self._tasks[follow_task.id] = follow_task
            self._title_to_id[follow_title] = follow_task.id
        await sse_manager.broadcast("task_created", {
            "task_id": follow_task.id,
            "title": follow_task.title,
            "assigned_to": follow_task.assigned_to,
            "trigger": "sop",
        })

    async def execute_ready_tasks(self, adapter: IAgentAdapter | None = None) -> None:
        """并行执行所有就绪任务"""
        ready = self.get_ready_tasks()
        if not ready:
            return
        await asyncio.gather(*(self.execute_task(t, adapter) for t in ready))

    async def run_all(self, adapter: IAgentAdapter | None = None) -> None:
        """执行所有任务直到完成或卡住"""
        if self.has_cycle():
            for task in self._tasks.values():
                if task.status == TaskStatus.PENDING:
                    await self.execute_task(task, adapter)
            return
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
