"""SQLite manager for chat persistence."""

import aiosqlite
import logging
import sqlite3
import uuid
import time
from typing import Optional

logger = logging.getLogger(__name__)

# 连接失效时自动重试的操作错误码
_RETRYABLE_ERRORS = ("database is locked", "database disk image is malformed")


def _generate_id(prefix: str, length: int = 8) -> str:
    """Generate prefixed UUID: thread_xxxxxxxx or msg_xxxxxxxx."""
    return f"{prefix}_{uuid.uuid4().hex[:length]}"


def _now_ms() -> int:
    """Current time in milliseconds since Unix epoch."""
    return int(time.time() * 1000)


def _require_db(db: Optional[aiosqlite.Connection]) -> aiosqlite.Connection:
    """Guard against None _db. Raises RuntimeError if not initialized."""
    if db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return db


class SQLiteManager:
    """Async SQLite storage for threads and messages.

    自动处理连接失效：当 SQLite 返回 'database is locked' 或
    'database disk image is malformed' 时，关闭旧连接并重建，
    然后重试操作一次。
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def __aenter__(self) -> "SQLiteManager":
        await self.init_db()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def init_db(self) -> None:
        """Initialize database connection and create tables."""
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA foreign_keys=ON")

        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS threads (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                user_id TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                is_pinned INTEGER NOT NULL DEFAULT 0,
                is_archived INTEGER NOT NULL DEFAULT 0
            )
        """)

        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                agent_id TEXT,
                sender_name TEXT,
                type TEXT DEFAULT 'text',
                created_at INTEGER NOT NULL,
                FOREIGN KEY (thread_id) REFERENCES threads(id) ON DELETE CASCADE
            )
        """)

        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON messages(thread_id)
        """)
        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_threads_user_id ON threads(user_id)
        """)

        await self._db.commit()

    async def _reconnect(self) -> None:
        """关闭旧连接并重建数据库连接。"""
        logger.warning("Reconnecting to SQLite database: %s", self.db_path)
        if self._db:
            try:
                await self._db.close()
            except Exception:
                pass
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA foreign_keys=ON")

    async def _run_with_retry(self, coro_factory):
        """执行数据库操作，遇到可重试错误时自动重连并重试一次。

        Args:
            coro_factory: 返回协程的无参工厂函数，每次调用产生一个新的操作。
        """
        try:
            return await coro_factory()
        except sqlite3.OperationalError as e:
            if any(msg in str(e) for msg in _RETRYABLE_ERRORS):
                logger.warning("Retryable SQLite error: %s — reconnecting", e)
                await self._reconnect()
                return await coro_factory()
            raise

    async def create_thread(self, title: str, user_id: str) -> str:
        """Create a new thread and return its ID."""
        async def _op():
            db = _require_db(self._db)
            thread_id = _generate_id("thread")
            now = _now_ms()
            await db.execute(
                "INSERT INTO threads (id, title, user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (thread_id, title, user_id, now, now),
            )
            await db.commit()
            return thread_id
        return await self._run_with_retry(_op)

    async def get_thread(self, thread_id: str) -> Optional[dict]:
        """Get thread by ID, return None if not found."""
        db = _require_db(self._db)
        cursor = await db.execute(
            "SELECT * FROM threads WHERE id = ?", (thread_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    async def get_threads(self, user_id: str, limit: int = 50) -> list[dict]:
        """Get threads for a user, most recently updated first."""
        db = _require_db(self._db)
        cursor = await db.execute(
            "SELECT * FROM threads WHERE user_id = ? ORDER BY updated_at DESC, ROWID DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def update_thread(self, thread_id: str, **kwargs) -> bool:
        """Update thread fields. Returns False if thread not found."""
        if not kwargs:
            return False

        existing = await self.get_thread(thread_id)
        if existing is None:
            return False

        allowed = {"title", "is_pinned", "is_archived"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False

        now = _now_ms()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [now, thread_id]

        async def _op():
            db = _require_db(self._db)
            await db.execute(
                f"UPDATE threads SET {set_clause}, updated_at = ? WHERE id = ?",
                values,
            )
            await db.commit()
        await self._run_with_retry(_op)
        return True

    async def delete_thread(self, thread_id: str) -> bool:
        """Delete thread and cascade delete messages. Returns False if not found."""
        existing = await self.get_thread(thread_id)
        if existing is None:
            return False

        async def _op():
            db = _require_db(self._db)
            await db.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
            await db.commit()
        await self._run_with_retry(_op)
        return True

    async def delete_all_except(self, keep_thread_id: str) -> int:
        """删除除指定会话外的所有会话（级联删除消息）。

        Returns: 删除的会话数量
        """
        async def _op():
            db = _require_db(self._db)
            cursor = await db.execute(
                "DELETE FROM threads WHERE id != ?", (keep_thread_id,)
            )
            await db.commit()
            return cursor.rowcount
        return await self._run_with_retry(_op)

    async def add_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        agent_id: Optional[str] = None,
        sender_name: Optional[str] = None,
    ) -> str:
        """Add message to thread and return message ID."""
        async def _op():
            db = _require_db(self._db)
            msg_id = _generate_id("msg")
            now = _now_ms()
            await db.execute(
                "INSERT INTO messages (id, thread_id, role, content, agent_id, sender_name, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (msg_id, thread_id, role, content, agent_id, sender_name, now),
            )
            await db.commit()
            return msg_id
        return await self._run_with_retry(_op)

    async def get_messages(self, thread_id: str, limit: int = 100) -> list[dict]:
        """Get messages for a thread in chronological order."""
        db = _require_db(self._db)
        cursor = await db.execute(
            "SELECT * FROM messages WHERE thread_id = ? ORDER BY created_at DESC, ROWID DESC LIMIT ?",
            (thread_id, limit),
        )
        rows = await cursor.fetchall()
        messages = []
        for row in list(reversed(rows)):
            msg = dict(row)
            # 根据 role 字段设置前端需要的 type 字段
            # role = "user" -> type = "user" (用户消息，显示在右边)
            # 其他 role (agent_id) -> type = "agent" (Agent 消息，显示在左边)
            msg["type"] = "user" if msg.get("role") == "user" else "agent"
            messages.append(msg)
        return messages

    async def get_message_count(self, thread_id: str) -> int:
        """Get count of messages in a thread."""
        db = _require_db(self._db)
        cursor = await db.execute(
            "SELECT COUNT(*) FROM messages WHERE thread_id = ?", (thread_id,)
        )
        row = await cursor.fetchone()
        return row[0]

    async def get_threads_with_message_count(self, user_id: str, limit: int = 50) -> list[dict]:
        """Get threads for a user with message count, using a single JOIN query."""
        db = _require_db(self._db)
        cursor = await db.execute(
            """
            SELECT t.*, COUNT(m.id) as message_count
            FROM threads t
            LEFT JOIN messages m ON m.thread_id = t.id
            WHERE t.user_id = ?
            GROUP BY t.id
            ORDER BY t.updated_at DESC, t.ROWID DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def close(self) -> None:
        """Close database connection."""
        if self._db:
            await self._db.close()
            self._db = None
