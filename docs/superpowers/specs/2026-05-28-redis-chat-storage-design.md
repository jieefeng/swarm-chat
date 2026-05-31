# Redis 聊天记录存储设计

> 日期: 2026-05-28
> 状态: 设计完成，待审阅

## 1. 背景与目标

当前 `MemoryManager` 使用 Python 内存 list 存储消息，服务器重启后数据全部丢失。本次改造目标：

1. **持久化存储**：服务器重启后聊天记录不丢失
2. **按用户隔离**：每个用户有独立的消息流
3. **自动过期清理**：超过 TTL 的消息自动删除
4. **保持 API 不变**：REST 端点和前端代码无需改动（后端内部从同步改为 async）

## 2. 方案选型

| 方案 | 适用性 | 结论 |
|------|--------|------|
| Redis String | 最简单，但每次追加需 GET→追加→SET，非原子 | 不采用 |
| **Redis List** | **LPUSH+LRANGE+LTRIM，天然支持消息列表场景** | **采用** |
| Redis Sorted Set | 支持去重和 score 范围查询，当前不需要 | 过度设计 |
| Redis Streams | 多消费者语义，当前不需要 | 过度设计 |

## 3. 数据模型

### Redis Key 结构

```
chat:messages:{user_id}   → List（最新消息在左）
```

- `user_id` 来源于前端传递的用户标识，默认值 `"default"`
- 每条消息是 JSON 字符串，格式与现有 `add_message()` 返回的 dict 一致

### 消息格式

```json
{
  "id": "msg_a1b2c3d4",
  "role": "user",
  "content": "你好",
  "agent_id": "pm",
  "sender_name": "用户",
  "timestamp": 1716864000,
  "type": "user"
}
```

字段说明：
- `sender_name`：显示用名称（用户消息为 `"用户"`，Agent 消息为 Agent 中文名如 `"产品经理"`）
- `type`：消息类型，`"user"` 或 `"agent"`，前端用于区分消息样式

### 过期策略

- 每个 key 设置 TTL（默认 30 天，可配置）
- 每次写入时刷新 TTL（`EXPIRE`），保持活跃会话不过期
- `LTRIM` 限制最大消息数（默认 1000），防止无限增长

## 4. 接口设计

### RedisMemoryManager 类

```python
class RedisMemoryManager:
    def __init__(self, redis_url="redis://localhost:6379",
                 max_messages=1000, ttl_days=30):
        self.redis = redis.asyncio.from_url(redis_url)
        self.max_messages = max_messages
        self.ttl_seconds = ttl_days * 86400

    async def add_message(self, role, content, user_id="default",
                          agent_id=None, sender_name=None) -> dict:
        """LPUSH 新消息到用户列表，LTRIM 限制数量，EXPIRE 刷新 TTL"""

    async def get_messages(self, user_id="default", limit=50) -> list:
        """LRANGE 取最近 N 条"""

    async def get_context_for_agent(self, agent_id, user_id="default",
                                     limit=10) -> str:
        """取最近消息拼成上下文字符串"""

    async def clear(self, user_id="default"):
        """DEL 删除用户的消息 key"""
```

### 与现有接口的差异

| 现有 | 新增 |
|------|------|
| 同步方法 | 全部改为 async |
| 无 user_id 参数 | 每个方法加 `user_id` 参数，默认 `"default"` |
| 内存 list | Redis List |

## 5. 集成方案

### 改动文件清单

| 文件 | 改动内容 |
|------|---------|
| `services/memory_manager.py` | 新增 `RedisMemoryManager` 类，保留原 `MemoryManager` |
| `routers/messages.py` | `add_message`/`get_messages`/`get_context_for_agent` 改为 `await` 调用；`SendMessageRequest` 加 `user_id` 字段 |
| `requirements.txt` | 添加 `redis[hiredis]>=5.0.0` |
| `.env.example` | 添加 Redis 配置项 |

### 环境变量

```bash
# Redis 配置
REDIS_URL=redis://localhost:6379      # Redis 连接地址
STORAGE_BACKEND=redis                  # redis | memory（默认 memory）
MESSAGE_TTL_DAYS=30                   # 消息过期天数
MAX_MESSAGES=1000                     # 每用户最大消息数
```

### 存储后端切换

通过 `STORAGE_BACKEND` 环境变量切换：
- `memory`（默认）：使用原有内存 `MemoryManager`，向后兼容
- `redis`：使用 `RedisMemoryManager`

在 `messages.py` 中根据配置选择实例：

```python
if os.getenv("STORAGE_BACKEND") == "redis":
    from agenthub.backend.services.memory_manager import redis_memory_manager as memory_manager
else:
    from agenthub.backend.services.memory_manager import memory_manager
```

## 6. 错误处理

| 场景 | 处理方式 |
|------|---------|
| Redis 连接失败（启动时） | 回退到内存模式，打印警告 |
| 写入失败（运行时） | 降级到内存存储，不阻塞请求 |
| 读取失败 | 返回空列表 |
| Redis 不可用（运行时） | 自动重试 3 次，仍失败则降级 |

核心原则：**Redis 不可用时系统仍能正常工作**，只是消息不持久化。

## 7. 测试策略

- **单元测试**：用 `fakeredis` mock Redis，测试 `RedisMemoryManager` 所有方法
- **集成测试**：启动真实 Redis（Docker），验证端到端读写
- **降级测试**：模拟 Redis 不可用，验证自动降级到内存模式

## 8. 部署

### 本地开发

```bash
# Docker 启动 Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# backend/.env
REDIS_URL=redis://localhost:6379
STORAGE_BACKEND=redis
```

### 切换到云 Redis

修改 `REDIS_URL` 即可，无需改动代码：

```bash
REDIS_URL=redis://:password@your-redis-host:6379
```
