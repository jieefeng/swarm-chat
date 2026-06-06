# 每个会话支持修改默认 Agent 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `AgentSelector` 上加"设为默认"按钮，弹迷你确认 toast 后改写该 thread 的 localStorage 默认 agent。

**Architecture:** 三处改动。新增 `SetDefaultConfirmToast` 小组件（纯展示）；`AgentSelector` 加 `defaultAgentId`/`onSetDefault` props + 设为默认按钮；`HomePage (forum/page.tsx)` 维护 `pendingDefaultAgentId` 状态串联两者。复用现有 `useDefaultAgent` hook（不动它）。

**Tech Stack:** Next.js 15 + React 19 + Tailwind v4 + Vitest 2 + @testing-library/react 16 + TypeScript 5

---

## File Structure

| 文件 | 状态 | 责任 |
|------|------|------|
| `agenthub/frontend/components/agents/SetDefaultConfirmToast.tsx` | 创建 | 迷你确认 toast，纯展示 |
| `agenthub/frontend/components/agents/__tests__/SetDefaultConfirmToast.test.tsx` | 创建 | Toast 单元测试 |
| `agenthub/frontend/components/agents/__tests__/AgentSelector.test.tsx` | 创建 | AgentSelector 单元测试 |
| `agenthub/frontend/components/agents/AgentSelector.tsx` | 修改 | 加 `defaultAgentId` prop、「默认」徽章、「设为默认」按钮 |
| `agenthub/frontend/app/forum/page.tsx` | 修改 | 串联 toast 状态，监听 thread 切换清 pending |

> 注：HomePage 集成测试**省略**——Next.js client component + 多 zustand store + useChatStream，依赖重且项目内无先例；改用 type-check + 手工验证覆盖。

---

### Task 1: SetDefaultConfirmToast 组件（最简起点）

**Files:**
- Create: `agenthub/frontend/components/agents/SetDefaultConfirmToast.tsx`
- Create: `agenthub/frontend/components/agents/__tests__/SetDefaultConfirmToast.test.tsx`

- [ ] **Step 1: 写失败测试**

在 `agenthub/frontend/components/agents/__tests__/SetDefaultConfirmToast.test.tsx` 写入：

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SetDefaultConfirmToast } from "../SetDefaultConfirmToast";

describe("SetDefaultConfirmToast", () => {
  it("renders agent name in prompt", () => {
    render(
      <SetDefaultConfirmToast
        agentName="开发"
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.getByText(/将.*开发.*设为默认/)).toBeInTheDocument();
  });

  it("calls onConfirm when 确定 clicked", () => {
    const onConfirm = vi.fn();
    render(
      <SetDefaultConfirmToast
        agentName="开发"
        onConfirm={onConfirm}
        onCancel={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "确定" }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("calls onCancel when 取消 clicked", () => {
    const onCancel = vi.fn();
    render(
      <SetDefaultConfirmToast
        agentName="开发"
        onConfirm={vi.fn()}
        onCancel={onCancel}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "取消" }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
```

- [ ] **Step 2: 跑测试，验证失败**

Run:
```bash
cd agenthub/frontend && npx vitest run components/agents/__tests__/SetDefaultConfirmToast.test.tsx
```
Expected: FAIL with "Cannot find module '../SetDefaultConfirmToast'"

- [ ] **Step 3: 写最小实现**

创建 `agenthub/frontend/components/agents/SetDefaultConfirmToast.tsx`：

```tsx
"use client";

interface SetDefaultConfirmToastProps {
  agentName: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function SetDefaultConfirmToast({
  agentName,
  onConfirm,
  onCancel,
}: SetDefaultConfirmToastProps) {
  return (
    <div
      role="dialog"
      aria-label="设为默认 agent 确认"
      className="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-10 bg-paper rounded-lg shadow-lg border border-ink/[0.08] px-4 py-2.5 flex items-center gap-3 font-body text-sm whitespace-nowrap"
    >
      <span className="text-ink/70">
        将 <span className="text-ink font-medium">{agentName}</span> 设为默认？
      </span>
      <div className="flex gap-1.5">
        <button
          type="button"
          onClick={onCancel}
          className="px-2.5 py-1 rounded-md text-ink/50 hover:bg-ink/[0.04] transition-colors"
        >
          取消
        </button>
        <button
          type="button"
          onClick={onConfirm}
          className="px-2.5 py-1 rounded-md bg-gold/15 text-gold-dim border border-gold/25 hover:bg-gold/25 transition-colors"
        >
          确定
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: 跑测试，验证通过**

Run:
```bash
cd agenthub/frontend && npx vitest run components/agents/__tests__/SetDefaultConfirmToast.test.tsx
```
Expected: PASS (3 tests)

- [ ] **Step 5: 提交**

```bash
git add agenthub/frontend/components/agents/SetDefaultConfirmToast.tsx agenthub/frontend/components/agents/__tests__/SetDefaultConfirmToast.test.tsx
git commit -m "feat(frontend): 新增 SetDefaultConfirmToast 组件"
```

---

### Task 2: AgentSelector 接收 defaultAgentId 并显示「默认」徽章

**Files:**
- Modify: `agenthub/frontend/components/agents/AgentSelector.tsx`（props interface + chip 渲染）
- Create: `agenthub/frontend/components/agents/__tests__/AgentSelector.test.tsx`

- [ ] **Step 1: 写失败测试**

创建 `agenthub/frontend/components/agents/__tests__/AgentSelector.test.tsx`：

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { Agent } from "@/lib/types";
import { AgentSelector } from "../AgentSelector";

const makeAgent = (id: string, nickname: string): Agent => ({
  id,
  name: id.toUpperCase(),
  role: "test",
  nickname,
  color: { primary: "#000", secondary: "#fff" },
});

const agents: Agent[] = [
  makeAgent("pm", "产品"),
  makeAgent("dev", "开发"),
  makeAgent("qa", "测试"),
];

describe("AgentSelector", () => {
  it("renders all agents", () => {
    render(
      <AgentSelector
        agents={agents}
        activeAgentId={null}
        defaultAgentId={null}
        onAgentSelect={vi.fn()}
        onSetDefault={vi.fn()}
      />,
    );
    expect(screen.getByText("产品")).toBeInTheDocument();
    expect(screen.getByText("开发")).toBeInTheDocument();
    expect(screen.getByText("测试")).toBeInTheDocument();
  });

  it("shows 默认 badge on the default agent chip", () => {
    render(
      <AgentSelector
        agents={agents}
        activeAgentId={null}
        defaultAgentId="dev"
        onAgentSelect={vi.fn()}
        onSetDefault={vi.fn()}
      />,
    );
    const devChip = screen.getByText("开发").closest("[role='button']");
    expect(devChip).toHaveTextContent("默认");
  });

  it("does not show 默认 badge on non-default chips", () => {
    render(
      <AgentSelector
        agents={agents}
        activeAgentId={null}
        defaultAgentId="dev"
        onAgentSelect={vi.fn()}
        onSetDefault={vi.fn()}
      />,
    );
    const pmChip = screen.getByText("产品").closest("[role='button']");
    expect(pmChip).not.toHaveTextContent("默认");
  });
});
```

- [ ] **Step 2: 跑测试，验证失败**

Run:
```bash
cd agenthub/frontend && npx vitest run components/agents/__tests__/AgentSelector.test.tsx
```
Expected: FAIL with TS error "Property 'defaultAgentId' does not exist on type 'AgentSelectorProps'"（因为 props 还没加）。

- [ ] **Step 3: 修改 AgentSelector**

在 `agenthub/frontend/components/agents/AgentSelector.tsx` 中做两处改动。

**改动 A**：把现有 `AgentSelectorProps` interface 替换为：

```tsx
interface AgentSelectorProps {
  agents: Agent[];
  activeAgentId: string | null;
  defaultAgentId: string | null;
  onAgentSelect: (agentId: string) => void;
  onSetDefault: (agentId: string) => void;
}
```

**改动 B**：把现有函数签名替换为：

```tsx
export function AgentSelector({
  agents,
  activeAgentId,
  defaultAgentId,
  onAgentSelect,
  onSetDefault,
}: AgentSelectorProps) {
```

**改动 C**：在 chip 内部，紧跟昵称 `<span>`（约第 80 行之后）插入条件渲染的「默认」徽章：

```tsx
{/* 默认 Agent 徽章 */}
{agent.id === defaultAgentId && (
  <span
    className="text-[9px] px-1.5 py-0.5 rounded-full bg-gold/15 text-gold-dim font-medium"
    title="当前默认 Agent"
  >
    默认
  </span>
)}
```

- [ ] **Step 4: 跑测试，验证通过**

Run:
```bash
cd agenthub/frontend && npx vitest run components/agents/__tests__/AgentSelector.test.tsx
```
Expected: PASS (3 tests)

- [ ] **Step 5: 类型检查**

Run:
```bash
cd agenthub/frontend && npx tsc --noEmit
```
Expected: 0 errors（因为 `forum/page.tsx` 还**没**传新 props——Task 4 才传）

如果报错说"Property X is required"导致 page.tsx 编译失败，先**忽略**这一项；继续到 Task 4 一次性传齐。

- [ ] **Step 6: 提交**

```bash
git add agenthub/frontend/components/agents/AgentSelector.tsx agenthub/frontend/components/agents/__tests__/AgentSelector.test.tsx
git commit -m "feat(frontend): AgentSelector 加 defaultAgentId 与「默认」徽章"
```

---

### Task 3: AgentSelector 增加「设为默认」按钮

**Files:**
- Modify: `agenthub/frontend/components/agents/AgentSelector.tsx`（在 chip 内部加新按钮）
- Modify: `agenthub/frontend/components/agents/__tests__/AgentSelector.test.tsx`（追加 3 个测试）

- [ ] **Step 1: 追加失败测试**

在 `agenthub/frontend/components/agents/__tests__/AgentSelector.test.tsx` 顶部 imports 区域加 `import { fireEvent } from "@testing-library/react";`，然后在 `describe("AgentSelector", ...)` 内部、`});` 关闭前追加：

```tsx
  it("shows 设为默认 button on non-default chips", () => {
    render(
      <AgentSelector
        agents={agents}
        activeAgentId={null}
        defaultAgentId="dev"
        onAgentSelect={vi.fn()}
        onSetDefault={vi.fn()}
      />,
    );
    const pmChip = screen.getByText("产品").closest("[role='button']");
    expect(
      pmChip?.querySelector("button[aria-label='设为默认']"),
    ).toBeInTheDocument();
  });

  it("does not show 设为默认 button on the default chip", () => {
    render(
      <AgentSelector
        agents={agents}
        activeAgentId={null}
        defaultAgentId="dev"
        onAgentSelect={vi.fn()}
        onSetDefault={vi.fn()}
      />,
    );
    const devChip = screen.getByText("开发").closest("[role='button']");
    expect(
      devChip?.querySelector("button[aria-label='设为默认']"),
    ).not.toBeInTheDocument();
  });

  it("calls onSetDefault with the agent id when 设为默认 clicked", () => {
    const onSetDefault = vi.fn();
    render(
      <AgentSelector
        agents={agents}
        activeAgentId={null}
        defaultAgentId="dev"
        onAgentSelect={vi.fn()}
        onSetDefault={onSetDefault}
      />,
    );
    const pmChip = screen.getByText("产品").closest("[role='button']");
    const btn = pmChip?.querySelector(
      "button[aria-label='设为默认']",
    ) as HTMLButtonElement;
    fireEvent.click(btn);
    expect(onSetDefault).toHaveBeenCalledWith("pm");
  });
```

- [ ] **Step 2: 跑测试，验证失败**

Run:
```bash
cd agenthub/frontend && npx vitest run components/agents/__tests__/AgentSelector.test.tsx
```
Expected: FAIL — 3 个新测试全部失败，按钮尚未渲染。

- [ ] **Step 3: 修改 AgentSelector chip 渲染**

在 `AgentSelector.tsx` 的 chip 内部，紧贴现有 `<button>`（⚙ 设置）**之前**插入新按钮：

```tsx
{/* 设为默认按钮（非默认 chip 才显示） */}
{agent.id !== defaultAgentId && (
  <button
    aria-label="设为默认"
    onClick={(e) => {
      e.stopPropagation();
      onSetDefault(agent.id);
    }}
    className="ml-0.5 p-0.5 text-ink/20 hover:text-gold/60 transition-colors opacity-0 group-hover:opacity-100"
    title="设为默认 Agent"
  >
    <svg
      className="w-3 h-3"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
      />
    </svg>
  </button>
)}
```

- [ ] **Step 4: 跑测试，验证通过**

Run:
```bash
cd agenthub/frontend && npx vitest run components/agents/__tests__/AgentSelector.test.tsx
```
Expected: PASS (6 tests total)

- [ ] **Step 5: 提交**

```bash
git add agenthub/frontend/components/agents/AgentSelector.tsx agenthub/frontend/components/agents/__tests__/AgentSelector.test.tsx
git commit -m "feat(frontend): AgentSelector 加「设为默认」按钮"
```

---

### Task 4: HomePage 串联 toast 状态

**Files:**
- Modify: `agenthub/frontend/app/forum/page.tsx`

- [ ] **Step 1: 修改 page.tsx**

在 `agenthub/frontend/app/forum/page.tsx` 中做以下 6 处改动：

**改动 A**：顶部 import 区（大约第 5 行 import 后）追加：

```tsx
import { SetDefaultConfirmToast } from "@/components/agents/SetDefaultConfirmToast";
```

**改动 B**：在现有 `useState` 三连后（约第 25 行 `useState<string | null>(null)` 后）追加：

```tsx
const [pendingDefaultAgentId, setPendingDefaultAgentId] = useState<
  string | null
>(null);
```

**改动 C**：现有 `useDefaultAgent` 解构（32-33 行）原样保持（已拿 `defaultAgentId, setDefaultAgentId`）。

**改动 D**：把现有 `<AgentSelector ... />` 调用（约 218-222 行）替换为：

```tsx
<AgentSelector
  agents={agents}
  activeAgentId={activeAgentId}
  defaultAgentId={defaultAgentId}
  onAgentSelect={setActiveAgentId}
  onSetDefault={setPendingDefaultAgentId}
/>
```

**改动 E**：在 `useEffect(() => { ... loadData() ... }, [setAgents])`（约 110-127 行）**之后**追加新 effect：

```tsx
useEffect(() => {
  setPendingDefaultAgentId(null);
}, [currentThreadId]);
```

**改动 F**：在现有 `{showAgentModal && <DefaultAgentModal ... />}` 块**之后**追加 toast 渲染：

```tsx
{pendingDefaultAgentId &&
  (() => {
    const pendingAgent = agents.find((a) => a.id === pendingDefaultAgentId);
    if (!pendingAgent) return null;
    return (
      <div className="absolute right-6 top-16 z-40">
        <SetDefaultConfirmToast
          agentName={pendingAgent.nickname || pendingAgent.name}
          onConfirm={() => {
            setDefaultAgentId(pendingDefaultAgentId);
            setPendingDefaultAgentId(null);
          }}
          onCancel={() => setPendingDefaultAgentId(null)}
        />
      </div>
    );
  })()}
```

- [ ] **Step 2: 类型检查**

Run:
```bash
cd agenthub/frontend && npx tsc --noEmit
```
Expected: 0 errors

- [ ] **Step 3: 跑所有 agent 组件测试**

Run:
```bash
cd agenthub/frontend && npx vitest run components/agents
```
Expected: PASS (AgentSelector 6 + SetDefaultConfirmToast 3 = 9 tests)

- [ ] **Step 4: 提交**

```bash
git add agenthub/frontend/app/forum/page.tsx
git commit -m "feat(frontend): HomePage 串联 SetDefaultConfirmToast 状态"
```

---

### Task 5: Biome 检查与手工验证

**Files:** 无（或 `biome --write` 自动修复过的文件）

- [ ] **Step 1: Biome + tsc 检查**

Run:
```bash
cd agenthub/frontend && npm run check
```
Expected: Biome 0 issues; tsc 0 errors

- [ ] **Step 2: 启动 dev 服务器手工验证**

启动后端：
```bash
cd agenthub/backend && python main.py
```
另开终端启动前端：
```bash
cd agenthub/frontend && npm run dev
```
浏览器打开 `http://localhost:7000`。

验证清单：
- [ ] 进入任意 thread，顶部 AgentSelector 看到「默认」徽章在某个 chip 上
- [ ] hover 其他 chip，星形 icon 在右侧出现
- [ ] 点击星形 icon → 浮出迷你确认 toast（"将 X 设为默认？" + 取消/确定）
- [ ] 点「确定」→ 「默认」徽章移动到新 chip；新 chip 名字显示
- [ ] 点「取消」→ toast 关闭，徽章位置不变
- [ ] 切到别的 thread → 该 thread 的「默认」徽章独立显示（不受上一个 thread 设置影响）
- [ ] 刷新页面 → 之前设置的「默认」agent 仍在（localStorage 持久化）
- [ ] **回归**：点 chip 切 active（不高亮默认）依旧正常；`@agent` 切 active 仍走 mention；无 @ 消息仍走默认；新建 thread 弹 DefaultAgentModal 仍正常

- [ ] **Step 3: 提交（如 biome --write 修复了什么）**

```bash
git status
```
如果只有 `biome --write` 触发的格式修复：

```bash
git add -u
git commit -m "chore: biome --write 自动修复"
```

如果没修复任何东西，**不**提交。

---

## Self-Review Checklist

完成后逐项核对：

- [ ] **Spec 覆盖**：
  - spec §2.1 用户流程（hover → 弹 toast → 确认 → 改 localStorage）→ Task 2 ★、Task 3 按钮、Task 1 toast、Task 4 状态串联
  - spec §3.1 文件改动表（3 个文件：AgentSelector / forum/page.tsx / 新组件 + 测试）→ 全部覆盖
  - spec §3.2 AgentSelector 新接口（`defaultAgentId: string | null`、`onSetDefault: (id: string) => void`）→ Task 2/3 实现 + 测试断言
  - spec §3.3 SetDefaultConfirmToast 接口 → Task 1
  - spec §4.2 状态图（pendingDefaultAgentId 状态、event 流）→ Task 4
  - spec §5.1 AgentSelector 视觉（★ 标记、hover 按钮）→ Task 2 徽章 + Task 3 按钮
  - spec §5.2 SetDefaultConfirmToast 视觉（卡片、确定/取消、金色风格）→ Task 1
  - spec §6 边界情况（默认 agent 不在 agents 列表 → Task 2 条件渲染兜底；切换 thread 清 pending → Task 4 effect）
  - spec §7 实现步骤 → Task 1-4 1:1 对应
  - spec §8 显式排除（后端 / 全局默认 / 新建流程改动）→ 全部不涉及

- [ ] **无占位符**：
  - 所有代码块完整
  - 无 "TBD" / "TODO" / "add appropriate error handling" / "fill in details"

- [ ] **类型一致**：
  - `defaultAgentId: string | null` — spec §3.2、Task 2 props、Task 3 测试、Task 4 调用
  - `onSetDefault: (agentId: string) => void` — spec §3.2、Task 2 props、Task 3 测试、Task 4 调用
  - `SetDefaultConfirmToast({ agentName, onConfirm, onCancel })` — spec §3.3、Task 1 props、Task 4 渲染

- [ ] **频繁提交**：5 个 Task，5 次 commit（最后一个 task 可能因 biome 修复 0/1 次）

- [ ] **每步可独立验证**：每个 Task 的 Step 4 / Step 2 / Step 3 都有具体的 vitest/tsc 命令与预期输出
