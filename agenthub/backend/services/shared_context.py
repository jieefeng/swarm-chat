"""SharedContext - Agent 间共享状态（黑板模式）+ 结构化记忆"""
import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class MemoryType(str, Enum):
    """结构化记忆类型"""
    LESSON = "lesson"       # 教训：踩过的坑、经验总结
    DECISION = "decision"   # 决策：技术选型、方案取舍及原因
    EVIDENCE = "evidence"   # 证据：验证过的结论、测试结果


@dataclass
class StructuredMemory:
    """一条结构化记忆"""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    type: MemoryType = MemoryType.LESSON
    content: str = ""
    agent_id: str = ""          # 写入者
    tags: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class SharedContext:
    """Agent 间共享上下文，支持写锁 + 结构化记忆"""

    def __init__(self):
        self._data: dict[str, object] = {}
        self._task_locks: dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()
        self._memories: List[StructuredMemory] = []

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

    # --- 结构化记忆 ---

    async def add_memory(
        self,
        type: MemoryType,
        content: str,
        agent_id: str,
        tags: Optional[List[str]] = None,
    ) -> StructuredMemory:
        """写入一条结构化记忆（教训/决策/证据）"""
        memory = StructuredMemory(
            type=type,
            content=content,
            agent_id=agent_id,
            tags=tags or [],
        )
        async with self._global_lock:
            self._memories.append(memory)
        return memory

    async def query_memories(
        self,
        type: Optional[MemoryType] = None,
        agent_id: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 20,
    ) -> List[StructuredMemory]:
        """查询结构化记忆，支持按类型/写入者/标签过滤"""
        results = self._memories
        if type is not None:
            results = [m for m in results if m.type == type]
        if agent_id is not None:
            results = [m for m in results if m.agent_id == agent_id]
        if tag is not None:
            results = [m for m in results if tag in m.tags]
        return results[-limit:]

    def clear(self):
        self._data.clear()
        self._task_locks.clear()
        self._memories.clear()


# 全局单例
shared_context = SharedContext()
