"""Callback Router - 处理 Agent 的 HTTP callback 请求

Agent 收到注入的 callback 指令后，通过 HTTP 与平台交互：
- post_message: 发送消息给团队（可选 @mention 其他 Agent）
- thread-context: 获取对话上下文
- pending-mentions: 获取待处理的 @提及

凭证由 InvocationRegistry 校验。
"""
import logging
from typing import Any, Dict, List, Optional

from .a2a_router import a2a_router
from .invocation_registry import invocation_registry
from .memory_manager import redis_memory_manager as memory
from .session import AGENT_CONFIGS
from .sse_manager import sse_manager

logger = logging.getLogger(__name__)


class CallbackRouter:
    """Agent HTTP callback 的服务层"""

    async def post_message(
        self,
        invocation_id: str,
        callback_token: str,
        content: str,
        target_agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Agent 发送消息给团队。

        Args:
            invocation_id / callback_token: 凭证
            content: 消息内容
            target_agent_id: @mention 的目标 Agent（可选）

        Raises:
            ValueError: 凭证无效或过期
        """
        inv = invocation_registry.verify(invocation_id, callback_token)
        if inv is None:
            raise ValueError("Invalid or expired credentials")

        agent_id = inv["agent_id"]
        thread_id = inv["thread_id"]
        agent_name = AGENT_CONFIGS.get(agent_id, {}).get("name", agent_id)

        msg = await memory.add_message(
            role=agent_id,
            content=content,
            agent_id=agent_id,
            sender_name=agent_name,
            thread_id=thread_id,
        )

        # 广播给所有订阅者
        await sse_manager.broadcast("message", msg, thread_id=thread_id)

        # @mention 目标 Agent → 追加到该 thread 的 A2A worklist
        if target_agent_id:
            a2a_router.enqueue_a2a_targets(thread_id, [target_agent_id])

        logger.info(
            "Callback post_message: agent=%s thread=%s target=%s",
            agent_id, thread_id, target_agent_id,
        )
        return {"status": "ok", "message_id": msg.get("id")}

    async def get_thread_context(
        self,
        invocation_id: str,
        callback_token: str,
    ) -> Dict[str, Any]:
        """获取当前 thread 的对话上下文。

        Raises:
            ValueError: 凭证无效或过期
        """
        inv = invocation_registry.verify(invocation_id, callback_token)
        if inv is None:
            raise ValueError("Invalid or expired credentials")

        messages = await memory.get_messages(thread_id=inv["thread_id"])
        return {"messages": messages}

    async def get_pending_mentions(
        self,
        invocation_id: str,
        callback_token: str,
    ) -> Dict[str, Any]:
        """获取当前 thread 中 @提及该 Agent 的消息。

        Raises:
            ValueError: 凭证无效或过期
        """
        inv = invocation_registry.verify(invocation_id, callback_token)
        if inv is None:
            raise ValueError("Invalid or expired credentials")

        agent_id = inv["agent_id"]
        mention_tag = f"@{agent_id}"
        messages = await memory.get_messages(thread_id=inv["thread_id"])

        mentions: List[Dict[str, Any]] = [
            {
                "message_id": m.get("id"),
                "from_agent": m.get("agent_id") or m.get("role"),
                "content": m.get("content", ""),
                "timestamp": m.get("timestamp"),
            }
            for m in messages
            if mention_tag in (m.get("content") or "")
            and (m.get("agent_id") or m.get("role")) != agent_id
        ]
        return {"mentions": mentions}


# 全局单例
callback_router = CallbackRouter()
