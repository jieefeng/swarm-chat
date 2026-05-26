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
