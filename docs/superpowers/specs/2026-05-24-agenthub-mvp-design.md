# AgentHub MVP - 多Agent协作聊天平台设计

**日期：** 2026-05-24
**版本：** v1.0 (MVP)

---

## 1. 项目概述

### 1.1 背景

在大模型与 AI Agent 技术快速发展的背景下，多 Agent 协作已成为提升复杂任务执行效率的关键趋势。本项目聚焦 AI 驱动的开发与协作场景，打造一个 IM 聊天式的多 Agent 协作平台（AgentHub）。

### 1.2 核心定位

- **产品形态：** 类似飞书/微信的 IM 聊天界面
- **协作模式：** 通过 @ 指令实现群聊协作，Agent 之间可以自由讨论
- **目标场景：** 产品经理（PM）和架构师（Architect）围绕需求进行多轮讨论
- **开发方式：** AI辅助开发，前端完全由AI编写

### 1.3 MVP 范围

| 功能 | 说明 |
|------|------|
| ✅ 单聊 (1v1) | PM 和 Architect 的固定会话 |
| ✅ 群聊协作 (@) | 通过 @ 指令触发特定 Agent |
| ✅ 多会话并行 | 每个 Agent 维护独立 Claude 会话 |
| ✅ 消息汇总展示 | 所有消息汇总到同一界面 |
| ✅ 广播模式 | 无@时所有Agent都能看到 |
| ✅ Spec文档格式 | Agent输出采用标准markdown格式 |
| ✅ 人类触发终止 | 用户说"结束"等关键词触发后续 |
| ❌ 代码 Diff | 不在 MVP 范围 |
| ❌ 网页预览 | 不在 MVP 范围 |
| ❌ 一键部署 | 不在 MVP 范围 |

---

## 2. 技术架构

### 2.1 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **前端** | Next.js 14 + TypeScript | AI编程工具支持最好，生态完善 |
| **UI组件** | shadcn/ui + TailwindCSS | AI友好，快速构建美观界面 |
| **后端** | FastAPI + Python | AI集成最好，异步高性能 |
| **通信** | HTTP POST + SSE | 简单稳定，自动重连 |
| **Claude集成** | Anthropic API | Claude会话管理 |

### 2.2 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                      前端 (Next.js)                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ChatWindow│  │AgentList │  │MessageList│ │Input    │         │
│  └────┬─────┘  └──────────┘  └──────────┘  └──────────┘         │
│       │                                                       │
│       │ HTTP POST + SSE                                      │
└───────┼───────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                      后端 (FastAPI)                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    核心服务                               │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │   │
│  │  │ WSManager  │  │MessageRouter│ │SessionMgr  │        │   │
│  │  │  (SSE管理)  │  │ (@指令解析) │  │(会话管理)  │        │   │
│  │  └────────────┘  └────────────┘  └────────────┘        │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Claude Adapter Layer                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │PM Agent  │  │Architect │  │Dev Agent │              │   │
│  │  │(会话管理) │  │(会话管理) │  │(会话管理) │              │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 通信模式

```
用户输入: "需要设计一个用户认证系统"
       │
       ▼
┌─────────────────────────────┐
│      HTTP POST             │
│  /api/messages              │
└─────────────┬───────────────┘
              │
              ▼
    ┌─────────────────┐
    │  Message Router │
    │  - 无@：广播所有 │
    │  - 有@：仅目标   │
    └────────┬────────┘
              │
    ┌────────┴────────┐
    ▼                 ▼
┌──────────┐    ┌──────────┐
│PM Agent  │    │Architect │
│(Claude) │    │(Claude)  │
└────┬─────┘    └────┬─────┘
     │                │
     └────────┬───────┘
              │
              ▼
    ┌─────────────────┐
    │  SSE 推送响应   │
    │  /api/events    │
    └────────┬────────┘
              │
              ▼
         前端显示
```

---

## 3. 项目结构

### 3.1 目录结构

```
agenthub/
├── backend/
│   ├── main.py              # FastAPI入口
│   ├── requirements.txt     # Python依赖
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── messages.py      # 消息API (/api/messages)
│   │   └── events.py        # SSE端点 (/api/events)
│   └── services/
│       ├── __init__.py
│       ├── router.py         # @指令解析 + 广播
│       ├── session.py        # Agent会话管理
│       ├── memory.py         # 共享上下文
│       └── claude.py         # Claude API适配
├── frontend/
│   ├── app/
│   │   ├── layout.tsx        # 根布局
│   │   ├── page.tsx         # 主页面
│   │   └── globals.css       # 全局样式
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   └── MessageInput.tsx
│   │   └── agents/
│   │       └── AgentList.tsx
│   ├── lib/
│   │   ├── api.ts           # API调用
│   │   └── types.ts         # TypeScript类型
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.ts
└── README.md
```

---

## 4. 核心组件设计

### 4.1 Agent 定义

```yaml
Agent:
  id: string              # 唯一标识 (pm, architect, developer)
  name: string            # 显示名称
  role: string            # 角色描述
  backstory: string       # 背景故事
  system_prompt: string    # Claude系统提示词
  status: online | offline | busy
```

### 4.2 MVP Agent 角色

| Agent | Role | Backstory | System Prompt |
|-------|------|-----------|---------------|
| **PM** | 产品经理 | 资深产品经理，擅长需求挖掘和用户体验设计 | 专注于需求分析，用产品视角补充技术视角，输出Spec格式 |
| **Architect** | 系统架构师 | 精通系统设计和云原生技术 | 专注于技术方案，从技术角度评估可行性，输出Spec格式 |

### 4.3 消息结构

```typescript
interface Message {
  id: string;              // 消息唯一 ID
  sender: string;          // 发送者 agent ID
  sender_name: string;     // 发送者显示名
  content: string;         // 消息内容
  timestamp: number;       // Unix时间戳
  type: 'user' | 'agent'; // 消息类型
}
```

### 4.4 Spec 输出格式

当 Agent 输出给另一个 Agent 时，采用 Spec 文档格式：

```markdown
## Spec: [功能名称]

### 1. 需求概述
[简洁描述要解决的问题]

### 2. 功能描述
[详细的功能说明]

### 3. 技术方案
[架构设计、API设计等]

### 4. 约束条件
[性能要求、兼容性等]

### 5. 验收标准
[如何判断功能完成]
```

---

## 5. API 设计

### 5.1 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/messages` | 发送消息 |
| `GET` | `/api/messages` | 获取消息历史 |
| `GET` | `/api/agents` | 获取 Agent 列表 |
| `GET` | `/api/events` | SSE事件流（实时推送） |

### 5.2 请求/响应示例

**发送消息：**
```http
POST /api/messages
Content-Type: application/json

{
  "content": "@architect 需要一个用户认证系统",
  "sender": "user",
  "sender_name": "用户"
}
```

**响应：**
```json
{
  "success": true,
  "message_id": "msg_xxx",
  "is_broadcast": false
}
```

**SSE事件流：**
```
GET /api/events

event: message
data: {"id":"msg_xxx","sender":"architect","sender_name":"架构师","content":"## Spec:...","timestamp":1716500000,"type":"agent"}

event: message
data: {"id":"msg_yyy","sender":"pm","sender_name":"产品经理","content":"这种设计有什么优缺点？","timestamp":1716500001,"type":"agent"}
```

### 5.3 人类终止信号

当用户发送包含终止关键词的消息时，SSE推送终止事件：

```json
{
  "event": "termination",
  "data": {
    "keyword": "结束讨论",
    "message_id": "msg_zzz"
  }
}
```

---

## 6. 后端服务设计

### 6.1 MessageRouter

```python
class MessageRouter:
    def parse_at_mention(self, text: str) -> tuple[Optional[str], str]:
        """解析@mention，返回(target, content)"""

    def get_target_agents(self, text: str) -> list[str]:
        """获取消息目标，无@返回所有Agent"""

    def is_termination_signal(self, text: str) -> bool:
        """检查终止关键词"""
```

### 6.2 SessionManager

```python
class SessionManager:
    def get_or_create_session(self, agent_id: str) -> str:
        """获取或创建Agent的Claude会话"""

    def send_to_agent(self, agent_id: str, message: str) -> str:
        """发送消息给Agent并获取响应"""
```

### 6.3 SSEEventManager

```python
class SSEEventManager:
    def subscribe(self, client_id: str) -> AsyncGenerator:
        """SSE订阅，返回事件流"""

    async def push_message(self, message: dict):
        """推送消息到所有订阅者"""

    async def push_termination(self, keyword: str, message_id: str):
        """推送终止信号"""
```

---

## 7. 前端组件设计

### 7.1 页面结构

```
app/page.tsx
├── layout.tsx (根布局)
└── page.tsx (主页面)
    ├── AgentList (左侧边栏)
    └── ChatWindow (主聊天区)
        ├── MessageList (消息列表)
        └── MessageInput (输入框)
```

### 7.2 组件职责

| 组件 | 职责 |
|------|------|
| `AgentList` | 显示Agent列表和状态 |
| `ChatWindow` | 聊天窗口容器 |
| `MessageList` | 消息列表，支持Markdown渲染 |
| `MessageBubble` | 单条消息气泡 |
| `MessageInput` | 输入框，支持@自动补全 |

---

## 8. 已确认设计决策

| 问题 | 决策 |
|------|------|
| 消息发给谁？ | **广播所有Agent** — 所有Agent都能看到并参与 |
| 所有Agent能参与？ | **是** — 每个Agent都可以响应 |
| PM需要Claude会话？ | **是** — PM也是Agent，参与讨论 |
| 如何判断结束？ | **人类触发** — "结束"、"实现"等关键词 |
| 通信方式 | **HTTP POST + SSE** — 简单稳定 |
| 前端框架 | **Next.js** — AI编程工具支持最好 |
| 后端框架 | **FastAPI** — Python AI集成最好 |

---

## 9. 实现计划

详见：`docs/superpowers/plans/2026-05-24-agenthub-mvp-plan.md`

---

**Author:** Claude Code
**Last Updated:** 2026-05-24