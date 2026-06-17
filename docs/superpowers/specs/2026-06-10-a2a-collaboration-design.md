# A2A 协作架构设计文档

> **日期**：2026-06-10
> **状态**：设计完成，待用户审核
> **作者**：AI 助手 + 用户协作
> **参考**：Cat Café 项目（zts212653/clowder-ai）

---

## 1. 背景和目标

### 1.1 背景

AgentHub 是一个多 Agent 协作聊天平台，当前有 5 个 Agent（PM、架构师、开发者、QA、协调器）。但当前架构存在以下问题：

- **没有 A2A 路由**：Agent 不能互相 @mention，需要用户手动中转
- **没有 MCP 回传**：Agent 不能在执行过程中主动发消息
- **没有安全机制**：没有深度限制、取消传播等，可能无限循环

### 1.2 目标

从 Cat Café 项目中吸收以下核心能力：

1. **A2A 路由**：Agent 通过工具调用 @mention 其他 Agent，自动触发下一个 Agent
2. **MCP 回传**：Agent 在执行过程中随时主动向聊天室发消息
3. **Worklist 模式**：深度限制、共享 AbortController、isFinal 语义等安全机制

### 1.3 成功标准

1. ✅ Agent 可以通过 post_message 工具 @mention 其他 Agent
2. ✅ A2A 路由支持深度限制（默认 15 轮）
3. ✅ 用户可以随时 Stop，取消整个 A2A 链
4. ✅ 输入框在 A2A 执行中锁定，全部完成后解锁
5. ✅ 前端显示 A2A 执行进度（当前 Agent、深度）
6. ✅ 双 UUID 认证安全可靠，凭证自动过期

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户（铲屎官）                            │
│                     @苍龙 分析这个需求                           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    A2A 路由层（新增）                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Worklist 模式：while循环 + 动态数组                      │   │
│  │  • 工具调用检测（Agent 调用 post_message）                │   │
│  │  • 深度限制：MAX_A2A_DEPTH = 15                          │   │
│  │  • 共享 AbortController（用户可随时 Stop）                │   │
│  │  • isFinal 延迟发送（全部完成后才解锁输入框）              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Callback 路由层（新增）                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  HTTP 端点（供 Agent 调用）                               │   │
│  │  • POST /api/callbacks/post-message      (发消息)        │   │
│  │  • GET  /api/callbacks/thread-context    (获取上下文)     │   │
│  │  • GET  /api/callbacks/pending-mentions  (获取@提及)      │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  双 UUID 认证                                            │   │
│  │  • invocationId    → 标识"这次调用"                       │   │
│  │  • callbackToken   → 这次调用的密码（有 TTL）             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   现有 AgentHub 架构                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  5 个 Agent（PM、架构师、开发者、QA、协调器）              │   │
│  │  • session.py: AGENT_CONFIGS                             │   │
│  │  • llm_router.py: LLM 路由                               │   │
│  │  • sse_manager.py: SSE 广播                              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**核心变化**：
1. **新增 A2A 路由层**：Worklist 模式，深度限制、取消传播、isFinal 语义
2. **新增 Callback 路由层**：HTTP 端点 + 双 UUID 认证
3. **保留现有架构**：Agent 配置、LLM 路由、SSE 广播不变

---

## 3. A2A 路由引擎

### 3.1 核心组件

**文件**：`agenthub/backend/services/a2a_router.py`

```python
class A2ARouter:
    """A2A 路由引擎 - Worklist 模式"""
    
    def __init__(self):
        self.max_depth = int(os.getenv("MAX_A2A_DEPTH", "15"))
        self.thread_worklists: Dict[str, List[str]] = {}
    
    async def route_execution(
        self,
        initial_agents: List[str],
        message: str,
        thread_id: str,
        user_id: str,
        signal: Optional[asyncio.Event] = None,
    ) -> AsyncIterator[dict]:
        """执行 A2A 路由，流式返回消息"""
        
        worklist = list(initial_agents)
        a2a_count = 0
        
        # 注册 worklist（供 callback 追加）
        self.thread_worklists[thread_id] = worklist
        
        try:
            i = 0
            while i < len(worklist) and a2a_count < self.max_depth:
                # 检查取消信号
                if signal and signal.is_set():
                    yield {"type": "cancelled", "reason": "用户取消"}
                    break
                
                agent_id = worklist[i]
                
                # 执行 Agent，流式返回
                full_response = ""
                async for chunk in self._invoke_agent(agent_id, message, thread_id, user_id):
                    if isinstance(chunk, str):
                        full_response += chunk
                        yield {"type": "chunk", "agent_id": agent_id, "content": chunk}
                    elif isinstance(chunk, dict):
                        # 工具调用结果
                        yield chunk
                
                # 检查是否有 @mention（通过工具调用）
                mentions = self._extract_mentions_from_tools(full_response)
                if mentions and a2a_count < self.max_depth:
                    for mention in mentions:
                        if mention not in worklist:  # 去重
                            worklist.append(mention)
                            a2a_count += 1
                
                i += 1
            
            # 全部完成
            yield {"type": "done", "is_final": True}
            
        finally:
            # 清理 worklist
            self.thread_worklists.pop(thread_id, None)
    
    def _extract_mentions_from_tools(self, response: str) -> List[str]:
        """从 Agent 的工具调用中提取 @mention"""
        # 解析 Agent 调用 post_message 工具的参数
        # 提取 target_agent_id
        mentions = []
        # ... 解析逻辑 ...
        return mentions
    
    def enqueue_a2a_targets(self, thread_id: str, targets: List[str]):
        """供 callback 追加 Agent 到 worklist"""
        worklist = self.thread_worklists.get(thread_id)
        if worklist:
            for target in targets:
                if target not in worklist:  # 去重
                    worklist.append(target)
```

### 3.2 关键设计

1. **Worklist 模式**：`while` 循环 + 动态数组，支持运行中追加 Agent
2. **深度限制**：`a2a_count < self.max_depth`，防止无限循环
3. **共享 AbortController**：`signal.is_set()` 检查取消信号
4. **isFinal 语义**：只有 worklist 全部执行完才发 `is_final: True`
5. **去重**：`if target not in worklist`，防止重复执行

---

## 4. Callback 路由层

### 4.1 核心组件

**文件**：`agenthub/backend/services/callback_router.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import uuid
import time

router = APIRouter(prefix="/api/callbacks", tags=["callbacks"])

# 双 UUID 认证存储
class InvocationRegistry:
    """管理 invocationId + callbackToken 对"""
    
    def __init__(self):
        self._invocations: Dict[str, dict] = {}
    
    def create(self, agent_id: str, thread_id: str) -> tuple[str, str]:
        """创建新的 invocation，返回 (invocationId, callbackToken)"""
        invocation_id = str(uuid.uuid4())
        callback_token = str(uuid.uuid4())
        
        self._invocations[invocation_id] = {
            "agent_id": agent_id,
            "thread_id": thread_id,
            "callback_token": callback_token,
            "created_at": time.time(),
            "ttl": 3600,  # 1 小时过期
        }
        
        return invocation_id, callback_token
    
    def verify(self, invocation_id: str, callback_token: str) -> Optional[dict]:
        """验证凭证，返回 invocation 信息"""
        invocation = self._invocations.get(invocation_id)
        if not invocation:
            return None
        
        # 检查 token
        if invocation["callback_token"] != callback_token:
            return None
        
        # 检查过期
        if time.time() - invocation["created_at"] > invocation["ttl"]:
            self._invocations.pop(invocation_id, None)
            return None
        
        return invocation

invocation_registry = InvocationRegistry()


class PostMessageRequest(BaseModel):
    invocation_id: str
    callback_token: str
    content: str
    target_agent_id: Optional[str] = None  # @mention 目标


@router.post("/post-message")
async def post_message(req: PostMessageRequest):
    """Agent 发送消息（通过工具调用）"""
    
    # 验证凭证
    invocation = invocation_registry.verify(req.invocation_id, req.callback_token)
    if not invocation:
        raise HTTPException(status_code=401, detail="Invalid or expired credentials")
    
    # 保存消息
    msg = await _persist_message(
        role=invocation["agent_id"],
        content=req.content,
        agent_id=invocation["agent_id"],
        sender_name=AGENT_CONFIGS[invocation["agent_id"]]["name"],
        user_id="default",
        thread_id=invocation["thread_id"],
    )
    
    # 广播消息
    await sse_manager.broadcast("message", msg)
    
    # 如果有 @mention，追加到 worklist
    if req.target_agent_id:
        a2a_router.enqueue_a2a_targets(invocation["thread_id"], [req.target_agent_id])
    
    return {"status": "ok", "message_id": msg.get("id", "")}


@router.get("/thread-context")
async def get_thread_context(invocation_id: str, callback_token: str):
    """获取对话上下文"""
    
    invocation = invocation_registry.verify(invocation_id, callback_token)
    if not invocation:
        raise HTTPException(status_code=401, detail="Invalid or expired credentials")
    
    messages = await memory.get_messages(thread_id=invocation["thread_id"])
    return {"messages": messages}


@router.get("/pending-mentions")
async def get_pending_mentions(invocation_id: str, callback_token: str):
    """获取待处理的 @提及"""
    
    invocation = invocation_registry.verify(invocation_id, callback_token)
    if not invocation:
        raise HTTPException(status_code=401, detail="Invalid or expired credentials")
    
    # 获取当前线程的 pending mentions
    mentions = a2a_router.get_pending_mentions(invocation["thread_id"])
    return {"mentions": mentions}
```

### 4.2 关键设计

1. **双 UUID 认证**：`invocationId` + `callbackToken`，有 TTL（1 小时）
2. **Callback 路由**：3 个端点（post-message、thread-context、pending-mentions）
3. **A2A 触发**：`post_message` 时如果有 `target_agent_id`，追加到 worklist
4. **安全验证**：每次请求都验证凭证，过期自动清理

---

## 5. Prompt 注入机制

### 5.1 核心组件

**文件**：`agenthub/backend/services/prompt_injector.py`

```python
class PromptInjector:
    """在系统提示词里注入 HTTP callback 指令"""
    
    def __init__(self, api_url: str):
        self.api_url = api_url
    
    def build_callback_instructions(
        self,
        invocation_id: str,
        callback_token: str,
    ) -> str:
        """构建 callback 指令"""
        
        return f"""
## 团队协作工具

你可以通过 HTTP 请求与团队其他成员协作。

### 发送消息给团队

```bash
curl -X POST {self.api_url}/api/callbacks/post-message \\
  -H "Content-Type: application/json" \\
  -d '{{
    "invocation_id": "{invocation_id}",
    "callback_token": "{callback_token}",
    "content": "你的消息",
    "target_agent_id": "目标Agent ID（可选，用于@mention）"
  }}'
```

### 获取对话上下文

```bash
curl -X GET "{self.api_url}/api/callbacks/thread-context?invocation_id={invocation_id}&callback_token={callback_token}"
```

### 获取待处理的 @提及

```bash
curl -X GET "{self.api_url}/api/callbacks/pending-mentions?invocation_id={invocation_id}&callback_token={callback_token}"
```

### 使用规则

1. **主动发消息**：当你完成任务或有重要发现时，主动调用 post_message 告知团队
2. **@mention 其他 Agent**：当你需要其他 Agent 协助时，设置 target_agent_id
3. **获取上下文**：当你需要了解对话历史时，调用 thread-context
4. **检查 @提及**：当你被 @mention 时，调用 pending-mentions 获取详情

### 工作流触发点

- 完成需求分析 → @architect（架构师）
- 完成架构设计 → @developer（开发者）
- 完成代码实现 → @qa（测试）
- 发现问题需要澄清 → @pm（产品经理）
- 需要任务拆解 → @orchestrator（协调器）
"""
    
    def inject_into_system_prompt(
        self,
        system_prompt: str,
        invocation_id: str,
        callback_token: str,
    ) -> str:
        """将 callback 指令注入到系统提示词"""
        
        instructions = self.build_callback_instructions(invocation_id, callback_token)
        
        return f"{system_prompt}\n\n{instructions}"


# 全局实例
prompt_injector = PromptInjector(api_url=os.getenv("API_URL", "http://localhost:7010"))
```

### 5.2 关键设计

1. **HTTP 指令**：教 Agent 写 curl 命令调用 callback 端点
2. **工作流触发点**：明确的场景 → Agent 映射
3. **凭证传递**：`invocation_id` 和 `callback_token` 写在指令里
4. **渐进式**：先用 Prompt 注入，后续支持原生 MCP

---

## 6. 前端集成

### 6.1 状态管理

**文件**：`agenthub/frontend/lib/stores/messageStore.ts`

```typescript
interface A2AState {
  isRunning: boolean;        // A2A 链是否在执行
  currentAgent: string;      // 当前执行的 Agent
  depth: number;             // 当前深度
  maxDepth: number;          // 最大深度
  canCancel: boolean;        // 是否可以取消
}

interface MessageStore {
  // ... 现有状态 ...
  a2aState: A2AState;
  setA2AState: (state: Partial<A2AState>) => void;
  cancelA2A: () => void;  // 取消 A2A 链
}
```

### 6.2 SSE 事件扩展

```typescript
type SSEEvent = 
  | { type: "message"; data: Message }
  | { type: "stream_chunk"; data: { message_id: string; content: string; seq: number } }
  | { type: "termination"; data: { keyword: string } }
  | { type: "a2a_start"; data: { agent_id: string; depth: number } }      // 新增
  | { type: "a2a_progress"; data: { agent_id: string; depth: number } }   // 新增
  | { type: "a2a_done"; data: { is_final: boolean } }                     // 新增
  | { type: "a2a_cancelled"; data: { reason: string } };                  // 新增
```

### 6.3 Stop 按钮

**文件**：`agenthub/frontend/components/chat/MessageInput.tsx`

```tsx
export function MessageInput() {
  const { a2aState, cancelA2A } = useMessageStore();
  
  return (
    <div className="message-input">
      <textarea disabled={a2aState.isRunning} />
      
      {a2aState.isRunning && (
        <button onClick={cancelA2A} className="stop-button">
          ⏹ 停止（{a2aState.currentAgent} 执行中，深度 {a2aState.depth}/{a2aState.maxDepth}）
        </button>
      )}
    </div>
  );
}
```

### 6.4 isFinal 语义

```typescript
const handleSSEEvent = (event: SSEEvent) => {
  switch (event.type) {
    case "a2a_start":
      setA2AState({ isRunning: true, currentAgent: event.data.agent_id, depth: event.data.depth });
      break;
    
    case "a2a_progress":
      setA2AState({ currentAgent: event.data.agent_id, depth: event.data.depth });
      break;
    
    case "a2a_done":
      if (event.data.is_final) {
        // 全部完成，解锁输入框
        setA2AState({ isRunning: false, currentAgent: "", depth: 0 });
      }
      break;
    
    case "a2a_cancelled":
      setA2AState({ isRunning: false, currentAgent: "", depth: 0 });
      break;
  }
};
```

---

## 7. 文件变更清单

### 7.1 新增文件

```
agenthub/backend/
├── services/
│   ├── a2a_router.py          # A2A 路由引擎
│   ├── callback_router.py     # Callback 路由
│   ├── invocation_registry.py # 双 UUID 认证
│   └── prompt_injector.py     # Prompt 注入
├── routers/
│   └── callbacks.py           # Callback API 端点
└── ...
```

### 7.2 修改文件

```
agenthub/backend/
├── services/
│   ├── session.py             # 注入 callback 指令
│   └── sse_manager.py         # 新增 A2A 事件类型
├── routers/
│   └── messages.py            # 集成 A2A 路由
└── ...

agenthub/frontend/
├── lib/
│   └── stores/
│       └── messageStore.ts    # 扩展 A2A 状态
├── components/
│   └── chat/
│       └── MessageInput.tsx   # Stop 按钮
└── ...
```

---

## 8. 实现计划

| 阶段 | 任务 | 文件 | 预计时间 |
|------|------|------|----------|
| **Phase 1** | A2A 路由引擎 | `a2a_router.py` | 3-4 天 |
| **Phase 2** | Callback 路由 | `callback_router.py`, `invocation_registry.py`, `callbacks.py` | 3-4 天 |
| **Phase 3** | Prompt 注入 | `prompt_injector.py`, `session.py` | 2-3 天 |
| **Phase 4** | 前端集成 | `messageStore.ts`, `MessageInput.tsx`, `sse_manager.py` | 3-4 天 |
| **Phase 5** | 测试和调试 | 全部文件 | 2-3 天 |

**总预计时间**：2-3 周

---

## 9. 验收标准

1. ✅ Agent 可以通过 post_message 工具 @mention 其他 Agent
2. ✅ A2A 路由支持深度限制（默认 15 轮）
3. ✅ 用户可以随时 Stop，取消整个 A2A 链
4. ✅ 输入框在 A2A 执行中锁定，全部完成后解锁
5. ✅ 前端显示 A2A 执行进度（当前 Agent、深度）
6. ✅ 双 UUID 认证安全可靠，凭证自动过期

---

## 10. 风险和缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Agent 不会写 curl 命令 | A2A 协作失败 | 在 prompt 里提供详细的 curl 示例和工作流触发点 |
| 凭证过期导致 401 错误 | Agent 调用失败 | 凭证 TTL 设置为 1 小时，足够完成大多数任务 |
| A2A 链无限循环 | 系统失控 | 深度限制（默认 15 轮）+ 用户可随时 Stop |
| 前端输入框卡住 | 用户体验差 | isFinal 语义确保只有全部完成后才解锁 |

---

## 11. 后续优化

1. **原生 MCP 支持**：后续实现 MCP Server，让 Agent 通过原生工具调用
2. **四层协作保障**：出口检查、工作流触发点、Skill 链式导航
3. **持久化存储**：将 A2A 状态持久化到数据库，支持重启恢复
4. **监控和日志**：添加 A2A 执行的监控和日志，便于排查问题

---

## 12. 参考资料

1. **Cat Café 项目**：https://github.com/zts212653/clowder-ai
2. **Cat Café 教程**：https://github.com/zts212653/cat-cafe-tutorials
3. **第四课：多猫路由**：https://github.com/zts212653/cat-cafe-tutorials/blob/main/docs/lessons/04-a2a-routing.md
4. **第五课：MCP 回传**：https://github.com/zts212653/cat-cafe-tutorials/blob/main/docs/lessons/05-mcp-callback.md

---

**文档版本**：v1.0
**最后更新**：2026-06-10

---

## 实施记录

- **2026-06-17**：工程化收尾完成（参见 `2026-06-17-a2a-finishup-design.md` + `2026-06-17-a2a-finishup.md`）
  - 修复两个端到端跑不通的硬缺口（messages.py 接入 a2a_router；a2a_router._invoke_agent 接入 prompt_injector + invocation_registry）
  - 新增 5 个测试文件：test_invocation_registry.py / test_prompt_injector.py / test_callback_router.py / test_callbacks_api.py / test_a2a_router.py
  - 新增 `POST /api/a2a/cancel` 端点供前端 Stop 按钮
  - 事件名变更：`a2a_progress` → `a2a_chunk`；拆 `a2a_done`（单 agent）vs `a2a_complete`（整链 is_final）
  - 状态存储：保持内存 Map（YAGNI）
