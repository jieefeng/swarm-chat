"""A2A 消息路由 - @mention 解析 + 自动路由"""
import logging
import re
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Optional

from agenthub.backend.services.session import AGENT_CONFIGS, session_manager
from agenthub.backend.services.thread_manager import thread_manager
from agenthub.backend.services.sse_manager import sse_manager

logger = logging.getLogger(__name__)


class A2ARouter:
    """A2A 消息路由器

    负责：
    1. 解析消息中的 @mention
    2. 路由消息到正确的 agent
    3. 投递消息并触发 LLM 响应
    """

    # @mention 正则：匹配 @agent_id 或 @agent_name（不匹配 email 中的 @）
    MENTION_PATTERN = re.compile(r"(?<!\w)@(\w+)")

    def __init__(self):
        # 构建 name → id 映射
        self._name_to_id: dict[str, str] = {}
        for agent_id, config in AGENT_CONFIGS.items():
            name = config.get("name", "").lower()
            if name:
                self._name_to_id[name] = agent_id

    def parse_mentions(self, content: str) -> tuple[str, list[str]]:
        """解析消息中的 @mention

        Args:
            content: 原始消息内容

        Returns:
            (清理后的消息内容, mention 的 agent_id 列表)
        """
        mentions = []
        for match in self.MENTION_PATTERN.finditer(content):
            mention = match.group(1).lower()
            # 尝试直接匹配 agent_id
            if mention in AGENT_CONFIGS:
                mentions.append(mention)
            # 尝试匹配 agent name
            elif mention in self._name_to_id:
                mentions.append(self._name_to_id[mention])

        # 清理消息内容（移除 @mention）
        cleaned = self.MENTION_PATTERN.sub("", content).strip()
        return cleaned, mentions

    async def route_message(self, thread_id: str, content: str,
                            agent_id: Optional[str] = None) -> list[str]:
        """路由消息到正确的 agent

        路由逻辑：
        1. 如果指定了 agent_id → 直接使用
        2. 解析 @mention → 如果有，只发给指定 agent
        3. 如果没有 @mention → 调用 orchestrator 自动决定

        Args:
            thread_id: 线程 ID
            content: 消息内容
            agent_id: 前端指定的 agent ID（可选）

        Returns:
            应该接收消息的 agent_id 列表
        """
        # 1. 前端明确指定
        if agent_id:
            return [agent_id]

        # 2. 解析 @mention
        _, mentions = self.parse_mentions(content)
        if mentions:
            return mentions

        # 3. 自动路由（调用 orchestrator）
        try:
            from agenthub.backend.services.orchestrator import OrchestratorAgent
            orchestrator = OrchestratorAgent()
            output = await orchestrator.decompose(content)
            if output.tasks:
                targets = list(set(task.assigned_to for task in output.tasks))
                return targets
        except Exception as e:
            logger.warning(f"Orchestrator routing failed, falling back to broadcast: {e}", exc_info=True)

        # 4. 降级：广播给所有 agent
        return list(AGENT_CONFIGS.keys())

    async def deliver_to_agent(self, agent_id: str, thread_id: str,
                               message: str, from_agent: Optional[str] = None):
        """投递消息给指定 agent，触发 LLM 响应

        Args:
            agent_id: 目标 agent ID
            thread_id: 线程 ID
            message: 消息内容
            from_agent: 来源 agent ID（None 表示来自用户）
                        当前 Phase 只实现 user→agent，此参数为后续扩展预留
        """
        config = AGENT_CONFIGS.get(agent_id)
        if not config:
            logger.error(f"Unknown agent: {agent_id}")
            return

        agent_name = config.get("name", agent_id)
        message_id = f"msg_{uuid.uuid4().hex[:8]}"

        # 获取线程上下文
        context = await thread_manager.get_thread_context(thread_id)
        agent_message = f"上下文参考:\n{context}\n\n用户消息: {message}" if context else message

        # 流式调用 LLM
        full_response = ""
        seq = 0

        try:
            queue: asyncio.Queue = asyncio.Queue()

            def _produce():
                try:
                    for chunk in session_manager.send_to_agent_stream(agent_id, agent_message):
                        queue.put_nowait(chunk)
                except Exception as e:
                    queue.put_nowait(e)
                finally:
                    queue.put_nowait(None)

            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, _produce)

            while True:
                item = await queue.get()
                if item is None:
                    break
                if isinstance(item, Exception):
                    raise item
                full_response += item
                await sse_manager.broadcast_stream_chunk(message_id, item, seq)
                seq += 1

            # 存储 agent 响应到线程
            await thread_manager.add_message(
                thread_id=thread_id,
                sender_id=agent_id,
                content=full_response,
            )

            # 广播完整消息事件
            await sse_manager.broadcast("message", {
                "id": message_id,
                "thread_id": thread_id,
                "sender": agent_id,
                "sender_name": agent_name,
                "content": full_response,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "type": "agent",
            }, thread_id=thread_id)

        except Exception as e:
            logger.error(f"Agent {agent_id} LLM call failed: {e}", exc_info=True)
            error_content = "抱歉，Agent 处理消息时出现错误，请稍后重试。"
            await thread_manager.add_message(
                thread_id=thread_id,
                sender_id=agent_id,
                content=error_content,
            )
            await sse_manager.broadcast("message", {
                "id": message_id,
                "thread_id": thread_id,
                "sender": agent_id,
                "sender_name": agent_name,
                "content": error_content,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "type": "agent",
            }, thread_id=thread_id)


# 全局实例
a2a_router = A2ARouter()
