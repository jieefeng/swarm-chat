# AgentHub Orchestrator 协调器设计规范

**日期：** 2026-05-27
**版本：** v1.0
**状态：** 设计定稿

---

## 1. 背景与目标

### 1.1 设计背景

AgentHub 当前已实现基础 IM 聊天功能（2 个 Agent、@mention 路由、SSE 实时推送），但缺乏比赛核心要求的 Orchestrator 协调器、代码 Diff、网页预览、一键部署等功能。

### 1.2 设计目标

- 新增 Orchestrator 协调器，实现 LLM 驱动的任务自动拆解
- 扩展 Agent 角色至 5 个（PM、架构师、开发者、QA、Orchestrator）
- 实现代码 Diff 组件、网页预览、一键部署（轻量实现）
- 提升 IM 交互体验（流式文本、任务进度展示、HITL 澄清）

### 1.3 约束条件

- 基于现有 FastAPI + Next.js 架构扩展
- LLM 调用使用百炼 API（OpenAI 兼容接口）
- 优先保证核心功能稳定，非核心功能可简化实现

---

## 2. 整体架构

### 2.1 架构概览

用户描述需求 -> Orchestrator Agent（LLM 拆解任务）-> 输出 JSON 任务列表 -> 后端解析 -> TaskManager 管理任务生命周期 -> PM / 架构师 / 开发者 / QA 并行执行 -> QA Agent 验证 -> 结果通过 SSE 推送给前端 -> 前端展示任务进度 + 各 Agent 回复 + Diff + 预览

### 2.2 核心组件

| 组件 | 职责 | 文件路径 |
|------|------|----------|
| OrchestratorAgent | LLM 驱动任务拆解 | backend/services/orchestrator.py |
| TaskManager | 任务状态机 + DAG 调度 | backend/services/task_manager.py |
| AgentAdapter | 统一 LLM 调用适配 | backend/services/agent_adapter.py |
| SharedContext | Agent 间共享状态 | backend/services/shared_context.py |
| TaskPanel | 前端任务进度组件 | frontend/components/chat/TaskPanel.tsx |
| DiffViewer | 代码 Diff 组件 | frontend/components/chat/DiffViewer.tsx |
| PreviewCard | 网页预览卡片 | frontend/components/chat/PreviewCard.tsx |
| DeployCard | 部署卡片 | frontend/components/chat/DeployCard.tsx |
| ClarificationCard | HITL 澄清卡片 | frontend/components/chat/ClarificationCard.tsx |
| taskStore | 任务状态 Store | frontend/lib/stores/taskStore.ts |

---

## 3. Orchestrator 核心设计

### 3.1 输出格式（JSON Schema）

```json
{
  "analysis": "string - 对用户需求的理解和分析",
  "tasks": [
    {
      "title": "string - 任务标题",
      "description": "string - 任务详细描述",
      "assigned_to": "string - Agent ID (pm/architect/developer/qa)",
      "depends_on": ["string - 依赖的任务标题"],
      "priority": "string - high/medium/low"
    }
  ],
  "requires_clarification": "boolean - 是否需要用户澄清",
  "clarification_question": "string|null - 澄清问题",
  "uncertain_points": [
    {
      "question": "string - 不确定点描述",
      "options": ["string - 选项列表"]
    }
  ]
}
```

**关键规则：**
- 任务标题必须唯一，作为任务标识
- depends_on 引用其他任务的标题
- assigned_to 必须是已注册的 Agent ID
- requires_clarification 为 true 时，clarification_question 和 uncritical_points 必须非空

### 3.2 Self-Correction 机制

LLM 输出 JSON 可能有格式错误，必须内置重试机制：
1. 后端使用 Pydantic 校验 LLM 输出
2. 校验失败时，将错误信息回传给 LLM
3. LLM 根据错误信息修正输出
4. 最多重试 2 次，仍失败则降级为广播模式

### 3.3 Human-in-the-Loop (HITL)

当 Orchestrator 不确定时，通过 requires_clarification: true 向用户提问。前端渲染 ClarificationCard，用户点击选项后以消息形式回传答案。

### 3.4 反思与验证闭环

Dev Agent 产出代码 -> QA Agent 验证 -> 通过则完成，失败则重试（最多 3 次）-> 仍失败则 Orchestrator 重新拆解 -> 仍失败则请求用户介入。

---

## 4. TaskManager 状态机

### 4.1 状态定义

- Pending: 等待前置任务完成
- Running: Agent 正在执行
- Reviewing: QA Agent 正在验证
- Done: 任务完成
- Failed: 执行失败，进入重试逻辑
- Escalate: 重试耗尽，请求用户介入
- Cancelled: 用户取消或计划变更
- Skipped: 前置任务失败导致无意义

### 4.2 DAG 任务依赖

任务间支持依赖关系（depends_on），TaskManager 按拓扑排序执行。

**执行算法：**
1. 解析任务列表，构建依赖图
2. 使用 Kahn 算法进行拓扑排序
3. 无依赖的任务立即并行执行
4. 有依赖的任务等待前置任务完成后再执行
5. 检测循环依赖，报错并降级为顺序执行

**降级策略：**
- Orchestrator 输出校验失败（重试 2 次后）：降级为广播模式，将用户消息发送给所有 Agent
- 循环依赖检测：降级为顺序执行（按任务列表顺序）
- 单个 Agent 执行超时（5 分钟）：标记任务为 Failed，触发重试或 Escalate

---

## 5. SSE 协议设计

### 5.1 事件类型

- stream_chunk: 流式文本片段
- message_complete: 消息完成
- task_created: 任务创建
- task_update: 任务状态变更
- task_completed: 任务完成
- task_failed: 任务失败
- clarification_request: 请求澄清
- artifact_diff: 代码 Diff
- preview_ready: 预览就绪
- deploy_progress: 部署进度
- heartbeat: 心跳

---

## 6. 实现优先级

### P0（必须实现）
- Orchestrator Agent + Self-Correction
- 5 个 Agent 角色配置
- TaskManager 状态机 + DAG 调度
- 流式文本渲染（stream_chunk）
- HITL 澄清机制

### P1（应该实现）
- 代码 Diff 组件
- 任务进度展示（TaskPanel）
- Agent 适配器层（最小化）

### P2（可以实现）
- 网页预览（iframe）
- 一键部署（模拟）
- 断线重连 + 心跳

---

## 7. 文件变更清单

### 新增文件
- backend/services/orchestrator.py
- backend/services/task_manager.py
- backend/services/agent_adapter.py
- backend/services/shared_context.py
- backend/routers/tasks.py
- frontend/components/chat/TaskPanel.tsx
- frontend/components/chat/DiffViewer.tsx
- frontend/components/chat/PreviewCard.tsx
- frontend/components/chat/DeployCard.tsx
- frontend/components/chat/ClarificationCard.tsx
- frontend/lib/stores/taskStore.ts

### 修改文件
- backend/services/session.py
- backend/services/router.py
- backend/services/sse_manager.py
- backend/routers/messages.py
- frontend/lib/sse.ts
- frontend/lib/hooks/useChatStream.ts
- frontend/lib/types.ts
- frontend/app/page.tsx

---

**Author:** Claude Code
**Last Updated:** 2026-05-27
