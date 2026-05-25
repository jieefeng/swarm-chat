"""内存管理器 - 消息历史存储"""
import uuid
from typing import List, Dict, Optional
from datetime import datetime


class MemoryManager:
    """管理对话消息历史"""

    def __init__(self, max_messages: int = 1000):
        self.messages: List[Dict] = []
        self.max_messages = max_messages

    def add_message(self, role: str, content: str, agent_id: Optional[str] = None, sender_name: Optional[str] = None) -> Dict:
        """添加消息到历史，返回消息字典（含id）"""
        message = {
            "id": f"msg_{uuid.uuid4().hex[:8]}",
            "role": role,
            "content": content,
            "agent_id": agent_id,
            "sender_name": sender_name or role,
            "timestamp": int(datetime.now().timestamp())
        }
        self.messages.append(message)

        # 保持消息数量在限制内
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

        return message

    def get_messages(self, limit: int = 50) -> List[Dict]:
        """获取最近的消息"""
        return self.messages[-limit:] if limit > 0 else self.messages

    def get_context_for_agent(self, agent_id: str, limit: int = 10) -> str:
        """获取指定Agent的上下文

        Args:
            agent_id: Agent ID
            limit: 返回消息条数

        Returns:
            格式化的上下文字符串
        """
        recent = self.get_messages(limit=limit)
        context_parts = []
        for msg in recent:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:200]  # 截断到200字符
            context_parts.append(f"[{role}]: {content}")
        return "\n".join(context_parts)

    def clear(self):
        """清空消息历史"""
        self.messages.clear()


# 全局内存管理器实例
memory_manager = MemoryManager()