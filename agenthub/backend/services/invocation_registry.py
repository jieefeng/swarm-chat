"""Invocation Registry - A2A callback 凭证管理

每个 agent invocation 发放一对凭证 (invocation_id, callback_token)，
Agent 通过 HTTP callback 与平台交互时必须携带。
凭证内存存储，TTL 默认 1 小时（见 CLAUDE.md A2A 隐性知识）。
"""
import logging
import time
import uuid
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# 默认 TTL：1 小时
DEFAULT_TTL = 3600


class InvocationRegistry:
    """管理 invocation 凭证的创建/校验/撤销（内存存储）"""

    def __init__(self, ttl: int = DEFAULT_TTL):
        self.ttl = ttl
        # invocation_id -> {"token", "agent_id", "thread_id", "ttl", "created_at"}
        self._invocations: Dict[str, Dict[str, Any]] = {}

    def create(self, agent_id: str, thread_id: str) -> Tuple[str, str]:
        """为 agent 创建凭证。

        Returns:
            (invocation_id, callback_token)，均为 UUID4 字符串。
        """
        invocation_id = str(uuid.uuid4())
        callback_token = str(uuid.uuid4())
        self._invocations[invocation_id] = {
            "token": callback_token,
            "agent_id": agent_id,
            "thread_id": thread_id,
            "ttl": self.ttl,
            "created_at": time.time(),
        }
        logger.info(
            "Invocation created: agent=%s thread=%s inv=%s", agent_id, thread_id, invocation_id
        )
        return invocation_id, callback_token

    def get_invocation(self, invocation_id: str) -> Optional[Dict[str, Any]]:
        """获取 invocation 元数据（不含 token），不存在返回 None。"""
        return self._invocations.get(invocation_id)

    def verify(self, invocation_id: str, callback_token: str) -> Optional[Dict[str, Any]]:
        """校验凭证。通过返回元数据，失败/过期返回 None。

        过期的 invocation 会被移除。
        """
        inv = self._invocations.get(invocation_id)
        if inv is None:
            return None
        if inv["token"] != callback_token:
            return None
        if self._is_expired(inv):
            del self._invocations[invocation_id]
            logger.info("Invocation expired and removed: %s", invocation_id)
            return None
        return inv

    def revoke(self, invocation_id: str) -> bool:
        """撤销 invocation。存在返回 True，不存在返回 False。"""
        if invocation_id in self._invocations:
            del self._invocations[invocation_id]
            return True
        return False

    def cleanup_expired(self) -> int:
        """清理所有过期 invocation，返回清理数量。"""
        now = time.time()
        expired = [
            inv_id
            for inv_id, inv in self._invocations.items()
            if self._is_expired(inv, now=now)
        ]
        for inv_id in expired:
            del self._invocations[inv_id]
        if expired:
            logger.info("Cleaned up %d expired invocations", len(expired))
        return len(expired)

    def count(self) -> int:
        """当前活跃 invocation 数量。"""
        return len(self._invocations)

    def get_all_invocations(self) -> Dict[str, Dict[str, Any]]:
        """返回所有 invocation 的浅拷贝快照。"""
        return dict(self._invocations)

    def _is_expired(self, inv: Dict[str, Any], now: Optional[float] = None) -> bool:
        if now is None:
            now = time.time()
        return (now - inv["created_at"]) > inv["ttl"]


# 全局单例：TTL 1 小时
invocation_registry = InvocationRegistry(ttl=DEFAULT_TTL)
