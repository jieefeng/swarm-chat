# 聊天记录持久化与历史会话列表实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现聊天记录的 SQLite 持久化存储和历史会话列表 UI，支持多会话切换。

**Architecture:** 使用 SQLite 存储会话和消息，通过 `aiosqlite` 实现异步操作。前端添加会话列表侧边栏，支持新建、切换、删除会话。

**Tech Stack:** Python, FastAPI, SQLite, aiosqlite, Next.js, TypeScript, Zustand

---

## 文件结构

### 后端文件

| 文件 | 职责 |
|------|------|
| `agenthub/backend/services/sqlite_manager.py` | SQLite 存储管理器（新增） |
| `agenthub/backend/routers/threads.py` | 会话 API 端点（新增） |
| `agenthub/backend/services/memory_manager.py` | 修改：添加 SQLite 支持 |
| `agenthub/backend/main.py` | 修改：注册 threads 路由 |
| `agenthub/backend/requirements.txt` | 修改：添加 aiosqlite 依赖 |

### 前端文件

| 文件 | 职责 |
|------|------|
| `agenthub/frontend/components/threads/ThreadList.tsx` | 会话列表组件（新增） |
| `agenthub/frontend/components/threads/ThreadItem.tsx` | 会话项组件（新增） |
| `agenthub/frontend/components/threads/NewThreadButton.tsx` | 新建会话按钮（新增） |
| `agenthub/frontend/lib/api.ts` | 修改：添加会话 API |
| `agenthub/frontend/lib/stores/threadStore.ts` | 会话状态管理（新增） |
| `agenthub/frontend/app/page.tsx` | 修改：添加会话列表侧边栏 |

### 测试文件

| 文件 | 职责 |
|------|------|
| `agenthub/backend/tests/test_sqlite_manager.py` | SQLite 管理器测试（新增） |
| `agenthub/backend/tests/test_threads_api.py` | 会话 API 测试（新增） |

---

## Task 1: 添加 aiosqlite 依赖

**Files:**
- Modify: `agenthub/backend/requirements.txt`

- [ ] **Step 1: 添加 aiosqlite 依赖**

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
anthropic==0.18.0
openai>=1.0.0
pydantic==2.5.3
python-dotenv==1.0.0
sse-starlette==1.8.2
redis[hiredis]>=5.0.0
fakeredis>=2.21.0
aiosqlite>=0.19.0
```

- [ ] **Step 2: 安装依赖**

Run: `cd agenthub/backend && pip install -r requirements.txt`
Expected: 成功安装 aiosqlite

- [ ] **Step 3: 验证安装**

Run: `python -c "import aiosqlite; print('aiosqlite installed')"`
Expected: 输出 "aiosqlite installed"

- [ ] **Step 4: Commit**

```bash
git add agenthub/backend/requirements.txt
git commit -m "deps: 添加 aiosqlite 依赖"
```

---

## Task 2: 创建 SQLite 管理器

**Files:**
- Create: `agenthub/backend/services/sqlite_manager.py`
- Test: `agenthub/backend/tests/test_sqlite_manager.py`

- [ ] **Step 1: 创建测试文件**

```python
# agenthub/backend/tests/test_sqlite_manager.py
import pytest
import asyncio
from agenthub.backend.services.sqlite_manager import SQLiteManager

@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")

@pytest.fixture
async def manager(db_path):
    mgr = SQLiteManager(db_path)
    await mgr.init_db()
    yield mgr
    await mgr.close()

@pytest.mark.asyncio
async def test_create_thread(manager):
    thread = await manager.create_thread("测试会话")
    assert thread["id"].startswith("thread_")
    assert thread["title"] == "测试会话"
    assert thread["is_pinned"] == 0
    assert thread["is_archived"] == 0

@pytest.mark.asyncio
async def test_get_threads(manager):
    await manager.create_thread("会话 1")
    await manager.create_thread("会话 2")
    threads = await manager.get_threads()
    assert len(threads) == 2
    assert threads[0]["title"] == "会话 2"  # 按 updated_at 降序

@pytest.mark.asyncio
async def test_add_message(manager):
    thread = await manager.create_thread("测试会话")
    msg = await manager.add_message(
        thread_id=thread["id"],
        role="user",
        content="你好",
    )
    assert msg["id"].startswith("msg_")
    assert msg["content"] == "你好"

@pytest.mark.asyncio
async def test_get_messages(manager):
    thread = await manager.create_thread("测试会话")
    await manager.add_message(thread["id"], "user", "消息 1")
    await manager.add_message(thread["id"], "agent", "回复 1")
    messages = await manager.get_messages(thread["id"])
    assert len(messages) == 2
    assert messages[0]["content"] == "消息 1"

@pytest.mark.asyncio
async def test_delete_thread(manager):
    thread = await manager.create_thread("测试会话")
    await manager.add_message(thread["id"], "user", "消息")
    await manager.delete_thread(thread["id"])
    threads = await manager.get_threads()
    assert len(threads) == 0

@pytest.mark.asyncio
async def test_update_thread_title(manager):
    thread = await manager.create_thread("旧标题")
    await manager.update_thread(thread["id"], title="新标题")
    threads = await manager.get_threads()
    assert threads[0]["title"] == "新标题"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd agenthub/backend && python -m pytest tests/test_sqlite_manager.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'agenthub.backend.services.sqlite_manager'"

- [ ] **Step 3: 创建 SQLite 管理器**

```python
# agenthub/backend/services/sqlite_manager.py
"""SQLite 存储管理器 - 会话和消息持久化"""
import uuid
import aiosqlite
from typing import List, Dict, Optional
from datetime import datetime


class SQLiteManager:
    """基于 SQLite 的会话和消息存储管理器"""

    def __init__(self, db_path: str = "agenthub.db"):
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None

    async def init_db(self):
        """初始化数据库连接和表结构"""
        self._db = await aiosqlite.connect(self.db_path)
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute("PRAGMA foreign_keys=ON")
        await self._create_tables()

    async def _create_tables(self):
        """创建会话和消息表"""
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS threads (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                user_id TEXT NOT NULL DEFAULT 'default',
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                is_pinned INTEGER DEFAULT 0,
                is_archived INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                agent_id TEXT,
                sender_name TEXT,
                type TEXT NOT NULL DEFAULT 'user',
                created_at INTEGER NOT NULL,
                FOREIGN KEY (thread_id) REFERENCES threads(id)
            );

            CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON messages(thread_id);
            CREATE INDEX IF NOT EXISTS idx_threads_user_id ON threads(user_id);
            CREATE INDEX IF NOT EXISTS idx_threads_updated_at ON threads(updated_at DESC);
        """)

    async def create_thread(self, title: str, user_id: str = "default") -> Dict:
        """创建新会话"""
        thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        now = int(datetime.now().timestamp())
        await self._db.execute(
            "INSERT INTO threads (id, title, user_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (thread_id, title, user_id, now, now)
        )
        await self._db.commit()
        return {
            "id": thread_id,
            "title": title,
            "user_id": user_id,
            "created_at": now,
            "updated_at": now,
            "is_pinned": 0,
            "is_archived": 0,
        }

    async def get_threads(self, user_id: str = "default", limit: int = 50) -> List[Dict]:
        """获取会话列表（按更新时间降序）"""
        cursor = await self._db.execute(
            """SELECT id, title, user_id, created_at, updated_at, is_pinned, is_archived
               FROM threads
               WHERE user_id = ? AND is_archived = 0
               ORDER BY is_pinned DESC, updated_at DESC
               LIMIT ?""",
            (user_id, limit)
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": row[0],
                "title": row[1],
                "user_id": row[2],
                "created_at": row[3],
                "updated_at": row[4],
                "is_pinned": row[5],
                "is_archived": row[6],
            }
            for row in rows
        ]

    async def get_thread(self, thread_id: str) -> Optional[Dict]:
        """获取单个会话"""
        cursor = await self._db.execute(
            "SELECT id, title, user_id, created_at, updated_at, is_pinned, is_archived FROM threads WHERE id = ?",
            (thread_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "title": row[1],
            "user_id": row[2],
            "created_at": row[3],
            "updated_at": row[4],
            "is_pinned": row[5],
            "is_archived": row[6],
        }

    async def update_thread(self, thread_id: str, **kwargs) -> bool:
        """更新会话属性"""
        allowed = {"title", "is_pinned", "is_archived"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [thread_id]
        await self._db.execute(
            f"UPDATE threads SET {set_clause}, updated_at = ? WHERE id = ?",
            values + [int(datetime.now().timestamp()), thread_id]
        )
        await self._db.commit()
        return True

    async def delete_thread(self, thread_id: str) -> bool:
        """删除会话（级联删除消息）"""
        await self._db.execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
        cursor = await self._db.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
        await self._db.commit()
        return cursor.rowcount > 0

    async def add_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        agent_id: Optional[str] = None,
        sender_name: Optional[str] = None,
    ) -> Dict:
        """添加消息到会话"""
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        now = int(datetime.now().timestamp())
        message_type = "user" if role == "user" else "agent"

        await self._db.execute(
            """INSERT INTO messages (id, thread_id, role, content, agent_id, sender_name, type, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (message_id, thread_id, role, content, agent_id, sender_name or role, message_type, now)
        )

        # 更新会话的 updated_at
        await self._db.execute(
            "UPDATE threads SET updated_at = ? WHERE id = ?",
            (now, thread_id)
        )
        await self._db.commit()

        return {
            "id": message_id,
            "thread_id": thread_id,
            "role": role,
            "content": content,
            "agent_id": agent_id,
            "sender_name": sender_name or role,
            "type": message_type,
            "timestamp": now,
        }

    async def get_messages(self, thread_id: str, limit: int = 50) -> List[Dict]:
        """获取会话内的消息"""
        cursor = await self._db.execute(
            """SELECT id, thread_id, role, content, agent_id, sender_name, type, created_at
               FROM messages
               WHERE thread_id = ?
               ORDER BY created_at ASC
               LIMIT ?""",
            (thread_id, limit)
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": row[0],
                "thread_id": row[1],
                "role": row[2],
                "content": row[3],
                "agent_id": row[4],
                "sender_name": row[5],
                "type": row[6],
                "timestamp": row[7],
            }
            for row in rows
        ]

    async def get_message_count(self, thread_id: str) -> int:
        """获取会话内的消息数量"""
        cursor = await self._db.execute(
            "SELECT COUNT(*) FROM messages WHERE thread_id = ?",
            (thread_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def close(self):
        """关闭数据库连接"""
        if self._db:
            await self._db.close()
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd agenthub/backend && python -m pytest tests/test_sqlite_manager.py -v`
Expected: 所有测试 PASS

- [ ] **Step 5: Commit**

```bash
git add agenthub/backend/services/sqlite_manager.py agenthub/backend/tests/test_sqlite_manager.py
git commit -m "feat: 实现 SQLite 存储管理器"
```

---

## Task 3: 集成 SQLite 到 memory_manager

**Files:**
- Modify: `agenthub/backend/services/memory_manager.py:143-167`

- [ ] **Step 1: 修改 create_memory_manager 函数**

```python
# agenthub/backend/services/memory_manager.py:143-167
def create_memory_manager():
    """根据 STORAGE_BACKEND 环境变量创建对应的 memory manager"""
    backend = os.getenv("STORAGE_BACKEND", "sqlite")  # 默认改为 sqlite
    max_messages = int(os.getenv("MAX_MESSAGES", "1000"))

    if backend == "redis":
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        ttl_days = int(os.getenv("MESSAGE_TTL_DAYS", "30"))
        try:
            import redis as sync_redis
            client = sync_redis.from_url(redis_url, protocol=2)
            client.ping()
            client.close()
            manager = RedisMemoryManager(
                redis_url=redis_url,
                max_messages=max_messages,
                ttl_days=ttl_days,
            )
            logger.info(f"RedisMemoryManager initialized: {redis_url}")
            return manager
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, falling back to sqlite")
            backend = "sqlite"

    if backend == "sqlite":
        from agenthub.backend.services.sqlite_manager import SQLiteManager
        db_path = os.getenv("SQLITE_DB_PATH", "agenthub.db")
        manager = SQLiteManager(db_path=db_path)
        logger.info(f"SQLiteManager initialized: {db_path}")
        return manager

    return MemoryManager(max_messages=max_messages)
```

- [ ] **Step 2: 运行现有测试确保不破坏**

Run: `cd agenthub/backend && python -m pytest tests/ -v`
Expected: 所有测试通过

- [ ] **Step 3: Commit**

```bash
git add agenthub/backend/services/memory_manager.py
git commit -m "feat: 集成 SQLite 到 memory_manager"
```

---

## Task 4: 创建会话 API 端点

**Files:**
- Create: `agenthub/backend/routers/threads.py`
- Test: `agenthub/backend/tests/test_threads_api.py`

- [ ] **Step 1: 创建测试文件**

```python
# agenthub/backend/tests/test_threads_api.py
import pytest
from fastapi.testclient import TestClient
from agenthub.backend.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_create_thread(client):
    response = client.post("/api/threads", json={"title": "测试会话"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"].startswith("thread_")
    assert data["title"] == "测试会话"

def test_get_threads(client):
    # 先创建一个会话
    client.post("/api/threads", json={"title": "会话 1"})
    response = client.get("/api/threads")
    assert response.status_code == 200
    data = response.json()
    assert "threads" in data
    assert len(data["threads"]) >= 1

def test_get_thread_messages(client):
    # 创建会话
    create_resp = client.post("/api/threads", json={"title": "测试会话"})
    thread_id = create_resp.json()["id"]

    # 获取消息（应该为空）
    response = client.get(f"/api/threads/{thread_id}/messages")
    assert response.status_code == 200
    assert response.json()["messages"] == []

def test_delete_thread(client):
    create_resp = client.post("/api/threads", json={"title": "待删除"})
    thread_id = create_resp.json()["id"]

    response = client.delete(f"/api/threads/{thread_id}")
    assert response.status_code == 200

    # 验证已删除
    get_resp = client.get("/api/threads")
    threads = get_resp.json()["threads"]
    assert not any(t["id"] == thread_id for t in threads)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd agenthub/backend && python -m pytest tests/test_threads_api.py -v`
Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: 创建会话路由**

```python
# agenthub/backend/routers/threads.py
"""会话路由 - 提供会话管理 API"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from agenthub.backend.services.memory_manager import (
    memory_manager,
    redis_memory_manager,
)
from agenthub.backend.services.sqlite_manager import SQLiteManager

router = APIRouter(prefix="/api", tags=["threads"])

# 获取存储实例
def get_storage():
    backend = os.getenv("STORAGE_BACKEND", "sqlite")
    if backend == "sqlite":
        from agenthub.backend.services.sqlite_manager import SQLiteManager
        db_path = os.getenv("SQLITE_DB_PATH", "agenthub.db")
        return SQLiteManager(db_path=db_path)
    elif backend == "redis":
        return redis_memory_manager
    return memory_manager


class CreateThreadRequest(BaseModel):
    title: Optional[str] = None


class UpdateThreadRequest(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None


@router.post("/threads")
async def create_thread(req: CreateThreadRequest):
    """创建新会话"""
    storage = get_storage()
    title = req.title or "新会话"

    if isinstance(storage, SQLiteManager):
        await storage.init_db()
        thread = await storage.create_thread(title)
        await storage.close()
        return thread
    else:
        # 内存/Redis 模式：返回模拟数据
        import uuid
        from datetime import datetime
        thread_id = f"thread_{uuid.uuid4().hex[:8]}"
        now = int(datetime.now().timestamp())
        return {
            "id": thread_id,
            "title": title,
            "user_id": "default",
            "created_at": now,
            "updated_at": now,
            "is_pinned": 0,
            "is_archived": 0,
        }


@router.get("/threads")
async def get_threads(limit: int = 50):
    """获取会话列表"""
    storage = get_storage()

    if isinstance(storage, SQLiteManager):
        await storage.init_db()
        threads = await storage.get_threads(limit=limit)
        # 添加消息计数
        for thread in threads:
            thread["message_count"] = await storage.get_message_count(thread["id"])
        await storage.close()
        return {"threads": threads}
    else:
        # 内存/Redis 模式：返回空列表
        return {"threads": []}


@router.get("/threads/{thread_id}/messages")
async def get_thread_messages(thread_id: str, limit: int = 50):
    """获取会话内的消息"""
    storage = get_storage()

    if isinstance(storage, SQLiteManager):
        await storage.init_db()
        thread = await storage.get_thread(thread_id)
        if not thread:
            await storage.close()
            raise HTTPException(status_code=404, detail="会话不存在")
        messages = await storage.get_messages(thread_id, limit=limit)
        await storage.close()
        return {"messages": messages}
    else:
        # 内存/Redis 模式：使用现有 memory_manager
        messages = await memory_manager.get_messages(limit=limit, thread_id=thread_id)
        return {"messages": messages}


@router.patch("/threads/{thread_id}")
async def update_thread(thread_id: str, req: UpdateThreadRequest):
    """更新会话"""
    storage = get_storage()

    if isinstance(storage, SQLiteManager):
        await storage.init_db()
        thread = await storage.get_thread(thread_id)
        if not thread:
            await storage.close()
            raise HTTPException(status_code=404, detail="会话不存在")

        update_data = {}
        if req.title is not None:
            update_data["title"] = req.title
        if req.is_pinned is not None:
            update_data["is_pinned"] = 1 if req.is_pinned else 0

        await storage.update_thread(thread_id, **update_data)
        updated_thread = await storage.get_thread(thread_id)
        await storage.close()
        return updated_thread
    else:
        raise HTTPException(status_code=501, detail="当前存储后端不支持会话更新")


@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """删除会话"""
    storage = get_storage()

    if isinstance(storage, SQLiteManager):
        await storage.init_db()
        deleted = await storage.delete_thread(thread_id)
        await storage.close()
        if not deleted:
            raise HTTPException(status_code=404, detail="会话不存在")
        return {"success": True}
    else:
        raise HTTPException(status_code=501, detail="当前存储后端不支持会话删除")
```

- [ ] **Step 4: 运行测试验证通过**

Run: `cd agenthub/backend && python -m pytest tests/test_threads_api.py -v`
Expected: 所有测试 PASS

- [ ] **Step 5: Commit**

```bash
git add agenthub/backend/routers/threads.py agenthub/backend/tests/test_threads_api.py
git commit -m "feat: 实现会话 API 端点"
```

---

## Task 5: 注册会话路由到 main.py

**Files:**
- Modify: `agenthub/backend/main.py`

- [ ] **Step 1: 添加 threads 路由导入和注册**

```python
# agenthub/backend/main.py
# 在现有路由导入后添加
from agenthub.backend.routers import threads

# 在路由注册处添加
app.include_router(threads.router)
```

- [ ] **Step 2: 启动服务验证**

Run: `cd agenthub/backend && python main.py &`
Run: `curl http://localhost:7010/api/threads`
Expected: 返回 `{"threads": []}`

- [ ] **Step 3: Commit**

```bash
git add agenthub/backend/main.py
git commit -m "feat: 注册会话路由"
```

---

## Task 6: 创建前端会话状态管理

**Files:**
- Create: `agenthub/frontend/lib/stores/threadStore.ts`

- [ ] **Step 1: 创建会话 Store**

```typescript
// agenthub/frontend/lib/stores/threadStore.ts
import { create } from "zustand";

export interface Thread {
  id: string;
  title: string;
  created_at: number;
  updated_at: number;
  is_pinned: boolean;
  is_archived: boolean;
  message_count: number;
}

interface ThreadState {
  threads: Thread[];
  currentThreadId: string | null;
  isLoading: boolean;
  setThreads: (threads: Thread[]) => void;
  addThread: (thread: Thread) => void;
  updateThread: (id: string, updates: Partial<Thread>) => void;
  removeThread: (id: string) => void;
  setCurrentThreadId: (id: string | null) => void;
  setLoading: (v: boolean) => void;
}

export const useThreadStore = create<ThreadState>((set) => ({
  threads: [],
  currentThreadId: null,
  isLoading: false,
  setThreads: (threads) => set({ threads }),
  addThread: (thread) =>
    set((s) => ({ threads: [thread, ...s.threads] })),
  updateThread: (id, updates) =>
    set((s) => ({
      threads: s.threads.map((t) => (t.id === id ? { ...t, ...updates } : t)),
    })),
  removeThread: (id) =>
    set((s) => ({
      threads: s.threads.filter((t) => t.id !== id),
      currentThreadId: s.currentThreadId === id ? null : s.currentThreadId,
    })),
  setCurrentThreadId: (id) => set({ currentThreadId: id }),
  setLoading: (v) => set({ isLoading: v }),
}));
```

- [ ] **Step 2: 验证 TypeScript 编译**

Run: `cd agenthub/frontend && npm run check`
Expected: 无类型错误

- [ ] **Step 3: Commit**

```bash
git add agenthub/frontend/lib/stores/threadStore.ts
git commit -m "feat: 创建会话状态管理 store"
```

---

## Task 7: 添加会话 API 到前端

**Files:**
- Modify: `agenthub/frontend/lib/api.ts`

- [ ] **Step 1: 添加会话 API 方法**

```typescript
// agenthub/frontend/lib/api.ts
// 在 api 对象末尾添加以下方法

async getThreads(limit: number = 50): Promise<{ threads: Thread[] }> {
  const res = await fetch(`${API_BASE}/api/threads?limit=${limit}`, { headers });
  return res.json();
},

async createThread(title?: string): Promise<Thread> {
  const res = await fetch(`${API_BASE}/api/threads`, {
    method: "POST",
    headers,
    body: JSON.stringify({ title }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${res.status}`);
  }
  return res.json();
},

async deleteThread(threadId: string): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE}/api/threads/${threadId}`, {
    method: "DELETE",
    headers,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${res.status}`);
  }
  return res.json();
},

async getThreadMessages(threadId: string, limit: number = 50): Promise<{ messages: Message[] }> {
  const res = await fetch(`${API_BASE}/api/threads/${threadId}/messages?limit=${limit}`, { headers });
  return res.json();
},
```

- [ ] **Step 2: 验证 TypeScript 编译**

Run: `cd agenthub/frontend && npm run check`
Expected: 无类型错误

- [ ] **Step 3: Commit**

```bash
git add agenthub/frontend/lib/api.ts
git commit -m "feat: 添加会话 API 调用"
```

---

## Task 8: 创建会话列表组件

**Files:**
- Create: `agenthub/frontend/components/threads/ThreadList.tsx`
- Create: `agenthub/frontend/components/threads/ThreadItem.tsx`
- Create: `agenthub/frontend/components/threads/NewThreadButton.tsx`

- [ ] **Step 1: 创建 NewThreadButton 组件**

```tsx
// agenthub/frontend/components/threads/NewThreadButton.tsx
"use client";

import { PlusIcon } from "@heroicons/react/24/outline";

interface NewThreadButtonProps {
  onClick: () => void;
  disabled?: boolean;
}

export function NewThreadButton({ onClick, disabled }: NewThreadButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <PlusIcon className="w-4 h-4" />
      新建会话
    </button>
  );
}
```

- [ ] **Step 2: 创建 ThreadItem 组件**

```tsx
// agenthub/frontend/components/threads/ThreadItem.tsx
"use client";

import { TrashIcon } from "@heroicons/react/24/outline";
import type { Thread } from "@/lib/stores/threadStore";

interface ThreadItemProps {
  thread: Thread;
  isActive: boolean;
  onClick: () => void;
  onDelete: () => void;
}

export function ThreadItem({ thread, isActive, onClick, onDelete }: ThreadItemProps) {
  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
    } else if (diffDays === 1) {
      return "昨天";
    } else if (diffDays < 7) {
      return `${diffDays} 天前`;
    } else {
      return date.toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
    }
  };

  return (
    <div
      onClick={onClick}
      className={`group flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer ${
        isActive
          ? "bg-blue-50 border border-blue-200"
          : "hover:bg-gray-50 border border-transparent"
      }`}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-900 truncate">
            {thread.title}
          </span>
          {thread.is_pinned && (
            <span className="text-xs text-blue-600">📌</span>
          )}
        </div>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-gray-500">
            {formatDate(thread.updated_at)}
          </span>
          <span className="text-xs text-gray-400">
            {thread.message_count} 条消息
          </span>
        </div>
      </div>
      <button
        onClick={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500"
      >
        <TrashIcon className="w-4 h-4" />
      </button>
    </div>
  );
}
```

- [ ] **Step 3: 创建 ThreadList 组件**

```tsx
// agenthub/frontend/components/threads/ThreadList.tsx
"use client";

import { useEffect } from "react";
import { NewThreadButton } from "./NewThreadButton";
import { ThreadItem } from "./ThreadItem";
import { useThreadStore } from "@/lib/stores/threadStore";
import { api } from "@/lib/api";

interface ThreadListProps {
  onThreadSelect: (threadId: string) => void;
}

export function ThreadList({ onThreadSelect }: ThreadListProps) {
  const { threads, currentThreadId, isLoading, setThreads, setCurrentThreadId, removeThread, setLoading } =
    useThreadStore();

  useEffect(() => {
    loadThreads();
  }, []);

  const loadThreads = async () => {
    setLoading(true);
    try {
      const data = await api.getThreads();
      setThreads(data.threads || []);
      // 如果没有当前会话，选择第一个
      if (!currentThreadId && data.threads?.length > 0) {
        setCurrentThreadId(data.threads[0].id);
        onThreadSelect(data.threads[0].id);
      }
    } catch (err) {
      console.error("Failed to load threads:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateThread = async () => {
    try {
      const newThread = await api.createThread();
      setThreads([newThread, ...threads]);
      setCurrentThreadId(newThread.id);
      onThreadSelect(newThread.id);
    } catch (err) {
      console.error("Failed to create thread:", err);
    }
  };

  const handleDeleteThread = async (threadId: string) => {
    if (!confirm("确定删除这个会话吗？")) return;
    try {
      await api.deleteThread(threadId);
      removeThread(threadId);
      // 如果删除的是当前会话，选择第一个
      if (currentThreadId === threadId && threads.length > 1) {
        const nextThread = threads.find((t) => t.id !== threadId);
        if (nextThread) {
          setCurrentThreadId(nextThread.id);
          onThreadSelect(nextThread.id);
        }
      }
    } catch (err) {
      console.error("Failed to delete thread:", err);
    }
  };

  const handleThreadClick = (threadId: string) => {
    setCurrentThreadId(threadId);
    onThreadSelect(threadId);
  };

  return (
    <div className="w-64 flex flex-col border-r border-gray-200 bg-gray-50">
      {/* Header */}
      <div className="p-3 border-b border-gray-200">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">会话列表</h2>
        <NewThreadButton onClick={handleCreateThread} disabled={isLoading} />
      </div>

      {/* Thread List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {isLoading ? (
          <div className="text-center text-sm text-gray-500 py-4">加载中...</div>
        ) : threads.length === 0 ? (
          <div className="text-center text-sm text-gray-500 py-4">
            暂无会话，点击上方按钮创建
          </div>
        ) : (
          threads.map((thread) => (
            <ThreadItem
              key={thread.id}
              thread={thread}
              isActive={thread.id === currentThreadId}
              onClick={() => handleThreadClick(thread.id)}
              onDelete={() => handleDeleteThread(thread.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: 验证 TypeScript 编译**

Run: `cd agenthub/frontend && npm run check`
Expected: 无类型错误

- [ ] **Step 5: Commit**

```bash
git add agenthub/frontend/components/threads/
git commit -m "feat: 实现会话列表组件"
```

---

## Task 9: 修改主页集成会话列表

**Files:**
- Modify: `agenthub/frontend/app/page.tsx`

- [ ] **Step 1: 修改主页添加会话列表**

```tsx
// agenthub/frontend/app/page.tsx
"use client";

import { useEffect, useState } from "react";
import { AgentList } from "@/components/agents/AgentList";
import { MessageInput } from "@/components/chat/MessageInput";
import { MessageList } from "@/components/chat/MessageList";
import { ModelEditor } from "@/components/chat/ModelEditor";
import { ThreadList } from "@/components/threads/ThreadList";
import { api } from "@/lib/api";
import { useChatStream } from "@/lib/hooks/useChatStream";
import { useAgentStore } from "@/lib/stores/agentStore";
import { useMessageStore } from "@/lib/stores/messageStore";
import { useThreadStore } from "@/lib/stores/threadStore";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:7005";

export default function HomePage() {
  const [activeAgentId, setActiveAgentId] = useState<string | null>(null);
  const agents = useAgentStore((s) => s.agents);
  const setAgents = useAgentStore((s) => s.setAgents);
  const messages = useMessageStore((s) => s.messages);
  const { sendMessage, connectionState, lastError } = useChatStream({
    agentId: null,
    baseUrl: API_BASE,
  });

  const handleSendMessage = (content: string) => {
    const mentionMatch = content.match(/@(\w+)/);
    if (mentionMatch?.[1]) {
      setActiveAgentId(mentionMatch[1]);
    }
    sendMessage(content);
  };

  const handleThreadSelect = async (threadId: string) => {
    // 加载新会话的消息
    try {
      const data = await api.getThreadMessages(threadId);
      useMessageStore.getState().reset();
      data.messages?.forEach((m) => {
        useMessageStore.getState().addMessage(m);
      });
    } catch (err) {
      console.error("Failed to load thread messages:", err);
    }
  };

  useEffect(() => {
    // 加载初始数据
    const loadData = async () => {
      try {
        const [msgsRes, agentsRes] = await Promise.all([
          api.getMessages(),
          api.getAgents(),
        ]);
        useMessageStore.getState().reset();
        msgsRes.messages?.forEach((m) => {
          useMessageStore.getState().addMessage(m);
        });
        setAgents(agentsRes.agents || []);
      } catch (err) {
        console.error("Failed to load data:", err);
      }
    };
    loadData();
  }, [setAgents]);

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200 bg-white">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-semibold">🐉 AgentHub · 五行神兽</h1>
          {agents.length > 0 && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-400">|</span>
              <span className="text-gray-500">当前模型:</span>
              <ModelEditor
                agentId={
                  activeAgentId && agents.some((a) => a.id === activeAgentId)
                    ? activeAgentId
                    : agents[0]!.id
                }
                agentName={
                  (activeAgentId &&
                    agents.find((a) => a.id === activeAgentId)?.name) ||
                  agents[0]!.name
                }
              />
            </div>
          )}
        </div>
        <div className="text-sm text-gray-500">
          {connectionState === "connected"
            ? "🟢 已连接"
            : connectionState === "connecting"
              ? "🟡 连接中..."
              : "⚪ 空闲"}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* 会话列表侧边栏 */}
        <ThreadList onThreadSelect={handleThreadSelect} />

        {/* 聊天区域 */}
        <div className="flex-1 flex flex-col">
          <AgentList agents={agents} />
          <div className="flex-1 flex flex-col">
            <MessageList messages={messages} agentId={null} />
            <MessageInput
              onSubmit={handleSendMessage}
              disabled={connectionState === "connecting"}
              mentionCandidates={agents.map((a) => ({
                id: a.id,
                label: a.nickname || a.name,
                avatar: a.avatar,
                beast: a.beast,
                element: a.element,
                color: a.color,
              }))}
            />
          </div>
        </div>
      </div>

      {lastError && (
        <div className="absolute bottom-20 left-1/2 transform -translate-x-1/2 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg">
          {lastError}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: 验证 TypeScript 编译**

Run: `cd agenthub/frontend && npm run check`
Expected: 无类型错误

- [ ] **Step 3: Commit**

```bash
git add agenthub/frontend/app/page.tsx
git commit -m "feat: 集成会话列表到主页"
```

---

## Task 10: 端到端测试

**Files:**
- Test: 手动测试

- [ ] **Step 1: 启动后端服务**

Run: `cd agenthub/backend && python main.py`
Expected: 服务启动在 7010 端口

- [ ] **Step 2: 启动前端服务**

Run: `cd agenthub/frontend && npm run dev`
Expected: 前端启动在 7000 端口

- [ ] **Step 3: 测试会话创建**

1. 打开 http://localhost:7000
2. 点击"新建会话"按钮
3. 验证会话列表中出现新会话
4. 发送一条消息
5. 验证会话标题自动更新

- [ ] **Step 4: 测试会话切换**

1. 创建第二个会话
2. 发送消息
3. 切换回第一个会话
4. 验证消息列表显示正确

- [ ] **Step 5: 测试会话删除**

1. 删除一个会话
2. 验证会话从列表中消失
3. 验证自动切换到另一个会话

- [ ] **Step 6: 测试持久化**

1. 刷新页面
2. 验证会话列表保留
3. 验证消息历史保留

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "test: 完成端到端测试"
```

---

## 实现计划完成

**计划已保存到：** `docs/superpowers/plans/2026-06-03-chat-history-plan.md`

**两种执行方式：**

1. **Subagent-Driven（推荐）** - 我为每个任务分发独立的 subagent，任务间进行审查，快速迭代

2. **Inline Execution** - 在当前会话中使用 executing-plans 执行任务，批量执行并设置检查点

**选择哪种方式？**
