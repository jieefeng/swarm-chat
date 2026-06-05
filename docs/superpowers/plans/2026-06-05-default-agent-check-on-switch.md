# 切换会话时检查默认 Agent 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 切换会话时同步检查 localStorage 中是否存有该线程的默认 Agent，无则弹窗引导选择

**Architecture:** 前端逻辑改动，新增同步函数读取 localStorage，在 `handleThreadSelect` 中做分支处理

**Tech Stack:** Next.js 15, Zustand, TypeScript, localStorage

---

## 文件结构

| 文件 | 改动 |
|------|------|
| `agenthub/frontend/lib/hooks/useDefaultAgent.ts` | 新增 `getStoredDefaultAgentId` 同步导出函数 |
| `agenthub/frontend/app/page.tsx` | 修改 `handleThreadSelect` 增加检查；修复 `handleAgentSelect` 的 `pendingThreadId` 路径 |

---

## Task1: 新增同步函数到 useDefaultAgent.ts

**Files:**
- Modify: `agenthub/frontend/lib/hooks/useDefaultAgent.ts:7-9`

- [ ] **Step 1: 添加同步读取函数**

在 `getStorageKey` 函数之后、`useDefaultAgent` hook 之前，新增一个同步函数：

```typescript
/**
 * 同步读取 localStorage 中指定线程的默认 Agent ID
 * 供 handleThreadSelect 同步检查使用，不依赖 React 状态
 */
export function getStoredDefaultAgentId(threadId: string): string | null {
  if (!threadId) return null;
  try {
    return localStorage.getItem(getStorageKey(threadId));
  } catch {
    return null;
  }
}
```

在文件顶部 `"use client";` 之后添加 JSDoc 注释，函数放在 `getStorageKey` 之后、`useDefaultAgent` 之前。

- [ ] **Step 2: 验证语法正确**

确认文件可以正常解析，无语法错误。

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/lib/hooks/useDefaultAgent.ts
git commit -m "feat: add getStoredDefaultAgentId sync helper"
```

---

## Task 2: 修改 page.tsx — handleThreadSelect 增加默认 Agent 检查

**Files:**
- Modify: `agenthub/frontend/app/page.tsx:37-48`（handleThreadSelect 函数）

- [ ] **Step 1: 添加 getStoredDefaultAgentId 导入**

在文件顶部找到 `useDefaultAgent` 的导入行：
```typescript
import { useDefaultAgent } from "@/lib/hooks/useDefaultAgent";
```

改为：
```typescript
import { useDefaultAgent, getStoredDefaultAgentId } from "@/lib/hooks/useDefaultAgent";
```

- [ ] **Step 2: 修改 handleThreadSelect 函数体**

将现有的 `handleThreadSelect` 函数：
```typescript
const handleThreadSelect = async (threadId: string) => {
  useThreadStore.getState().setCurrentThreadId(threadId);
  try {
    const data = await api.getThreadMessages(threadId);
    useMessageStore.getState().reset();
    data.messages?.forEach((m) => {
      useMessageStore.getState().addMessage(m);
    });
  } catch (err) {
    console.error("Failed to load thread messages:", err);
  }
};
```

替换为：
```typescript
const handleThreadSelect = async (threadId: string) => {
  // 同步检查 localStorage 中是否有默认 Agent
  const storedDefaultAgent = getStoredDefaultAgentId(threadId);

  if (!storedDefaultAgent) {
    // 无默认 Agent → 弹窗，用户选择后再切换
    setPendingThreadId(threadId);
    setShowAgentModal(true);
    return;
  }

  // 有默认 Agent → 正常切换
  useThreadStore.getState().setCurrentThreadId(threadId);
  setActiveAgentId(storedDefaultAgent);
  try {
    const data = await api.getThreadMessages(threadId);
    useMessageStore.getState().reset();
    data.messages?.forEach((m) => {
      useMessageStore.getState().addMessage(m);
    });
  } catch (err) {
    console.error("Failed to load thread messages:", err);
  }
};
```

- [ ] **Step 3: 运行类型检查**

```bash
cd agenthub/frontend && npm run check
```

确认无 TypeScript 错误。

- [ ] **Step 4: 提交**

```bash
git add agenthub/frontend/app/page.tsx
git commit -m "feat: check default agent on thread switch, prompt if none"
```

---

## Task 3:修复 page.tsx — handleAgentSelect 的 pendingThreadId 路径

**Files:**
- Modify: `agenthub/frontend/app/page.tsx:62-71`（handleAgentSelect 函数）

- [ ] **Step 1: 确认当前 handleAgentSelect 实现**

查看现有代码：
```typescript
const handleAgentSelect = (agentId: string) => {
  setDefaultAgentId(agentId);
  setActiveAgentId(agentId);
  setShowAgentModal(false);

  if (pendingThreadId) {
    handleThreadSelect(pendingThreadId);
    setPendingThreadId(null);
  }
};
```

这段代码**已经是正确的**——`pendingThreadId` 存在时调用 `handleThreadSelect` 完成切换。无需修改。

（注：此任务为验证任务，确认后可直接标记完成）

- [ ] **Step 2: 提交（无改动）**

无需提交，确认代码正确后继续。

---

## Task 4: 整体验证

**Files:**
- Verify: `agenthub/frontend/app/page.tsx`
- Verify: `agenthub/frontend/lib/hooks/useDefaultAgent.ts`

- [ ] **Step 1: 运行全量类型检查**

```bash
cd agenthub/frontend && npm run check
```

期望：无错误。

- [ ] **Step 2: 启动前端验证**

```bash
cd agenthub/frontend && npm run dev
```

期望：dev server 正常启动，http://localhost:7000 可访问。

- [ ] **Step 3: 手动测试场景**

| 场景 | 操作 | 预期 |
|------|------|------|
|切换到有默认 Agent 的会话 | 点击已有会话 | 正常切换，不弹窗 |
| 切换到无默认 Agent 的会话 | 点击之前没设置默认 Agent 的会话 | 弹窗选择 |
| 新建会话 | 点击新建会话按钮 | 弹窗选择（已有流程） |
| 首次加载 | 刷新页面 | 自动选中第一个线程，不弹窗 |

- [ ] **Step 4: 提交所有改动**

```bash
git add agenthub/frontend/app/page.tsx agenthub/frontend/lib/hooks/useDefaultAgent.ts
git commit -m "feat: check default agent on thread switch with modal prompt"
```

---

## Spec 覆盖检查

| Spec 要求 | 对应任务 |
|----------|----------|
| 切换会话时同步检查 localStorage | Task 2 Step 2 |
| 无默认 Agent 则弹窗 | Task 2 Step 2 |
| 有默认 Agent 正常切换 | Task 2 Step 2 |
| 新建会话流程不变 | 无改动，已满足 |
| 首次加载不弹窗 | ThreadList mount 时不走 handleThreadSelect，已满足 |
| getStoredDefaultAgentId 同步函数 | Task 1 |
| handleAgentSelect pendingThreadId 修复 | Task 3（验证为无需改动） |

---

##依赖关系

```
Task 1 → Task 2 → Task 3 → Task 4
         ↑
         依赖 Task 1 的导出
```

Task 1 必须先完成，Task 2 依赖 Task 1 新增的函数。