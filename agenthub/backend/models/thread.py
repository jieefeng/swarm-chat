"""线程相关数据模型"""
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class Thread(BaseModel):
    """线程模型

    每个线程是一个独立的工作空间，对应一个功能/bug/话题。

    Attributes:
        id: 线程唯一标识
        title: 线程标题
        description: 可选描述
        created_by: 创建者 ("user" 或 agent_id)
        participants: 参与的 agent ID 列表
        status: 状态 (active/archived)
        created_at: 创建时间
        updated_at: 更新时间
    """
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str
    description: str | None = None
    created_by: str = "user"
    participants: list[str] = Field(default_factory=list)
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ThreadMessage(BaseModel):
    """线程消息模型

    Attributes:
        id: 消息唯一标识
        thread_id: 所属线程 ID
        sender_id: 发送者 ("user" 或 agent_id)
        content: 消息内容
        mentions: @mention 的 agent ID 列表
        reply_to: 回复的消息 ID (可选)
        created_at: 创建时间
    """
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    thread_id: str
    sender_id: str
    content: str
    mentions: list[str] = Field(default_factory=list)
    reply_to: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)


class CreateThreadRequest(BaseModel):
    """创建线程请求"""
    title: str
    description: str | None = None


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    content: str
    reply_to: str | None = None
