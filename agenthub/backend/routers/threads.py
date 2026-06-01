"""线程 API 端点"""
import asyncio

from fastapi import APIRouter, HTTPException

from agenthub.backend.models.thread import (
    Thread, ThreadMessage, CreateThreadRequest, SendMessageRequest
)
from agenthub.backend.services.thread_manager import thread_manager
from agenthub.backend.services.a2a_router import a2a_router


router = APIRouter(prefix="/api/threads", tags=["threads"])


@router.post("", response_model=Thread)
async def create_thread(req: CreateThreadRequest):
    """创建新线程"""
    thread = await thread_manager.create_thread(
        title=req.title,
        created_by="user",
        description=req.description,
    )
    return thread


@router.get("")
async def list_threads(status: str = "active"):
    """获取线程列表"""
    threads = await thread_manager.list_threads(status=status)
    return {"threads": threads}


@router.get("/{thread_id}", response_model=Thread)
async def get_thread(thread_id: str):
    """获取线程详情"""
    thread = await thread_manager.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread


@router.delete("/{thread_id}")
async def archive_thread(thread_id: str):
    """归档线程"""
    success = await thread_manager.archive_thread(thread_id)
    if not success:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {"success": True}


@router.get("/{thread_id}/messages")
async def get_messages(thread_id: str, limit: int = 50):
    """获取线程消息历史"""
    thread = await thread_manager.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    messages = await thread_manager.get_messages(thread_id, limit=limit)
    return {"messages": messages}


@router.post("/{thread_id}/messages")
async def send_message(thread_id: str, req: SendMessageRequest):
    """发送消息到线程"""
    # 1. 验证线程
    thread = await thread_manager.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # 2. 解析 @mention
    cleaned_content, mentions = a2a_router.parse_mentions(req.content)

    # 3. 存储用户消息
    message = await thread_manager.add_message(
        thread_id=thread_id,
        sender_id="user",
        content=req.content,
        mentions=mentions,
        reply_to=req.reply_to,
    )

    # 4. 路由到目标 agent
    targets = await a2a_router.route_message(
        thread_id=thread_id,
        content=req.content,
    )

    # 5. 异步投递给所有目标 agent
    async def deliver_to_targets():
        await asyncio.gather(*[
            a2a_router.deliver_to_agent(
                agent_id=agent_id,
                thread_id=thread_id,
                message=cleaned_content,
            )
            for agent_id in targets
        ])

    asyncio.create_task(deliver_to_targets())

    return {
        "message": message,
        "routed_to": targets,
    }
