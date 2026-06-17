# A2A 协作架构收尾设计

> **日期**：2026-06-17
> **状态**：设计完成，待自审
> **范围**：工程化收尾（端到端能跑 + 80% 测试覆盖 + 文档更新）
> **上游 spec**：`2026-06-10-a2a-collaboration-design.md`（已实施 90%，本 spec 收尾）

---

## 1. 背景与目标

### 1.1 问题

AgentHub 的 A2A 协作架构（参考 Cat Café）从 6/10 开始实施。截至 6/17：

**已完成（未 commit）：**
- `a2a_router.py`（Worklist 模式 + 深度限制 15 + 取消信号 + 状态管理）
- `callback_router.py`（3 个端点 + @mention 追加 worklist）
- `invocation_registry.py`（双 UUID + TTL 1h）
- `callbacks.py`（HTTP router + pydantic schema）
- `prompt_injector.py`（已适配 3-agent 团队）
- 前端 `messageStore`（a2aState + cancelA2A）
- 前端 `MessageInput`（Stop 按钮 + 深度显示）

**端到端跑不通的两个硬缺口：**
1. `messages.py` 没接入 `a2a_router`（仍用 `session_manager.send_to_agent`）
2. `a2a_router._invoke_agent` 没用 `prompt_injector`（LLM 不知道可调 callback）

**其他缺口：**
- SSE 事件名 spec 与代码不齐（`a2a_progress` vs `a2a_chunk`、`a2a_complete` vs `a2a_done`）
- 4 个核心模块无单元测试
- `CLAUDE.md` 未更新
- 上游 spec 是 5-agent 时代写的（实际已 3-agent）

### 1.2 目标

工程化收尾：
1. **端到端能跑**：`@苍龙 @developer` 消息能真正触发 A2A 链
2. **测试覆盖 ≥ 80%**：4 个单元测试 + 1 个集成测试
3. **文档同步**：CLAUDE.md + 本 spec 反映当前 3-agent 状态

### 1.3 成功标准

- [ ] `POST /api/messages` 走 `a2a_router.route_execution`
- [ ] `prompt_injector` 实际被调用，LLM 知道可调 callback
- [ ] Stop 按钮能取消正在执行的 A2A
- [ ] 4 个单元测试 + 1 个集成测试通过，覆盖率 ≥ 80%
- [ ] `CLAUDE.md` 含 A2A 隐性知识小节
- [ ] 上游 spec 标"已实施日期"避免再次 drift

### 1.4 非目标（Out of Scope）

明确不做：
- **不持久化 A2A 状态**：保持内存 Map（YAGNI）
- **不升级 @mention 解析**：保持正则（YAGNI）
- **不做 UI/UX 打磨**：Stop 按钮样式、A2A 进度面板
- **不写真实 LLM 端到端测试**：需 API key、慢、超出"收尾"范围

---

## 2. 架构改动（端到端数据流）

### 2.1 数据流

```
用户 POST /api/messages
        │
        ▼
messages.py: 解析 @agent 提及
        │
        ├─ 无 @agent → 降级路径：直接调单 agent
        │
        └─ 有 @agent → initial_agents = ["designer", "developer"]
                │
                ▼
a2a_router.route_execution(initial_agents, message, thread_id, user_id)
                │
                ├─ 创建 invocation (invocation_id, callback_token)
                │
                ▼
        for agent_id in worklist:
                │
                ├─ a2a_router._invoke_agent(agent_id, ...)
                │       │
                │       ├─ prompt_injector.inject_into_system_prompt(
                │       │     system_prompt, invocation_id, callback_token, agent_id)
                │       │
                │       └─ LLM.send_message_stream(...)
                │               │
                │               └─ LLM 调 callback (HTTP)
                │                       │
                │                       ▼
                │       POST /api/callbacks/post-message
                │       {invocation_id, callback_token, content, target_agent_id}
                │                       │
                │                       ├─ invocation_registry.verify()
                │                       ├─ memory.add_message()
                │                       ├─ sse_manager.broadcast("message", ...)
                │                       └─ a2a_router.enqueue_a2a_targets(target)
                │
                └─ yield {type: "a2a_chunk"|"a2a_done"|"a2a_complete"|...}
```

### 2.2 关键缺口修复

**缺口 1：`messages.py` 接入 `a2a_router`**

修改 `agenthub/backend/routers/messages.py` 的发送消息逻辑：

- 解析 `@agent` 提及 → `initial_agents: List[str]`
- 调 `a2a_router.route_execution(initial_agents, message, thread_id, user_id)`
- 保留无 `@agent` 时的降级路径（直接调单 agent）
- 利用 a2a_router 的回调（`on_agent_start` / `on_agent_chunk` / `on_agent_done` / `on_a2a_complete` / `on_a2a_cancelled`）发 SSE 事件

**缺口 2：`a2a_router._invoke_agent` 接入 `prompt_injector`**

修改 `agenthub/backend/services/a2a_router.py` 的 `_invoke_agent`：

- 调 LLM **前**先 `invocation_registry.create(agent_id, thread_id)` 创建凭证
- 用 `prompt_injector.inject_into_system_prompt(system_prompt, invocation_id, callback_token, agent_id)` 注入 callback 指令
- LLM 收到注入后的 system_prompt，触发 callback 调用
- 注：每个 agent 一次 invocation（不是 worklist 全局一次），确保每个 agent 都有合法凭证

---

## 3. SSE 事件对齐

### 3.1 事件清单

| 事件 | 来源 | 含义 | 前端处理 |
|------|------|------|---------|
| `a2a_start` | a2a_router | 单个 agent 开始执行 | `setA2AState({isRunning, currentAgent, depth})` |
| `a2a_chunk` | a2a_router | LLM 流式 chunk | 实时显示 |
| `a2a_done` | a2a_router | 单个 agent 完成 | 累加响应 |
| `a2a_complete` | a2a_router | 整链完成（`is_final=true`） | 解锁输入框 |
| `a2a_cancelled` | a2a_router | 用户取消 | 解锁 + 提示 |
| `a2a_error` | a2a_router | A2A 异常 | 提示 + 解锁 |
| `message` | callback_router | agent 通过 callback 发的消息 | 显示 |

### 3.2 事件名变更（spec 对齐代码）

| 上游 spec 名 | 代码实际名 | 决策 |
|--------------|-----------|------|
| `a2a_progress` | `a2a_chunk` | 采用代码名（更准确，每 chunk 触发） |
| `a2a_done`（终态）| `a2a_complete`（终态）| 拆分为两个：`a2a_done` = 单 agent 完成，`a2a_complete` = 整链 `is_final` |
| `a2a_cancelled` | `a2a_cancelled` | 一致 |
| `a2a_error` | `a2a_error` | 一致（代码已加，spec 未提） |
| `a2a_start` | `a2a_start` | 一致 |

---

## 4. 关键设计决策

### 4.1 状态存储：内存 Map（不持久化）

- `a2a_router.thread_worklists` / `thread_signals` / `thread_states` 均为内存 Dict
- 服务器重启后 in-flight A2A 链中断
- YAGNI：聊天场景下重启罕见，持久化收益不抵成本
- 不在 spec 范围，未来若需要可加 SQLite 持久化层

### 4.2 @mention 解析：正则（不升级）

- 当前实现：`r'"target_agent_id"\s*:\s*"([^"]+)"'`
- 覆盖 prompt_injector 教的标准 curl 格式（JSON 双引号）
- YAGNI：JSON 解析器或多重 fallback 收益不抵复杂度
- 测试驱动：单测断言"标准 JSON 输出能匹配"，失败时再升级

### 4.3 invocation 生命周期：每 agent 一次

- 每次 `_invoke_agent` 都 `invocation_registry.create()`
- TTL 1 小时
- 简单：每个 agent 有自己的合法凭证
- 备选：worklist 全局一次（更省凭证但需要把凭证传下去，复杂）

### 4.4 3-agent 适配

- `prompt_injector._build_workflow_triggers` 已按 designer/developer/qa 重写
- spec 5-agent 段落（PM/架构师/开发者/QA/协调器）保留为"演变记录"
- 测试显式断言 3-agent 触发点内容

---

## 5. 文件变更清单

### 5.1 修改文件

| 文件 | 改动内容 |
|------|---------|
| `agenthub/backend/routers/messages.py` | 接入 `a2a_router.route_execution`，用回调发 SSE 事件，保留无 @agent 降级路径 |
| `agenthub/backend/services/a2a_router.py` | `_invoke_agent` 加 prompt_injector + invocation_registry 调用 |
| `agenthub/CLAUDE.md` | 新增"A2A 隐性知识"小节：SSE 事件名、取消机制、prompt 注入位置、状态内存 |
| `docs/superpowers/specs/2026-06-10-a2a-collaboration-design.md` | 末尾加"已实施日期 2026-06-17"标注，避免 drift |

### 5.2 新增文件

| 文件 | 覆盖内容 |
|------|---------|
| `agenthub/backend/tests/test_a2a_router.py` | worklist/signal/state 状态机 + 取消传播 + @mention 提取 |
| `agenthub/backend/tests/test_callback_router.py` | post_message/get_thread_context/get_pending_mentions |
| `agenthub/backend/tests/test_invocation_registry.py` | create/verify/cleanup_expired/revoke |
| `agenthub/backend/tests/test_prompt_injector.py` | inject_into_system_prompt + 3-agent 触发点 + curl 格式 |
| `agenthub/backend/tests/test_callbacks_api.py` | 3 个 HTTP 端点（401/200/异常），集成测试 |
| `docs/superpowers/specs/2026-06-17-a2a-finishup-design.md` | 本 spec |

### 5.3 不动文件

- `callback_router.py`（业务逻辑已完整）
- `invocation_registry.py`（逻辑已完整）
- `callbacks.py`（HTTP 端点已完整）
- `prompt_injector.py`（3-agent 适配已完整）
- 前端 `messageStore` / `MessageInput`（a2aState + Stop 按钮已实现）

---

## 6. 测试策略

### 6.1 测试金字塔

| 层级 | 数量 | 覆盖目标 | mock 策略 |
|------|------|---------|----------|
| 单元测试 | 4 | 80%+ | mock LLM / memory / sse_manager / a2a_router.enqueue |
| 集成测试 | 1 | HTTP 端点 401/200/异常 | `fastapi.testclient` + mock 业务层 |

### 6.2 不测

- 真实 LLM 行为（mock 即可）
- 前端 UI（已有前端单测）
- 持久化（不在范围）
- @mention 解析的边缘 case（LLM 输出非 JSON 等；超出正则方案覆盖）

### 6.3 关键测试用例

**`test_a2a_router.py`：**
- 初始 worklist 顺序正确
- @mention 提取（标准 JSON）
- @mention 重复去重
- 深度限制（>15 停止）
- 取消信号触发 `a2a_cancelled`
- `_invoke_agent` 调 LLM 前调用 `prompt_injector.inject_into_system_prompt`
- `_invoke_agent` 调 LLM 前创建 invocation
- 异常 yield `a2a_error`

**`test_callback_router.py`：**
- `post_message` 凭证验证失败 → ValueError
- `post_message` 凭证成功 → 持久化 + 广播 + enqueue
- `post_message` 带 `target_agent_id` → enqueue 追加
- `get_thread_context` 返回 messages
- `get_pending_mentions` 解析 @agent_id 提及

**`test_invocation_registry.py`：**
- create 返回 (invocation_id, callback_token)
- verify 正确凭证通过
- verify 错误 token 失败
- verify 过期 invocation 失败并清理
- revoke 移除
- cleanup_expired 批量清理
- count 正确

**`test_prompt_injector.py`：**
- inject_into_system_prompt 返回原 prompt + instructions
- 3-agent 触发点（designer/developer/qa）各自包含正确 curl + workflow
- curl 包含正确的 invocation_id 和 callback_token
- API URL 来自环境变量或默认值

**`test_callbacks_api.py`：**
- `POST /api/callbacks/post-message` 凭证失败 → 401
- `POST /api/callbacks/post-message` 凭证成功 → 200 + message_id
- `GET /api/callbacks/thread-context` 凭证失败 → 401
- `GET /api/callbacks/pending-mentions` 凭证成功 → 200 + mentions 列表

---

## 7. 验收标准

### 7.1 功能验收

- [ ] `POST /api/messages` 走 `a2a_router.route_execution`
- [ ] `@苍龙 @developer` 消息触发 A2A 链（手测或 mock 端到端）
- [ ] Stop 按钮能取消正在执行的 A2A
- [ ] 输入框在 A2A 期间锁定，完成后解锁
- [ ] 无 `@agent` 时降级到单 agent 路径
- [ ] SSE 事件类型与本 spec 表格一致

### 7.2 非功能验收

- [ ] 4 个单元测试 + 1 个集成测试通过
- [ ] 覆盖率 ≥ 80%（按 CLAUDE.md 规则）
- [ ] `CLAUDE.md` 含 A2A 隐性知识小节
- [ ] 本 spec 标"已实施日期"或等价的"已 commit"标记

---

## 8. 风险与缓解

| 风险 | 缓解 |
|------|------|
| LLM 行为不可预期，真实 A2A 跑可能不稳定 | 单元测试覆盖核心逻辑，集成测试 mock LLM；真实跑在本地手测 |
| spec 与代码 drift | 本 spec 标注"上游 spec 已实施日期"，CLAUDE.md 记录 SSE 事件名 |
| 3-agent 触发点遗漏 | `test_prompt_injector.py` 显式断言 designer/developer/qa 三个 agent 的 workflow triggers |
| `messages.py` 改动可能影响单 agent 路径 | 保留无 `@agent` 时的降级路径；现有 `test_messages.py` 应继续通过 |
| A2A 状态内存 Map 重启丢失 | 文档明示，本 spec 范围内不修 |

---

## 9. 实现顺序

按 TDD：先写测试，确保对**已存在代码**的测试通过；再写改动代码，确保新测试通过。

1. 写 `test_invocation_registry.py`（纯逻辑，无依赖）— 验证已存在代码
2. 写 `test_prompt_injector.py`（纯字符串断言）— 验证已存在代码
3. 写 `test_callback_router.py`（mock memory + sse）— 验证已存在代码
4. 写 `test_callbacks_api.py`（集成，fastapi.testclient）— 验证已存在 HTTP 端点
5. 写 `test_a2a_router.py`（mock LLM + invocation_registry + prompt_injector）— 部分验证已存在代码，部分为新行为（prompt 注入 + invocation 创建）写测试
6. 改 `a2a_router._invoke_agent`（接入 prompt_injector + invocation_registry）— **新测试触发**
7. 改 `messages.py`（接入 a2a_router，保留降级路径）— **新测试触发**
8. 更新 `CLAUDE.md` + 标注上游 spec 已实施

每步独立可验，不互相阻塞。

---

## 10. 参考

- **上游 spec**：`docs/superpowers/specs/2026-06-10-a2a-collaboration-design.md`
- **Cat Café 第四课**（A2A 路由）：https://github.com/zts212653/cat-cafe-tutorials/blob/main/docs/lessons/04-a2a-routing.md
- **Cat Café 第五课**（MCP 回传）：https://github.com/zts212653/cat-cafe-tutorials/blob/main/docs/lessons/05-mcp-callback.md

---

## 11. 自我审查（Spec Self-Review）

- [x] 无 "TBD" / "TODO" / 占位段落
- [x] 内部一致：SSE 事件表、文件清单、测试清单相互一致
- [x] 范围聚焦：只做 A2A 收尾，不持久化、不升级解析、不做 UI
- [x] 无歧义：每条改动都有具体文件 + 具体内容

**文档版本**：v1.0
**最后更新**：2026-06-17
