"""SSE事件路由 - Server-Sent Events端点"""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from services.sse_manager import sse_manager

router = APIRouter(prefix="/api", tags=["events"])


@router.get("/events")
async def events():
    """SSE事件流端点

    建立SSE连接，订阅所有消息事件和终止事件。
    客户端可通过EventSource API连接。
    """
    async def event_generator():
        async for event in sse_manager.subscribe():
            yield event

    return EventSourceResponse(event_generator())