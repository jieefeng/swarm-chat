# Swarm-Chat — Multi-Agent Collaboration Platform

> Orchestrator-driven AI multi-agent platform with LLM-powered task decomposition and parallel execution

[English](#english-version) | [中文](#项目简介)

---

## 项目简介

Swarm-Chat 是一个 IM 聊天式的多 Agent 协作平台，用户通过自然语言描述需求，Orchestrator 协调器自动拆解任务并分配给 5 个专业 Agent 并行执行。系统提供类似飞书/微信的交互体验，支持单聊、群聊协作、实时流式输出、HITL 人工澄清、代码 Diff 查看等功能。

## 核心特性

- **Orchestrator 协调器** — LLM 驱动的任务自动拆解，支持 Self-Correction 自修正机制
- **5 个专业 Agent** — PM（产品经理）、Architect（架构师）、Developer（开发者）、QA（测试）、Orchestrator（协调器）
- **DAG 任务调度** — 基于 Kahn 算法的拓扑排序，支持任务依赖与并行执行
- **任务状态机** — Pending → Running → Reviewing → Done/Failed/Escalate 完整生命周期
- **HITL 人工澄清** — Orchestrator 不确定时向用户提问，前端渲染选项卡片
- **流式文本渲染** — 基于 SSE 的 stream_chunk 事件，实时展示 Agent 输出
- **代码 Diff 查看** — 集成 react-diff-viewer，支持代码变更高亮对比
- **任务进度面板** — 实时展示任务状态、依赖关系和执行进度

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端框架 | Next.js 15 (App Router) | React 服务端组件 |
| 状态管理 | Zustand | 轻量级响应式状态 |
| 样式 | Tailwind CSS v4 | 原子化 CSS |
| 实时通信 | SSE (Server-Sent Events) | 自定义 fetch + ReadableStream |
| 后端框架 | FastAPI | 异步 Python Web 框架 |
| LLM 接口 | OpenAI 兼容 | 阿里云百炼 / Claude |
| Diff 查看 | react-diff-viewer-continued | 代码变更高亮 |

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+

### 后端

```bash
cd agenthub/backend
pip install -r requirements.txt
cp .env.example .env   # 编辑填入 API Key
python main.py
```

环境变量 (.env):

```
LLM_PROVIDER=bailian         # 或 anthropic
DASHSCOPE_API_KEY=sk-...     # 百炼 API
ANTHROPIC_API_KEY=sk-...     # Claude API
API_KEY=dev-secret-key       # API 认证密钥
PORT=7010                    # 必须 7010（与前端代理一致）
```

### 前端

```bash
cd agenthub/frontend
npm install
npm run dev
```

访问 http://localhost:7000，在聊天框使用 @orchestrator 触发任务拆解。

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| /api/messages | POST | 发送消息，支持 @agent 提及 |
| /api/messages?limit=N | GET | 获取消息历史 |
| /api/agents | GET | 获取 Agent 列表 |
| /api/tasks | GET | 获取任务列表 |
| /api/tasks/{id} | GET | 任务详情 |
| /api/tasks/{id}/cancel | POST | 取消任务 |
| /api/events | GET | SSE 事件流 |

### SSE 事件类型

stream_chunk | message_complete | task_created | task_update | clarification_request | artifact_diff | heartbeat

## 项目结构

```
swarm-chat/
├── agenthub/
│   ├── backend/
│   │   ├── main.py                # FastAPI 入口
│   │   ├── models/task.py         # Task / OrchestratorOutput 模型
│   │   ├── routers/               # messages, tasks, events
│   │   └── services/              # orchestrator, task_manager, agent_adapter, shared_context, session, sse_manager, llm_router, router, memory_manager
│   └── frontend/
│       ├── app/page.tsx           # 主聊天页
│       ├── app/agents/page.tsx    # Agent 列表页
│       ├── components/chat/       # MessageBubble, TaskPanel, ClarificationCard, DiffViewer, MessageInput
│       └── lib/                   # stores, hooks, sse.ts, types.ts
└── docs/superpowers/              # specs + plans
```

---

# English Version

## Overview

Swarm-Chat is an IM-style multi-agent collaboration platform powered by an Orchestrator coordinator. Users describe requirements in natural language, and the Orchestrator automatically decomposes tasks and assigns them to 5 specialized agents for parallel execution.

## Key Features

- **Orchestrator Agent** — LLM-driven task decomposition with self-correction
- **5 Agent Roles** — PM, Architect, Developer, QA, Orchestrator
- **DAG Task Scheduling** — Kahn's algorithm for topological sort with dependency resolution
- **Task State Machine** — Pending → Running → Reviewing → Done/Failed/Escalate
- **Human-in-the-Loop** — Clarification cards when Orchestrator is uncertain
- **Streaming Output** — Real-time stream_chunk events via SSE
- **Code Diff Viewer** — Highlighted comparison with react-diff-viewer
- **Task Progress Panel** — Live task status and execution progress

## Tech Stack

| Layer | Technology | Description |
|-------|-----------|-------------|
| Frontend | Next.js 15 (App Router) | React Server Components |
| State | Zustand | Lightweight reactive state |
| Styling | Tailwind CSS v4 | Utility-first CSS |
| Realtime | SSE | Custom fetch + ReadableStream |
| Backend | FastAPI | Async Python web framework |
| LLM | OpenAI-compatible | Alibaba Bailian / Claude |

## Quick Start

```bash
# Backend
cd agenthub/backend
pip install -r requirements.txt
cp .env.example .env
python main.py

# Frontend
cd agenthub/frontend
npm install
npm run dev
```

Visit http://localhost:7000 and use @orchestrator to trigger task decomposition.

## License

MIT

---

**Author:** jieefeng
**Repository:** [github.com/jieefeng/swarm-chat](https://github.com/jieefeng/swarm-chat)
