# Redis 聊天记录存储 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 MemoryManager 从纯内存存储改造为支持 Redis List 持久化存储，实现按用户隔离和自动过期清理。

**Architecture:** 在 `memory_manager.py` 中新增 `RedisMemoryManager` 类（async 接口），通过 `STORAGE_BACKEND` 环境变量切换存储后端。Redis 不可用时自动降级到内存模式。`messages.py` 中的调用改为 async，`SendMessageRequest` 新增 `user_id` 字段。

**Tech Stack:** Python 3.10+, FastAPI, redis-py (async), fakeredis (测试)

---

### Task 1: 添加依赖

**Files:**
- Modify: `agenthub/backend/requirements.txt`
- Modify: `agenthub/backend/.env.example`

- [ ] **Step 1: 在 requirements.txt 中添加 redis 依赖**

在 `agenthub/backend/requirements.txt` 末尾添加：

```
redis[hiredis]>=5.0.0
fakeredis>=2.21.0
```

- [ ] **Step 2: 更新 .env.example 添加 Redis 配置项**

在 `agenthub/backend/.env.example` 末尾添加：

```bash
# Redis 配置（可选，不配置则使用内存存储）
REDIS_URL=redis://localhost:6379
STORAGE_BACKEND=memory
MESSAGE_TTL_DAYS=30
MAX_MESSAGES=1000
```

- [ ] **Step 3: 安装依赖并验证**

Run: `cd agenthub/backend && pip install -r requirements.txt`
Expected: 安装成功，无报错

- [ ] **Step 4: Commit**

```bash
git add agenthub/backend/requirements.txt agenthub/backend/.env.example
git commit -m "chore: add redis and fakeredis dependencies"
```

---

### Task 2: 实现 RedisMemoryManager 类

**Files:**
- Modify: `agenthub/backend/services/memory_manager.py`

- [ ] **Step 1: 实现 RedisMemoryManager**

在 `memory_manager.py` 末尾（现有 `MemoryManager` 类和 `memory_manager` 实例之后）添加：

```python
import os
import json
import logging

logger = logging.getLogger(__name__)


class RedisMemoryManager:
    """基于 Redis List 的消息存储管理器"""

    def __init__(self, redis_url: str = "redis://localhost:6379",
                 max_messages: int = 1000, ttl_days: int = 30):
        import redis.asyncio as aioredis
        self.redis = aioredis.from_url(redis_url, decode_responses=True)
        self.max_messages = max_messages
        self.ttl_seconds = ttl_days * 86400

    def _key(self, user_id: str) -> str:
        return f"chat:messages:{user_id}"

    async def add_message(self, role: str, content: str,
                          user_id: str = "default",
                          agent_id: Optional[str] = None,
                          sender_name: Optional[str] = None) -> Dict:
        message = {
            "id": f"msg_{uuid.uuid4().hex[:8]}",
            "role": role,
            "content": content,
            "agent_id": agent_id,
            "sender_name": sender_name or role,
            "timestamp": int(datetime.now().timestamp()),
            "type": "user" if role == "user" else "agent",
        }
        key = self._key(user_id)
        await self.redis.lpush(key, json.dumps(message, ensure_ascii=False))
        await self.redis.ltrim(key, 0, self.max_messages - 1)
        await self.redis.expire(key, self.ttl_seconds)
        return message

    async def get_messages(self, user_id: str = "default",
                           limit: int = 50) -> List[Dict]:
        key = self._key(user_id)
        raw = await self.redis.lrange(key, 0, limit - 1)
        return [json.loads(item) for item in reversed(raw)]

    async def get_context_for_agent(self, agent_id: str,
                                     user_id: str = "default",
                                     limit: int = 10) -> str:
        recent = await self.get_messages(user_id=user_id, limit=limit)
        context_parts = []
        for msg in recent:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]
            context_parts.append(f"[{role}]: {content}")
        return "\n".join(context_parts)

    async def clear(self, user_id: str = "default"):
        await self.redis.delete(self._key(user_id))

    async def close(self):
        await self.redis.close()
```

- [ ] **Step 2: 添加后端选择逻辑和全局实例**

在 `memory_manager.py` 的 `memory_manager = MemoryManager()` 之后添加：

```python
def create_memory_manager():
    """根据 STORAGE_BACKEND 环境变量创建对应的 memory manager"""
    backend = os.getenv("STORAGE_BACKEND", "memory")
    if backend == "redis":
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        max_messages = int(os.getenv("MAX_MESSAGES", "1000"))
        ttl_days = int(os.getenv("MESSAGE_TTL_DAYS", "30"))
        try:
            manager = RedisMemoryManager(
                redis_url=redis_url,
                max_messages=max_messages,
                ttl_days=ttl_days,
            )
            logger.info(f"RedisMemoryManager initialized: {redis_url}")
            return manager
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}, falling back to memory")
            return MemoryManager(max_messages=max_messages)
    return MemoryManager(max_messages=int(os.getenv("MAX_MESSAGES", "1000")))


redis_memory_manager = create_memory_manager()
```

- [ ] **Step 3: 验证导入无报错**

Run: `cd agenthub/backend && python -c "from agenthub.backend.services.memory_manager import memory_manager, redis_memory_manager; print('OK')"`
Expected: `OK`（如果 Redis 未运行，会打印警告并降级到内存模式）

- [ ] **Step 4: Commit**

```bash
git add agenthub/backend/services/memory_manager.py
git commit -m "feat: add RedisMemoryManager with fallback to in-memory"
```

---

### Task 3: 编写 RedisMemoryManager 单元测试

**Files:**
- Create: `agenthub/backend/tests/test_redis_memory.py`

- [ ] **Step 1: 编写测试文件**

创建 `agenthub/backend/tests/test_redis_memory.py`：

```python
"""RedisMemoryManager 单元测试（使用 fakeredis）"""
import pytest
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import fakeredis.aioredis
from agenthub.backend.services.memory_manager import RedisMemoryManager


@pytest.fixture
async def redis_memory():
    """创建使用 fakeredis 的 RedisMemoryManager 实例"""
    fake_server = fakeredis.aioredis.FakeServer()
    client = fakeredis.aioredis.FakeRedis(server=fake_server, decode_responses=True)
    manager = RedisMemoryManager.__new__(RedisMemoryManager)
    manager.redis = client
    manager.max_messages = 1000
    manager.ttl_seconds = 30 * 86400
    yield manager
    await client.close()


class TestRedisMemoryManager:
    """RedisMemoryManager 测试类"""

    @pytest.mark.asyncio
    async def test_add_user_message(self, redis_memory):
        """添加用户消息后，消息包含正确的字段"""
        msg = await redis_memory.add_message(role="user", content="你好")
        assert msg["role"] == "user"
        assert msg["content"] == "你好"
        assert msg["type"] == "user"
        assert "id" in msg
        assert "timestamp" in msg

    @pytest.mark.asyncio
    async def test_add_agent_message(self, redis_memory):
        """添加 Agent 消息后，type 为 agent"""
        msg = await redis_memory.add_message(
            role="agent", content="我是助手", agent_id="pm",
            sender_name="产品经理"
        )
        assert msg["role"] == "agent"
        assert msg["type"] == "agent"
        assert msg["agent_id"] == "pm"
        assert msg["sender_name"] == "产品经理"

    @pytest.mark.asyncio
    async def test_get_messages_returns_latest(self, redis_memory):
        """get_messages 返回最近的消息，按时间正序"""
        for i in range(5):
            await redis_memory.add_message(role="user", content=f"消息{i}")
        messages = await redis_memory.get_messages(limit=3)
        assert len(messages) == 3
        assert messages[0]["content"] == "消息2"
        assert messages[2]["content"] == "消息4"

    @pytest.mark.asyncio
    async def test_max_messages_trim(self, redis_memory):
        """超过 max_messages 后，旧消息被淘汰"""
        redis_memory.max_messages = 10
        for i in range(15):
            await redis_memory.add_message(role="user", content=f"消息{i}")
        messages = await redis_memory.get_messages(limit=50)
        assert len(messages) == 10
        assert messages[-1]["content"] == "消息14"

    @pytest.mark.asyncio
    async def test_user_isolation(self, redis_memory):
        """不同用户的消息互相隔离"""
        await redis_memory.add_message(role="user", content="用户A的消息", user_id="user_a")
        await redis_memory.add_message(role="user", content="用户B的消息", user_id="user_b")
        msgs_a = await redis_memory.get_messages(user_id="user_a")
        msgs_b = await redis_memory.get_messages(user_id="user_b")
        assert len(msgs_a) == 1
        assert len(msgs_b) == 1
        assert msgs_a[0]["content"] == "用户A的消息"
        assert msgs_b[0]["content"] == "用户B的消息"

    @pytest.mark.asyncio
    async def test_clear(self, redis_memory):
        """clear 删除指定用户的所有消息"""
        await redis_memory.add_message(role="user", content="测试", user_id="u1")
        await redis_memory.clear(user_id="u1")
        messages = await redis_memory.get_messages(user_id="u1")
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_get_context_for_agent(self, redis_memory):
        """get_context_for_agent 返回格式化的上下文字符串"""
        await redis_memory.add_message(role="user", content="你好")
        await redis_memory.add_message(role="agent", content="你好，我是PM", agent_id="pm")
        context = await redis_memory.get_context_for_agent(agent_id="pm", limit=5)
        assert "[user]: 你好" in context
        assert "[agent]: 你好，我是PM" in context

    @pytest.mark.asyncio
    async def test_default_user_id(self, redis_memory):
        """不指定 user_id 时使用 default"""
        await redis_memory.add_message(role="user", content="默认用户")
        messages = await redis_memory.get_messages()
        assert len(messages) == 1
        assert messages[0]["content"] == "默认用户"
```

- [ ] **Step 2: 运行测试验证通过**

Run: `cd agenthub/backend && python -m pytest tests/test_redis_memory.py -v`
Expected: 全部 PASS

- [ ] **Step 3: Commit**

```bash
git add agenthub/backend/tests/test_redis_memory.py
git commit -m "test: add RedisMemoryManager unit tests with fakeredis"
```

---

### Task 4: 更新 messages.py 支持 async 和后端切换

**Files:**
- Modify: `agenthub/backend/routers/messages.py`

- [ ] **Step 1: 修改导入逻辑，支持后端切换**

将 `messages.py` 第 9 行：

```python
from agenthub.backend.services.memory_manager import memory_manager
```

替换为：

```python
import os
from agenthub.backend.services.memory_manager import (
    memory_manager,
    redis_memory_manager,
)

# 根据 STORAGE_BACKEND 选择存储实例
memory = redis_memory_manager if os.getenv("STORAGE_BACKEND") == "redis" else memory_manager
```

- [ ] **Step 2: SendMessageRequest 添加 user_id 字段**

将 `SendMessageRequest` 模型（第 21-25 行）：

```python
class SendMessageRequest(BaseModel):
    content: str
    sender: str = "user"
    sender_name: str = "用户"
    agent_id: Optional[str] = None  # 前端指定的Agent ID
```

替换为：

```python
class SendMessageRequest(BaseModel):
    content: str
    sender: str = "user"
    sender_name: str = "用户"
    agent_id: Optional[str] = None
    user_id: str = "default"
```

- [ ] **Step 3: 将所有 memory_manager 调用改为 await memory 调用**

将文件中所有 `memory_manager.` 替换为 `await memory.`，涉及以下位置：

1. 第 60 行 `get_messages` 端点：`memory_manager.get_messages(limit=limit)` → `await memory.get_messages(limit=limit)`
2. 第 78 行 `send_message` 中：`memory_manager.add_message(` → `await memory.add_message(`
3. 第 150 行 orchestrator 错误处理：`memory_manager.add_message(` → `await memory.add_message(`
4. 第 172 行 `get_context_for_agent`：`memory_manager.get_context_for_agent(agent_id)` → `await memory.get_context_for_agent(agent_id, user_id=req.user_id)`
5. 第 206 行流式完成：`memory_manager.add_message(` → `await memory.add_message(`
6. 第 219 行错误处理：`memory_manager.add_message(` → `await memory.add_message(`

同时在所有 `add_message` 调用中添加 `user_id=req.user_id` 参数。

具体改动：

**get_messages 端点（约第 58-61 行）：**
```python
@router.get("/messages")
async def get_messages(limit: int = Query(50, ge=1, le=200)):
    """获取消息历史"""
    messages = await memory.get_messages(limit=limit)
    return {"messages": messages}
```

**send_message 中用户消息添加（约第 78-83 行）：**
```python
    user_msg = await memory.add_message(
        role=req.sender,
        content=req.content,
        user_id=req.user_id,
        agent_id=req.sender,
        sender_name=req.sender_name
    )
```

**orchestrator 错误处理（约第 150-155 行）：**
```python
            error_msg = await memory.add_message(
                role="orchestrator",
                content=f"协调器处理失败: {str(e)}",
                user_id=req.user_id,
                agent_id="orchestrator",
                sender_name="协调器"
            )
```

**send_to_single_agent 中的 context 获取（约第 172 行）：**
```python
            context = await memory.get_context_for_agent(agent_id, user_id=req.user_id)
```

**流式完成后的消息存储（约第 206-211 行）：**
```python
            agent_msg = await memory.add_message(
                role=agent_id,
                content=full_response,
                user_id=req.user_id,
                agent_id=agent_id,
                sender_name=agent_name
            )
```

**错误处理中的消息存储（约第 219-223 行）：**
```python
            error_msg = await memory.add_message(
                role=agent_id,
                content=f"Error: {str(e)}",
                user_id=req.user_id,
                agent_id=agent_id,
                sender_name=agent_name
            )
```

- [ ] **Step 4: 验证语法无误**

Run: `cd agenthub/backend && python -c "from agenthub.backend.routers.messages import router; print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add agenthub/backend/routers/messages.py
git commit -m "feat: integrate RedisMemoryManager into message routes with user_id support"
```

---

### Task 5: 更新现有测试适配 async 接口

**Files:**
- Modify: `agenthub/backend/tests/test_memory.py`

- [ ] **Step 1: 验证现有测试仍然通过**

由于 `MemoryManager` 类本身接口未改（仍是同步），现有测试无需改动。

Run: `cd agenthub/backend && python -m pytest tests/test_memory.py -v`
Expected: 全部 PASS

- [ ] **Step 2: Commit（如有改动）**

如果测试需要调整，则提交；否则跳过此步骤。

---

### Task 6: 编写降级测试

**Files:**
- Create: `agenthub/backend/tests/test_memory_fallback.py`

- [ ] **Step 1: 编写降级测试**

创建 `agenthub/backend/tests/test_memory_fallback.py`：

```python
"""存储后端降级测试"""
import pytest
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMemoryFallback:
    """测试 Redis 不可用时的降级行为"""

    def test_redis_fallback_on_connection_error(self):
        """Redis 连接失败时降级到内存模式"""
        from agenthub.backend.services.memory_manager import (
            MemoryManager, create_memory_manager
        )
        with patch.dict(os.environ, {
            "STORAGE_BACKEND": "redis",
            "REDIS_URL": "redis://invalid-host:6379"
        }):
            manager = create_memory_manager()
            # 应该降级为 MemoryManager
            assert isinstance(manager, MemoryManager)
```

- [ ] **Step 2: 运行测试**

Run: `cd agenthub/backend && python -m pytest tests/test_memory_fallback.py -v`
Expected: 全部 PASS

- [ ] **Step 3: Commit**

```bash
git add agenthub/backend/tests/test_memory_fallback.py
git commit -m "test: add storage backend fallback tests"
```

---

### Task 7: 端到端验证

**Files:**
- 无文件改动

- [ ] **Step 1: 启动 Redis（Docker）**

Run: `docker run -d --name redis-test -p 6379:6379 redis:7-alpine`
Expected: 容器启动成功

- [ ] **Step 2: 配置环境变量并启动后端**

在 `agenthub/backend/.env` 中设置：
```
STORAGE_BACKEND=redis
REDIS_URL=redis://localhost:6379
```

启动后端：`cd agenthub/backend && python main.py`
Expected: 日志中出现 `RedisMemoryManager initialized`

- [ ] **Step 3: 通过 API 发送消息并验证持久化**

```bash
# 发送消息
curl -X POST http://localhost:7010/api/messages \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-secret-key" \
  -d '{"content": "测试 Redis 存储", "sender": "user", "sender_name": "用户"}'

# 获取消息历史
curl http://localhost:7010/api/messages?limit=10 \
  -H "X-API-Key: dev-secret-key"
```

Expected: 返回的消息列表中包含 "测试 Redis 存储"

- [ ] **Step 4: 重启后端验证持久化**

停止后端，重新启动，再次获取消息历史。
Expected: 消息仍然存在

- [ ] **Step 5: 清理测试容器**

Run: `docker rm -f redis-test`

- [ ] **Step 6: Commit（如有修复）**

如果端到端验证中发现问题并修复，提交修复。否则跳过。

---

### Task 8: 运行全部测试确保无回归

**Files:**
- 无文件改动

- [ ] **Step 1: 运行全部后端测试**

Run: `cd agenthub/backend && python -m pytest tests/ -v`
Expected: 全部 PASS

- [ ] **Step 2: 如有失败，修复并重新运行**

定位失败原因，修复后重新运行直到全部通过。
