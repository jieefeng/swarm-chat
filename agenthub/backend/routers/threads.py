"""会话 (Thread) 路由 - 提供会话管理 API"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from agenthub.backend.services.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["threads"])


class CreateThreadRequest(BaseModel):
    title: Optional[str] = None


class UpdateThreadRequest(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None


@router.get("/threads")
async def get_threads(user_id: str = Query("default"), limit: int = Query(50, ge=1, le=200)):
    """获取会话列表（使用 JOIN 查询避免 N+1 问题）"""
    db = await get_db()
    threads = await db.get_threads_with_message_count(user_id=user_id, limit=limit)

    # 转换布尔字段
    result = []
    for thread in threads:
        thread["is_pinned"] = bool(thread.get("is_pinned", 0))
        thread["is_archived"] = bool(thread.get("is_archived", 0))
        result.append(thread)

    return {"threads": result}


@router.post("/threads", status_code=201)
async def create_thread(req: CreateThreadRequest, user_id: str = Query("default")):
    """创建新会话"""
    try:
        db = await get_db()
        title = req.title or "新会话"
        thread_id = await db.create_thread(title=title, user_id=user_id)

        # 返回创建的会话
        thread = await db.get_thread(thread_id)
        thread["is_pinned"] = bool(thread.get("is_pinned", 0))
        thread["is_archived"] = bool(thread.get("is_archived", 0))
        return thread
    except Exception as e:
        logger.exception("Failed to create thread")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/threads/{thread_id}")
async def update_thread(thread_id: str, req: UpdateThreadRequest):
    """更新会话（标题、置顶、归档）"""
    db = await get_db()

    # 检查会话是否存在
    existing = await db.get_thread(thread_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    # 构建更新参数
    update_fields = {}
    if req.title is not None:
        update_fields["title"] = req.title
    if req.is_pinned is not None:
        update_fields["is_pinned"] = 1 if req.is_pinned else 0
    if req.is_archived is not None:
        update_fields["is_archived"] = 1 if req.is_archived else 0

    if update_fields:
        await db.update_thread(thread_id, **update_fields)

    # 返回更新后的会话
    thread = await db.get_thread(thread_id)
    thread["is_pinned"] = bool(thread.get("is_pinned", 0))
    thread["is_archived"] = bool(thread.get("is_archived", 0))
    return thread


@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """删除会话（级联删除消息）"""
    db = await get_db()

    deleted = await db.delete_thread(thread_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Thread not found")

    return {"success": True}


@router.delete("/threads")
async def delete_all_threads(keep: str = Query(..., description="要保留的会话 ID")):
    """清理除指定会话外的所有会话（包括置顶的）"""
    db = await get_db()

    # 验证 keep 指向的会话存在
    existing = await db.get_thread(keep)
    if existing is None:
        raise HTTPException(status_code=404, detail="Thread to keep not found")

    deleted_count = await db.delete_all_except(keep)
    return {"success": True, "deleted_count": deleted_count}


@router.get("/threads/{thread_id}/messages")
async def get_thread_messages(
    thread_id: str,
    limit: int = Query(50, ge=1, le=200),
):
    """获取会话内的消息"""
    db = await get_db()

    # 检查会话是否存在
    existing = await db.get_thread(thread_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    messages = await db.get_messages(thread_id=thread_id, limit=limit)
    return {"messages": messages}
