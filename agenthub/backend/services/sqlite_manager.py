"""SQLite manager for chat persistence."""

import aiosqlite
import uuid
import time
from typing import Optional


def _generate_id(prefix: str, length: int = 8) -> str:
    """Generate prefixed UUID: thread_xxxxxxxx or msg_xxxxxxxx."""
    return f"{prefix}_{uuid.uuid4().hex[:length]}"


def _now_ms() -> int:
    """Current time in milliseconds (Unix timestamp)."""
    return int(time.time() * 1000)


class SQLiteManager:
    """Async SQLite storage for threads and messages."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

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

    async def create_thread(self, title: str, user_id: str) -> str:
        """Create a new thread and return its ID."""
        thread_id = _generate_id("thread")
        now = _now_ms()

        await self._db.execute(
            "INSERT INTO threads (id, title, user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (thread_id, title, user_id, now, now),
        )
        await self._db.commit()
        return thread_id

    async def get_thread(self, thread_id: str) -> Optional[dict]:
        """Get thread by ID, return None if not found."""
        cursor = await self._db.execute(
            "SELECT * FROM threads WHERE id = ?", (thread_id,)
        )
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    async def get_threads(self, user_id: str, limit: int = 50) -> list[dict]:
        """Get threads for a user, most recently updated first."""
        cursor = await self._db.execute(
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

        await self._db.execute(
            f"UPDATE threads SET {set_clause}, updated_at = ? WHERE id = ?",
            values,
        )
        await self._db.commit()
        return True

    async def delete_thread(self, thread_id: str) -> bool:
        """Delete thread and cascade delete messages. Returns False if not found."""
        existing = await self.get_thread(thread_id)
        if existing is None:
            return False

        await self._db.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
        await self._db.commit()
        return True

    async def add_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        agent_id: Optional[str] = None,
        sender_name: Optional[str] = None,
    ) -> str:
        """Add message to thread and return message ID."""
        msg_id = _generate_id("msg")
        now = _now_ms()

        await self._db.execute(
            "INSERT INTO messages (id, thread_id, role, content, agent_id, sender_name, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (msg_id, thread_id, role, content, agent_id, sender_name, now),
        )
        await self._db.commit()
        return msg_id

    async def get_messages(self, thread_id: str, limit: int = 100) -> list[dict]:
        """Get messages for a thread in chronological order."""
        cursor = await self._db.execute(
            "SELECT * FROM messages WHERE thread_id = ? ORDER BY created_at DESC, ROWID DESC LIMIT ?",
            (thread_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in reversed(rows)]

    async def get_message_count(self, thread_id: str) -> int:
        """Get count of messages in a thread."""
        cursor = await self._db.execute(
            "SELECT COUNT(*) FROM messages WHERE thread_id = ?", (thread_id,)
        )
        row = await cursor.fetchone()
        return row[0]

    async def close(self) -> None:
        """Close database connection."""
        if self._db:
            await self._db.close()
            self._db = None
