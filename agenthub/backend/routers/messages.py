"""消息路由 - 提供消息历史和Agent列表API"""
import uuid
import asyncio
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from services.session import AGENT_CONFIGS, session_manager
from services.memory_manager import memory_manager
from services.sse_manager import sse_manager
from services.router import MessageRouter

router = APIRouter(prefix="/api", tags=["messages"])

# 初始化消息路由器
message_router = MessageRouter()


class SendMessageRequest(BaseModel):
    content: str
    sender: str = "user"
    sender_name: str = "用户"


class MessageRequest(BaseModel):
    role: str
    content: str
    agent_id: Optional[str] = None


class MessageResponse(BaseModel):
    role: str
    content: str
    agent_id: Optional[str] = None
    timestamp: str


class AgentInfo(BaseModel):
    id: str
    name: str
    role: str


@router.post("/messages")
async def send_message(req: SendMessageRequest):
    """发送消息并路由到相应Agent

    1. 解析@指令，确定目标Agent
    2. 推送用户消息到SSE
    3. 检测终止关键词
    4. 并行发送消息给目标Agent
    5. 推送Agent响应到SSE
    """
    route_result = message_router.parse(req.content)

    # 添加用户消息到memory
    user_msg = memory_manager.add_message(
        role=req.sender,
        content=req.content,
        agent_id=req.sender
    )

    # 推送用户消息到SSE
    await sse_manager.broadcast("message", user_msg)

    # 检查终止信号
    if route_result["is_termination"]:
        await sse_manager.broadcast("termination", {
            "keyword": route_result["content"],
            "message_id": user_msg.get("id", "")
        })
        return {
            "success": True,
            "message_id": user_msg.get("id", ""),
            "is_termination": True
        }

    # 获取目标Agent列表
    targets = route_result["target"]
    if not targets:
        targets = list(AGENT_CONFIGS.keys())

    # 并行发送消息给Agent
    async def send_to_single_agent(agent_id: str) -> dict:
        """发送消息给单个Agent"""
        config = AGENT_CONFIGS.get(agent_id)
        if not config:
            return None

        try:
            context = memory_manager.get_context_for_agent(agent_id)
            agent_message = f"上下文参考:\n{context}\n\n用户消息: {route_result['content']}" if context else route_result['content']

            response = session_manager.send_to_agent(agent_id, agent_message)

            agent_msg = memory_manager.add_message(
                role=agent_id,
                content=response,
                agent_id=agent_id
            )

            await sse_manager.broadcast("message", agent_msg)
            return agent_msg

        except Exception as e:
            error_msg = memory_manager.add_message(
                role=agent_id,
                content=f"Error: {str(e)}",
                agent_id=agent_id
            )
            await sse_manager.broadcast("message", error_msg)
            return error_msg

    # 使用asyncio.gather并行处理所有Agent
    await asyncio.gather(*[send_to_single_agent(agent_id) for agent_id in targets])

    return {
        "success": True,
        "message_id": user_msg.get("id", ""),
        "is_broadcast": route_result["is_broadcast"]
    }