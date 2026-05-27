# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 编辑原则

写每条规则时问自己：**"如果删掉这条，不了解本项目的高级工程师（或 AI）能不能凭常识做对？"**

- 凭常识能做对的 → 删除
- 不知道就会做错/踩坑的 → 保留

## 项目概述

AgentHub 是一个多 Agent 协作聊天平台，前端 Next.js 15 + Zustand，后端 FastAPI，通过 SSE 实现实时消息推送。

## 目录结构

```
agenthub/
├── backend/
│   ├── main.py              # FastAPI 入口，uvicorn 运行
│   ├── routers/             # messages.py, events.py
│   └── services/
│       ├── session.py       # AGENT_CONFIGS (Agent 配置)
│       ├── sse_manager.py   # SSE 广播，所有订阅者收到相同事件
│       ├── llm_router.py    # LLM 路由 (Claude/阿里云百炼)
│       ├── router.py        # 消息路由，解析@指令
│       └── memory_manager.py # 消息历史存储
└── frontend/
    ├── app/page.tsx         # 主聊天页
    ├── app/agents/page.tsx  # Agent 列表页
    ├── components/chat/     # MessageBubble, MessageInput, MessageList, MentionDropdown
    └── lib/
        ├── api.ts           # fetch 封装，添加 X-API-Key
        ├── hooks/useChatStream.ts  # SSE EventSource 订阅
        └── stores/          # Zustand: agentStore, messageStore
```

## 常用命令

```bash
# 后端
cd agenthub/backend && pip install -r requirements.txt && cp .env.example .env
python main.py    # 需要先填 ANTHROPIC_API_KEY 或 DASHSCOPE_API_KEY

# 前端
cd agenthub/frontend && npm install && npm run dev

# 检查
npm run check     # Biome + TypeScript
pytest            # 后端测试
pytest tests/test_router.py -v  # 运行单个测试文件
pytest -k "test_name"           # 运行匹配的测试
```

## 代码规范

- 组件: PascalCase (如 MessageBubble.tsx)
- Hooks: use 前缀 (如 useChatStream.ts)
- 常量: UPPER_SNAKE_CASE
- 禁止 any 类型，使用 interface/type 明确类型
- CSS: Tailwind v4，类名用 kebab-case

## API 设计

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/messages` | POST | 发送消息，支持 `@agent` 提及 |
| `/api/messages?limit=N` | GET | 获取消息历史 |
| `/api/agents` | GET | 获取 Agent 列表 |
| `/api/events` | GET | SSE 事件流 |

认证: `X-API-Key` Header，验证失败返回 401（不是 403）。

SSE 事件类型: `message`、`termination`。

## Agent 系统

配置在 `session.py:AGENT_CONFIGS`，当前有 `pm`（产品经理）和 `architect`（架构师）。

消息流程: POST /api/messages → session_manager.send_to_agent() → LLM → sse_manager.broadcast() → 所有订阅者

## LLM 提供商

通过 `LLM_PROVIDER` 环境变量切换：
- `bailian`（默认）: 阿里云百炼 API，使用 OpenAI 兼容接口，模型 `qwen3.6-plus-2026-04-02`
- `anthropic`: Claude API

选择逻辑在 `llm_router.py:get_llm_service()`。

## 前端状态管理

Zustand store 更新后组件自动响应，无需手动订阅。

- `agentStore`: Agent 列表 + 选中的 Agent ID
- `messageStore`: 消息历史 + streaming 状态
- `useChatStream`: SSE 连接，监听 message/termination 事件

## 隐性知识

- `sse_manager.broadcast()` 是 async 方法，调用时必须 `await`
- 前端 dev server (7000) 与后端 (7010) 通过 `next.config.mjs` 的代理将 /api 请求转发到后端
- SSE 连接使用 `fetch` + `ReadableStream`（不是 `EventSource`），支持自定义 headers（X-API-Key）
- SSE 连接断开后会自动重连，最多 5 次，指数退避（1s → 16s）
- `session.py` 中的 `send_to_agent` 是同步方法，在 `messages.py` 中通过 `asyncio.to_thread()` 调用以避免阻塞事件循环
- `memory_manager` 是内存存储，重启后消息丢失
- `main.py` 中 `PORT` 的代码默认值是 `7000`，但 `next.config.mjs` 代理目标是 `7010`——必须在 `backend/.env` 中设置 `PORT=7010`，否则前端请求全部 502

## 环境变量

```bash
# backend/.env（从 .env.example 复制后修改）
ANTHROPIC_API_KEY=sk-...   # Claude API 密钥（LLM_PROVIDER=anthropic 时必填）
DASHSCOPE_API_KEY=sk-...   # 百炼 API 密钥（LLM_PROVIDER=bailian 时必填）
API_KEY=dev-secret-key     # API 认证密钥
PORT=7010                  # 服务端口，必须设为 7010（与前端代理一致）
LLM_PROVIDER=bailian       # LLM 提供商，可选 bailian/anthropic
```

注意：`.env.example` 只列了 `ANTHROPIC_API_KEY` 和 `API_KEY`，使用百炼时需手动添加 `DASHSCOPE_API_KEY` 和 `LLM_PROVIDER=bailian`。

## ECC Skills（推荐使用）

本项目推荐以下 ECC Skills，使用 `/skill-name` 调用：

| 场景 | Skills |
|------|--------|
| 前端开发 | `/nextjs-turbopack` `/frontend-patterns` `/frontend-design` |
| 后端开发 | `/fastapi-patterns` `/python-patterns` `/api-design` |
| 代码审查 | `/fastapi-review` `/python-review` `/security-review` |
| 测试 | `/python-testing` |
| 实时通信 | `/mcp-server-patterns` |

## 需求规划流程

新功能开发前，按以下顺序进行：

1. **头脑风暴** → `/brainstorming`
   - 探索问题边界、用户场景、技术约束
   - 输出：结构化的需求理解

2. **撰写 PRD** → `/plan-prd`
   - 将讨论结果写成产品需求文档
   - 包含：背景目标、用户故事、功能需求、验收标准、排除项

3. **技术规划** → `/plan` 或 `/blueprint`
   - PRD 确认后，规划技术实现方案
   - 输出：任务拆解、依赖分析、实现步骤

判断当前阶段：
- 需求模糊 → 从步骤 1 开始
- 需求明确 → 直接步骤 2
- PRD 已有 → 直接步骤 3

## 工作流偏好

- 提交信息: Conventional Commits
- 回复和注释: 中文
- 端口: 后端 7010，前端 7000
