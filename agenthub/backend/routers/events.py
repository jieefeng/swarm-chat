"""SSE事件路由 - Server-Sent Events端点"""
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from agenthub.backend.services.sse_manager import sse_manager

router = APIRouter(prefix="/api", tags=["events"])


@router.get("/events")
async def events(thread_id: Optional[str] = None):
    """SSE 事件流

    Args:
        thread_id: 订阅指定线程的事件。不传则接收所有事件。
    """
    return EventSourceResponse(sse_manager.subscribe(thread_id=thread_id))
