"""消息模型定义"""
from pydantic import BaseModel
from typing import Optional


class Message(BaseModel):
    """消息模型

    Attributes:
        id: 消息唯一标识
        sender: 发送者ID: "pm", "architect", "user"
        sender_name: 显示名称
        content: 消息内容
        timestamp: Unix时间戳
        type: 消息类型: "user" | "agent"
    """
    id: str
    sender: str
    sender_name: str
    content: str
    timestamp: int
    type: str


class SendMessageRequest(BaseModel):
    """发送消息请求

    Attributes:
        content: 消息内容
        sender: 发送者ID，默认为"user"
        sender_name: 显示名称，默认为"用户"
    """
    content: str
    sender: str = "user"
    sender_name: str = "用户"