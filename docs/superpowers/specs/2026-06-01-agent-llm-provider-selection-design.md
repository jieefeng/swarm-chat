# Agent LLM Provider 选择功能设计

## 概述

允许用户在前端为每个 Agent 角色配置其使用的 LLM Provider（bailian 或 anthropic），配置持久化到 SQLite 数据库。

## 需求背景

当前每个 Agent 的 `llm_provider` 在 `session.py` 的 `AGENT_CONFIGS` 中硬编码，无法动态调整。用户希望根据实际需求（成本、性能、能力）为不同 Agent 选择不同的 LLM 服务。

## 设计方案

采用最小改动方案：新增 SQLite 表存储配置 + API 端点 + 前端 Agent 列表页选择器。

---

## 1. 数据库设计

### 表结构

```sql
CREATE TABLE agent_llm_config (
    agent_id TEXT PRIMARY KEY,      -- "pm", "architect", "developer" 等
    llm_provider TEXT NOT NULL,     -- "bailian" 或 "anthropic"
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 初始化逻辑

1. 应用启动时检查表是否存在，不存在则创建
2. 表为空时，从 `AGENT_CONFIGS` 读取默认值插入（保持现有行为不变）
3. 之后读取以数据库为准

---

## 2. 后端 API 设计

### 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/agents/llm-config` | GET | 获取所有 Agent 的 LLM 配置 |
| `/api/agents/{agent_id}/llm-config` | PUT | 更新指定 Agent 的 LLM 配置 |

### GET `/api/agents/llm-config`

**响应**：
```json
{
  "pm": { "llm_provider": "bailian" },
  "architect": { "llm_provider": "bailian" },
  "developer": { "llm_provider": "bailian" },
  "qa": { "llm_provider": "anthropic" },
  "orchestrator": { "llm_provider": "bailian" }
}
```

### PUT `/api/agents/{agent_id}/llm-config`

**请求**：
```json
{
  "llm_provider": "anthropic"
}
```

**响应**：`200 OK` + 更新后的配置

**错误处理**：
- `agent_id` 不存在 → 404
- `llm_provider` 不是 `bailian`/`anthropic` → 422

---

## 3. 前端 UI 设计

### 位置

Agent 列表页 (`/agents`)

### UI 元素

每个 Agent 卡片增加一个 Provider 下拉框：

```
┌─────────────────────────────────────────┐
│  🐉 苍龙 (青龙)                         │
│  产品经理（PM）                          │
│                                         │
│  LLM Provider:  [bailian ▼]             │  ← 新增下拉框
│                                         │
│  "需求不清？让我来帮你梳理"               │
└─────────────────────────────────────────┘
```

### 交互逻辑

1. 页面加载时调用 `GET /api/agents/llm-config` 获取配置
2. 下拉框选项：`bailian`（阿里云百炼）、`anthropic`（Claude）
3. 切换时立即调用 `PUT /api/agents/{agent_id}/llm-config` 保存
4. 保存成功后显示短暂 toast 提示"已切换到 anthropic"
5. 保存失败则回滚选择，显示错误提示

---

## 4. 数据流

### 配置更新流

```
用户在前端切换 Provider
    ↓
PUT /api/agents/{agent_id}/llm-config
    ↓
写入 SQLite agent_llm_config 表
    ↓
返回 200 OK
```

### 消息发送流

```
用户发消息 @agent
    ↓
POST /api/messages
    ↓
session.send_to_agent()
    ↓
llm_config_db.get_provider(agent_id)  ← 查数据库
    ↓ (回退到 AGENT_CONFIGS 默认值)
get_llm_service_for_provider(provider)
    ↓
调用对应 LLM 服务
```

---

## 5. 文件改动清单

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `backend/services/llm_config_db.py` | 新增 | 封装 SQLite 操作 |
| `backend/services/session.py` | 修改 | `send_to_agent` 从数据库读 provider |
| `backend/routers/agents.py` | 新增 | LLM 配置 API |
| `backend/main.py` | 修改 | 注册 agents 路由，启动时初始化表 |
| `frontend/app/agents/page.tsx` | 修改 | Agent 卡片增加 Provider 下拉框 |
| `frontend/lib/api.ts` | 修改 | 新增 LLM 配置相关 API 调用 |

### 不改动的文件

- `llm_router.py` — 已支持按 provider 选择，无需修改
- `AGENT_CONFIGS` — 保留作为默认值和回退

---

## 6. 约束与假设

### 约束

- 只支持 `bailian` 和 `anthropic` 两种 provider
- 配置即时生效，无需重启服务
- SQLite 单机部署，不适合多实例场景

### 假设

- Agent 列表相对固定，不需要动态增删
- 用户接受 SQLite 作为存储方案
- 切换 provider 不需要清空对话历史

---

## 7. 后续扩展

- 支持具体模型选择（如 `claude-opus-4-8` vs `claude-sonnet-4-6`）
- 支持更多 provider（如 OpenAI、本地模型）
- 配置导入/导出功能
- 对话历史与 provider 绑定（切换后可选择是否清空）
