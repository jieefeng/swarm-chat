# 聊天记录持久化与历史会话列表设计

**日期：** 2026-06-03
**状态：** 已批准
**作者：** Claude Code

## 背景目标

当前 AgentHub 的消息存储存在以下问题：
- 内存模式：重启后消息丢失
- Redis 模式：需要额外部署 Redis 服务
- 无会话管理：无法查看/切换历史会话

本设计实现：
1. **持久化保存** — 聊天记录保存到 SQLite，重启后不丢失
2. **历史会话列表** — 类似 ChatGPT 左侧面板，可切换多个会话

## 技术方案

### 方案选择：SQLite 持久化

**选择理由：**
- 项目已有 `agenthub.db` 文件，零额外依赖
- 单文件，易于备份/迁移
- 无需部署额外服务
- 可复用现有 `thread_id` 概念

**权衡：**
- 需添加 `aiosqlite` 依赖支持异步操作
- 高并发场景性能一般（当前规模足够）

## 数据模型

### 数据库 Schema

```sql
-- 会话表
CREATE TABLE threads (
    id TEXT PRIMARY KEY,              -- thread_{uuid}
    title TEXT NOT NULL,              -- 会话标题（首条消息摘要）
    user_id TEXT NOT NULL DEFAULT 'default',
    created_at INTEGER NOT NULL,      -- Unix timestamp
    updated_at INTEGER NOT NULL,      -- 最后活跃时间
    is_pinned INTEGER DEFAULT 0,      -- 是否置顶
    is_archived INTEGER DEFAULT 0     -- 是否归档
);

-- 消息表
CREATE TABLE messages (
    id TEXT PRIMARY KEY,              -- msg_{uuid}
    thread_id TEXT NOT NULL,
    role TEXT NOT NULL,               -- user/agent
    content TEXT NOT NULL,
    agent_id TEXT,                    -- Agent ID（agent 消息时有值）
    sender_name TEXT,
    type TEXT NOT NULL DEFAULT 'user',-- user/agent
    created_at INTEGER NOT NULL,      -- Unix timestamp
    FOREIGN KEY (thread_id) REFERENCES threads(id)
);

-- 索引
CREATE INDEX idx_messages_thread_id ON messages(thread_id);
CREATE INDEX idx_threads_user_id ON threads(user_id);
CREATE INDEX idx_threads_updated_at ON threads(updated_at DESC);
```

### 关系说明

```
threads (1) ──── (N) messages
   │                   │
   │ thread_id         │ thread_id
   └───────────────────┘
```

- **threads 表**：存储会话元数据（标题、创建时间、置顶状态）
- **messages 表**：存储会话内的具体消息
- **级联删除**：删除会话时自动删除相关消息

## API 设计

### 新增端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/threads` | GET | 获取会话列表 |
| `/api/threads` | POST | 创建新会话 |
| `/api/threads/{id}` | PATCH | 更新会话（标题、置顶） |
| `/api/threads/{id}` | DELETE | 删除会话（级联删除消息） |
| `/api/threads/{id}/messages` | GET | 获取会话内的消息 |

### 请求/响应格式

```typescript
// GET /api/threads
{
  "threads": [
    {
      "id": "thread_abc123",
      "title": "帮我写一个 React 组件",
      "created_at": 1717344000,
      "updated_at": 1717344060,
      "is_pinned": false,
      "message_count": 5
    }
  ]
}

// POST /api/threads
// Request: { "title?: string" }
// Response: { "id": "thread_new123", "title": "新会话", ... }

// PATCH /api/threads/{id}
// Request: { "title": "新标题", "is_pinned": true }

// GET /api/threads/{id}/messages?limit=50
// 与现有 GET /api/messages 相同格式，但按 thread_id 筛选
```

## 前端设计

### 新增组件

```
frontend/components/threads/
├── ThreadList.tsx        # 会话列表（侧边栏）
├── ThreadItem.tsx        # 单个会话项
└── NewThreadButton.tsx   # 新建会话按钮
```

### 修改组件

| 组件 | 修改内容 |
|------|----------|
| `page.tsx` | 添加 `ThreadList` 侧边栏，管理当前会话 ID |
| `api.ts` | 添加会话相关 API 调用 |
| `messageStore.ts` | 添加 `threadId` 状态，切换会话时清空消息 |

### UI 布局

```
┌─────────────────────────────────────────────┐
│ Header: AgentHub · 五行神兽                   │
├──────────┬──────────────────────────────────┤
│ 会话列表  │         聊天区域                  │
│          │                                  │
│ [新建会话] │    MessageList                   │
│          │                                  │
│ 会话 1    │                                  │
│ 会话 2    │                                  │
│ 会话 3    │                                  │
│          │    ┌────────────────────────┐    │
│          │    │ MessageInput           │    │
│          │    └────────────────────────┘    │
└──────────┴──────────────────────────────────┘
```

## 数据流

### 会话切换流程

```
用户点击会话 2
    ↓
前端: setCurrentThreadId("thread_2")
    ↓
前端: 调用 GET /api/threads/thread_2/messages
    ↓
前端: 清空 messageStore，加载新消息
    ↓
完成切换
```

### 新建会话流程

```
用户点击"新建会话"
    ↓
前端: 调用 POST /api/threads
    ↓
后端: 创建 thread 记录，返回 thread_id
    ↓
前端: 添加到会话列表，设置为当前会话
    ↓
前端: 清空消息列表
    ↓
用户发送第一条消息
    ↓
后端: 存储消息时使用新 thread_id
    ↓
后端: 自动更新 thread 的 title（首条消息摘要）
```

### 发送消息流程（修改现有）

```
用户发送消息
    ↓
前端: sendMessage(content, thread_id)
    ↓
后端: 存储消息到 messages 表（带 thread_id）
    ↓
后端: 更新 threads 表的 updated_at
    ↓
后端: 广播 SSE 事件（带 thread_id）
    ↓
前端: 更新 messageStore（仅当前会话）
```

## 错误处理

| 场景 | 处理方式 |
|------|----------|
| 会话不存在 | 返回 404，前端提示并切换到默认会话 |
| 消息存储失败 | 回滚，不更新 thread 的 updated_at |
| SQLite 连接失败 | 降级到内存模式，日志警告 |
| 并发创建会话 | 使用 UUID 避免 ID 冲突 |

## 测试策略

| 类型 | 测试内容 |
|------|----------|
| **单元测试** | 会话 CRUD、消息查询、级联删除 |
| **集成测试** | API 端点、SSE 广播带 thread_id |
| **E2E 测试** | 会话切换、新建会话、删除会话 |

## 实现计划

### 第一阶段：后端存储层
1. 添加 `aiosqlite` 依赖
2. 实现 `SQLiteMemoryManager` 类
3. 创建数据库迁移脚本

### 第二阶段：会话 API
1. 实现 `/api/threads` 端点
2. 修改现有 `/api/messages` 支持 thread_id
3. 更新 SSE 广播带 thread_id

### 第三阶段：前端 UI
1. 创建 `ThreadList` 组件
2. 修改 `page.tsx` 添加侧边栏
3. 实现会话切换逻辑

### 第四阶段：集成测试
1. 后端 API 测试
2. 前端组件测试
3. E2E 流程测试

## 依赖变更

### 新增依赖

```txt
aiosqlite>=0.19.0
```

### 环境变量

```bash
STORAGE_BACKEND=sqlite  # 可选：memory/redis/sqlite（默认 sqlite）
SQLITE_DB_PATH=agenthub.db  # SQLite 数据库路径
```

## 向后兼容

- 保持现有 `memory_manager` 和 `RedisMemoryManager` 不变
- 通过 `STORAGE_BACKEND` 环境变量切换存储后端
- 默认使用 SQLite，无需额外配置
