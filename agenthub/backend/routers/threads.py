"""会话 (Thread) 路由 - 提供会话管理 API"""
import os
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from agenthub.backend.services.sqlite_manager import SQLiteManager

router = APIRouter(prefix="/api", tags=["threads"])

# SQLite 存储实例
_db_path = os.getenv("SQLITE_DB_PATH", "agenthub.db")
sqlite_manager = SQLiteManager(db_path=_db_path)
_db_initialized = False


async def _get_db() -> SQLiteManager:
    """确保数据库已初始化"""
    global _db_initialized
    if not _db_initialized:
        await sqlite_manager.init_db()
        _db_initialized = True
    return sqlite_manager


class CreateThreadRequest(BaseModel):
    title: Optional[str] = None


class UpdateThreadRequest(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None


def _generate_thread_id() -> str:
    return f"thread_{uuid.uuid4().hex[:8]}"


def _now_ms() -> int:
    import time
    return int(time.time() * 1000)


@router.get("/threads")
async def get_threads(user_id: str = Query("default"), limit: int = Query(50, ge=1, le=200)):
    """获取会话列表"""
    db = await _get_db()
    threads = await db.get_threads(user_id=user_id, limit=limit)

    # 为每个会话添加 message_count
    result = []
    for thread in threads:
        count = await db.get_message_count(thread["id"])
        thread["message_count"] = count
        thread["is_pinned"] = bool(thread.get("is_pinned", 0))
        thread["is_archived"] = bool(thread.get("is_archived", 0))
        result.append(thread)

    return {"threads": result}


@router.post("/threads", status_code=201)
async def create_thread(req: CreateThreadRequest, user_id: str = Query("default")):
    """创建新会话"""
    db = await _get_db()
    title = req.title or "新会话"
    thread_id = await db.create_thread(title=title, user_id=user_id)

    # 返回创建的会话
    thread = await db.get_thread(thread_id)
    thread["is_pinned"] = bool(thread.get("is_pinned", 0))
    thread["is_archived"] = bool(thread.get("is_archived", 0))
    return thread


@router.patch("/threads/{thread_id}")
async def update_thread(thread_id: str, req: UpdateThreadRequest):
    """更新会话（标题、置顶、归档）"""
    db = await _get_db()

    # 检查会话是否存在
    existing = await db.get_thread(thread_id)
    if existing is None:
        raise HTTPException(status_code=405, detail="Thread not found")

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
    db = await _get_db()

    deleted = await db.delete_thread(thread_id)
    if not deleted:
        raise HTTPException(status_code=405, detail="Thread not found")

    return {"success": True}


@router.get("/threads/{thread_id}/messages")
async def get_thread_messages(
    thread_id: str,
    limit: int = Query(50, ge=1, le=200),
):
    """获取会话内的消息"""
    db = await _get_db()

    # 检查会话是否存在
    existing = await db.get_thread(thread_id)
    if existing is None:
        raise HTTPException(status_code=405, detail="Thread not found")

    messages = await db.get_messages(thread_id=thread_id, limit=limit)
    return {"messages": messages}
