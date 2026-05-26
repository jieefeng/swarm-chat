"""SharedContext 测试"""
import pytest
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
