"""Callbacks 路由 - Agent HTTP callback API 端点"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from agenthub.backend.services.callback_router import callback_router

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/callbacks", tags=["callbacks"])


class PostMessageRequest(BaseModel):
    """post-message 请求体"""

    invocation_id: str
    callback_token: str
    content: str
    target_agent_id: Optional[str] = None


@router.post("/post-message")
async def post_message(req: PostMessageRequest):
    """Agent 发送消息给团队（可选 @mention 目标 Agent）"""
    try:
        return await callback_router.post_message(
            invocation_id=req.invocation_id,
            callback_token=req.callback_token,
            content=req.content,
            target_agent_id=req.target_agent_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/thread-context")
async def thread_context(
    invocation_id: str = Query(...),
    callback_token: str = Query(...),
):
    """获取当前 thread 的对话上下文"""
    try:
        return await callback_router.get_thread_context(
            invocation_id=invocation_id,
            callback_token=callback_token,
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/pending-mentions")
async def pending_mentions(
    invocation_id: str = Query(...),
    callback_token: str = Query(...),
):
    """获取当前 thread 中 @提及该 Agent 的消息"""
    try:
        return await callback_router.get_pending_mentions(
            invocation_id=invocation_id,
            callback_token=callback_token,
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
