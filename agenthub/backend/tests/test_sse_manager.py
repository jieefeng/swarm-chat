"""SSEEventManager (SSEManager) 单元测试 (UT-E001 ~ UT-E005)

等待策略：先启动消费任务，用极短延迟让订阅生成器完成首次迭代（注册队列），
广播后用 wait_for 等事件到达。不要用无超时的 __anext__() 直接等事件——
队列空闲时生成器要等满 30s 才吐 keepalive。
"""
import asyncio
import json
import sys
import os

import pytest

# 添加父目录到路径以导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agenthub.backend.services.sse_manager import SSEManager

# 让订阅生成器完成首次迭代（注册队列）的让步延迟
ACTIVATE_DELAY = 0.01
# 单条事件的最长等待时间
EVENT_TIMEOUT = 1.0


class TestSSEEventManager:
    """SSEManager测试类"""

    @pytest.fixture
    def sse_manager(self):
        """创建SSEManager实例"""
        return SSEManager()

    # UT-E001: 订阅事件 -> 返回AsyncGenerator
    @pytest.mark.asyncio
    async def test_subscribe_returns_async_generator(self, sse_manager):
        """UT-E001: subscribe方法返回可用的AsyncGenerator"""
        gen = sse_manager.subscribe()
        assert hasattr(gen, "__anext__")  # 检查是否是异步生成器

        receiver = asyncio.create_task(gen.__anext__())
        await asyncio.sleep(ACTIVATE_DELAY)

        await sse_manager.broadcast("message", {"content": "test"})
        event = await asyncio.wait_for(receiver, timeout=EVENT_TIMEOUT)
        assert event["event"] == "message"
        assert "test" in event["data"]

        await gen.aclose()

    # UT-E002: 推送消息到所有订阅者 -> 所有队列收到消息
    @pytest.mark.asyncio
    async def test_broadcast_to_all_subscribers(self, sse_manager):
        """UT-E002: broadcast向所有订阅者推送消息"""
        gens = [sse_manager.subscribe() for _ in range(2)]
        receivers = [asyncio.create_task(g.__anext__()) for g in gens]
        await asyncio.sleep(ACTIVATE_DELAY)

        await sse_manager.broadcast("message", {"content": "test"})

        for receiver in receivers:
            event = await asyncio.wait_for(receiver, timeout=EVENT_TIMEOUT)
            assert event["event"] == "message"
            assert "test" in event["data"]

        for gen in gens:
            await gen.aclose()

    # UT-E003: 推送终止信号 -> 所有队列收到termination事件
    @pytest.mark.asyncio
    async def test_broadcast_termination_signal(self, sse_manager):
        """UT-E003: broadcast终止信号，订阅者收到termination事件"""
        gen = sse_manager.subscribe()
        receiver = asyncio.create_task(gen.__anext__())
        await asyncio.sleep(ACTIVATE_DELAY)

        await sse_manager.broadcast("termination", {"reason": "session_end"})

        event = await asyncio.wait_for(receiver, timeout=EVENT_TIMEOUT)
        assert event["event"] == "termination"
        assert "session_end" in event["data"]

        await gen.aclose()

    # UT-E004: 取消订阅 -> queue不再收到消息
    @pytest.mark.asyncio
    async def test_unsubscribe_stops_receiving(self, sse_manager):
        """UT-E004: 关闭订阅生成器（aclose）后，广播不再投递给它"""
        gens = [sse_manager.subscribe() for _ in range(3)]
        receivers = [asyncio.create_task(g.__anext__()) for g in gens]
        await asyncio.sleep(ACTIVATE_DELAY)
        assert await sse_manager.get_subscriber_count() == 3

        await sse_manager.broadcast("message", {"content": "before"})
        for receiver in receivers:
            event = await asyncio.wait_for(receiver, timeout=EVENT_TIMEOUT)
            assert "before" in event["data"]

        # 关闭第一个订阅者，订阅者数量随之减少
        await gens[0].aclose()
        assert await sse_manager.get_subscriber_count() == 2

        # 后续广播只投递给仍在订阅的两个
        receivers_after = [asyncio.create_task(g.__anext__()) for g in gens[1:]]
        await asyncio.sleep(ACTIVATE_DELAY)
        await sse_manager.broadcast("message", {"content": "after"})
        for receiver in receivers_after:
            event = await asyncio.wait_for(receiver, timeout=EVENT_TIMEOUT)
            assert "after" in event["data"]

        for gen in gens[1:]:
            await gen.aclose()
        assert await sse_manager.get_subscriber_count() == 0

    # UT-E005: 并发推送 -> 无数据丢失
    @pytest.mark.asyncio
    async def test_concurrent_broadcast_no_data_loss(self, sse_manager):
        """UT-E005: 连续广播消息时，每个订阅者收到的消息一条不少"""
        num_messages = 10
        gens = [sse_manager.subscribe() for _ in range(3)]
        buffers = [[] for _ in gens]

        async def receive_all(gen, sink):
            for _ in range(num_messages):
                sink.append(await asyncio.wait_for(gen.__anext__(), timeout=EVENT_TIMEOUT))

        tasks = [asyncio.create_task(receive_all(g, b)) for g, b in zip(gens, buffers)]
        await asyncio.sleep(ACTIVATE_DELAY)

        for i in range(num_messages):
            await sse_manager.broadcast("message", {"index": i})

        await asyncio.wait_for(asyncio.gather(*tasks), timeout=EVENT_TIMEOUT * num_messages)

        for buffer in buffers:
            assert len(buffer) == num_messages
        for gen in gens:
            await gen.aclose()

    @pytest.mark.asyncio
    async def test_initial_subscriber_count(self, sse_manager):
        """测试初始订阅者数量为0"""
        assert await sse_manager.get_subscriber_count() == 0

    @pytest.mark.asyncio
    async def test_subscribe_increments_count(self, sse_manager):
        """测试订阅后订阅者数量增加，关闭后回落"""
        assert await sse_manager.get_subscriber_count() == 0

        gen = sse_manager.subscribe()
        receiver = asyncio.create_task(gen.__anext__())
        await asyncio.sleep(ACTIVATE_DELAY)
        assert await sse_manager.get_subscriber_count() == 1

        await sse_manager.broadcast("message", {"content": "x"})
        await asyncio.wait_for(receiver, timeout=EVENT_TIMEOUT)

        await gen.aclose()
        assert await sse_manager.get_subscriber_count() == 0

    @pytest.mark.asyncio
    async def test_broadcast_message_format(self, sse_manager):
        """测试广播消息格式正确"""
        gen = sse_manager.subscribe()
        receiver = asyncio.create_task(gen.__anext__())
        await asyncio.sleep(ACTIVATE_DELAY)

        await sse_manager.broadcast("test_event", {"key": "value"})

        event = await asyncio.wait_for(receiver, timeout=EVENT_TIMEOUT)
        assert event == {
            "event": "test_event",
            "data": json.dumps({"key": "value"}, ensure_ascii=False),
        }

        await gen.aclose()

    @pytest.mark.asyncio
    async def test_thread_isolation(self, sse_manager):
        """测试线程隔离：线程订阅者只收到该线程的事件"""
        # 创建两个订阅者：一个订阅线程 A，一个订阅全局
        queue_a = asyncio.Queue()
        queue_global = asyncio.Queue()

        sse_manager.subscribers[queue_a] = "thread_a"
        sse_manager.subscribers[queue_global] = None

        try:
            # 广播到线程 A
            await sse_manager.broadcast("message", {"content": "hello"}, thread_id="thread_a")

            # 线程 A 订阅者应该收到
            event_a = await asyncio.wait_for(queue_a.get(), timeout=1)
            assert event_a["event"] == "message"
            assert "hello" in event_a["data"]

            # 全局订阅者也应该收到
            event_global = await asyncio.wait_for(queue_global.get(), timeout=1)
            assert event_global["event"] == "message"
            assert "hello" in event_global["data"]

            # 广播到线程 B
            await sse_manager.broadcast("message", {"content": "world"}, thread_id="thread_b")

            # 线程 A 订阅者不应该收到
            assert queue_a.empty()

            # 全局订阅者应该收到
            event_global_b = await asyncio.wait_for(queue_global.get(), timeout=1)
            assert event_global_b["event"] == "message"
            assert "world" in event_global_b["data"]
        finally:
            # 清理手动添加的订阅者
            sse_manager.subscribers.pop(queue_a, None)
            sse_manager.subscribers.pop(queue_global, None)

    @pytest.mark.asyncio
    async def test_multiple_subscriptions(self, sse_manager):
        """测试多个订阅者同时在线"""
        gens = [sse_manager.subscribe() for _ in range(5)]
        receivers = [asyncio.create_task(g.__anext__()) for g in gens]
        await asyncio.sleep(ACTIVATE_DELAY)
        assert await sse_manager.get_subscriber_count() == 5

        await sse_manager.broadcast("message", {"content": "all"})
        for receiver in receivers:
            event = await asyncio.wait_for(receiver, timeout=EVENT_TIMEOUT)
            assert event["event"] == "message"

        for gen in gens:
            await gen.aclose()
        assert await sse_manager.get_subscriber_count() == 0
