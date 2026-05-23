"""消息路由 - 解析@指令和控制消息"""
from typing import List, Optional, Tuple
from .session import AGENT_CONFIGS


class MessageRouter:
    """解析消息中的@指令，返回目标Agent和内容"""

    # 支持的Agent列表 - 从session导入
    AGENTS = list(AGENT_CONFIGS.keys())

    # 终止关键词 - 移除"开始实现"（歧义）
    TERMINATION_KEYWORDS = ["结束讨论", "确认方案", "重新讨论"]

    def __init__(self):
        self.last_parse_result = None

    def parse(self, message: str) -> dict:
        """解析消息，返回路由结果

        Args:
            message: 原始消息字符串

        Returns:
            dict: {
                "target": str or list or None,  # 目标Agent(s)
                "content": str,                  # 实际内容
                "is_broadcast": bool,            # 是否广播
                "is_termination": bool           # 是否终止消息
            }
        """
        result = {
            "target": None,
            "content": message,
            "is_broadcast": False,
            "is_termination": False
        }

        # 检查终止关键词
        for keyword in self.TERMINATION_KEYWORDS:
            if keyword in message:
                result["is_termination"] = True
                result["content"] = message
                break

        # 跳过终止关键词检查进行其他解析
        # 查找@指令
        if message.startswith("@"):
            # 找到第一个空格的位置
            space_idx = message.find(" ")
            if space_idx == -1:
                # @后无空格，返回None
                result["target"] = None
                result["content"] = message
            else:
                # 提取@后的Agent名
                agent_name = message[1:space_idx]
                if agent_name in self.AGENTS:
                    result["target"] = agent_name
                    result["content"] = message[space_idx + 1:]
                else:
                    # 无效的@指令
                    result["target"] = None
                    result["content"] = message
        else:
            # 无@开头，检查是否广播消息（原样返回视为广播）
            if "@" not in message:
                # 广播消息 - 所有Agent
                result["target"] = self.AGENTS
                result["is_broadcast"] = True
                result["content"] = message

        self.last_parse_result = result
        return result

    def route(self, message: str) -> Tuple[Optional[str | List[str]], str, bool, bool]:
        """路由消息的便捷方法

        Returns:
            Tuple of (target, content, is_broadcast, is_termination)
        """
        result = self.parse(message)
        return (
            result["target"],
            result["content"],
            result["is_broadcast"],
            result["is_termination"]
        )