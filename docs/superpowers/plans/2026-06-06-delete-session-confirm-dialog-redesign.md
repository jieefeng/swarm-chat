# 删除会话确认弹窗重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 抽出可复用的 `ConfirmDialog` 组件，替换 `ThreadList` 中丑陋的原生 `confirm()` / `alert()` 和粗糙的 `CleanupConfirmModal`，所有删除场景统一走"印章红警示 + 实心红按钮"风格。

**Architecture:** 新建一个 `agenthub/frontend/components/ui/ConfirmDialog.tsx` 通用确认弹窗（接受 `title` / `message` / `confirmText` / `cancelText` / `danger` / `isLoading` / `error` 等 props），由 `ThreadList` 用两个实例分别承载单条删除与批量清理。原 `CleanupConfirmModal.tsx` 直接删除（其功能被 ConfirmDialog 完全覆盖）。

**Tech Stack:** React 19、TypeScript、Tailwind CSS v4、vitest + @testing-library/react。

**Spec:** `docs/superpowers/specs/2026-06-06-delete-session-confirm-dialog-redesign.md`

---

## File Structure

| 文件 | 操作 | 职责 |
|---|---|---|
| `agenthub/frontend/components/ui/ConfirmDialog.tsx` | Create | 通用确认弹窗：标题 + 消息 + 印章 + 金线 + 取消/确认按钮 + 错误条 |
| `agenthub/frontend/components/ui/__tests__/ConfirmDialog.test.tsx` | Create | 10 个单元测试覆盖渲染、回调、键盘、loading、错误条 |
| `agenthub/frontend/components/threads/ThreadList.tsx` | Modify | 删除 `confirm()` / `alert()` 调用，删除 `CleanupConfirmModal` 引用，新增 2 个 `<ConfirmDialog>` 实例 |
| `agenthub/frontend/components/threads/CleanupConfirmModal.tsx` | Delete | 完全被 `ConfirmDialog` 覆盖，无引用方后删除 |

**单文件职责边界：**
- `ConfirmDialog.tsx`：纯展示组件，无 store 依赖。`open` / `title` / `message` / `danger` / `isLoading` / `error` 等通过 props 传入，行为通过 `onCancel` / `onConfirm` 回调暴露。
- `ThreadList.tsx`：状态（`deleteTargetId` / `deleteTargetTitle` / `isDeleting` / `deleteError`）与业务逻辑（`handleDeleteThread`）保留在此；UI 通过 `<ConfirmDialog>` 实例展示。

---

### Task 1: ConfirmDialog 基础渲染

**Files:**
- Create: `agenthub/frontend/components/ui/__tests__/ConfirmDialog.test.tsx`
- Create: `agenthub/frontend/components/ui/ConfirmDialog.tsx`

- [ ] **Step 1.1: 写基础渲染的 3 个失败测试**

创建 `agenthub/frontend/components/ui/__tests__/ConfirmDialog.test.tsx`：

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ConfirmDialog } from "../ConfirmDialog";

describe("ConfirmDialog", () => {
  it("renders dialog when open is true", () => {
    render(
      <ConfirmDialog
        open
        title="删除会话？"
        message="此操作不可撤销"
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("does not render dialog when open is false", () => {
    render(
      <ConfirmDialog
        open={false}
        title="删除会话？"
        message="此操作不可撤销"
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("renders title and message", () => {
    render(
      <ConfirmDialog
        open
        title="删除会话？"
        message="此操作不可撤销"
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );
    expect(screen.getByText("删除会话？")).toBeInTheDocument();
    expect(screen.getByText("此操作不可撤销")).toBeInTheDocument();
  });
});
```

- [ ] **Step 1.2: 运行测试，确认失败**

```bash
cd agenthub/frontend && npx vitest run components/ui/__tests__/ConfirmDialog.test.tsx
```

Expected: FAIL — `Failed to resolve import "../ConfirmDialog"` 或类似 "module not found"。

- [ ] **Step 1.3: 实现最小 ConfirmDialog 让测试通过**

创建 `agenthub/frontend/components/ui/ConfirmDialog.tsx`：

```tsx
"use client";

import type { ReactNode } from "react";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: ReactNode;
  confirmText?: string;
  cancelText?: string;
  danger?: boolean;
  isLoading?: boolean;
  error?: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmText = "确定",
  cancelText = "取消",
  isLoading = false,
  onCancel,
  onConfirm,
}: ConfirmDialogProps) {
  if (!open) return null;

  return (
    <div role="dialog" aria-label={title} className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="bg-paper p-7 w-[500px] max-w-[90vw]">
        <h2 className="font-display text-lg font-semibold text-ink">{title}</h2>
        <div className="text-sm text-ink/65 font-body leading-relaxed mt-4">{message}</div>
        <div className="flex justify-end gap-3 mt-6">
          <button type="button" onClick={onCancel} disabled={isLoading}>
            {cancelText}
          </button>
          <button type="button" onClick={onConfirm} disabled={isLoading}>
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 1.4: 重新运行测试，确认 3 个全部通过**

```bash
cd agenthub/frontend && npx vitest run components/ui/__tests__/ConfirmDialog.test.tsx
```

Expected: PASS — 3 tests passing。

- [ ] **Step 1.5: 类型检查 + 提交**

```bash
cd agenthub/frontend && npm run check
```

Expected: 0 type errors。

```bash
cd ../.. && git add agenthub/frontend/components/ui/ConfirmDialog.tsx agenthub/frontend/components/ui/__tests__/ConfirmDialog.test.tsx
git commit -m "feat(frontend): add ConfirmDialog with basic rendering

- Renders dialog when open=true, nothing when open=false
- Renders title and message
- Minimal skeleton, no styling or interaction yet
- Will be expanded with buttons, ESC, loading, error in next tasks

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: 按钮点击事件

**Files:**
- Modify: `agenthub/frontend/components/ui/__tests__/ConfirmDialog.test.tsx`
- Modify: `agenthub/frontend/components/ui/ConfirmDialog.tsx`

- [ ] **Step 2.1: 在测试文件追加 3 个测试**

在 `describe("ConfirmDialog", ...)` 内、最后一个 `it(...)` 后追加：

```tsx
  it("calls onConfirm when confirm button is clicked", () => {
    const onConfirm = vi.fn();
    render(
      <ConfirmDialog
        open
        title="X"
        message="Y"
        onCancel={vi.fn()}
        onConfirm={onConfirm}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "确定" }));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("calls onCancel when cancel button is clicked", () => {
    const onCancel = vi.fn();
    render(
      <ConfirmDialog
        open
        title="X"
        message="Y"
        onCancel={onCancel}
        onConfirm={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "取消" }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("renders custom confirm and cancel text", () => {
    render(
      <ConfirmDialog
        open
        title="X"
        message="Y"
        confirmText="删除"
        cancelText="放弃"
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "删除" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "放弃" })).toBeInTheDocument();
  });
```

同时在文件顶部 `import` 行加 `fireEvent`：

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
```

- [ ] **Step 2.2: 运行测试，确认新增 3 个失败**

```bash
cd agenthub/frontend && npx vitest run components/ui/__tests__/ConfirmDialog.test.tsx
```

Expected: 6 total — 3 pass, 3 fail。失败的 3 个是新增的（按钮文本是"确定"/"取消"而不是"删除"/"放弃"，或 `onConfirm`/`onCancel` 还没绑定等）。

实际上因为 Task 1 的实现里按钮 `onClick` 已经绑定了 `onCancel` / `onConfirm`，且默认文字就是"确定"/"取消"，所以前 2 个测试**会通过**——只有"自定义文字"那个会失败（因为默认文字是"确定"而不是"删除"）。

**预期结果**：6 个测试，5 pass + 1 fail（"renders custom confirm and cancel text"）。

- [ ] **Step 2.3: 实现自定义文字支持**

`ConfirmDialog.tsx` 已经通过 `confirmText` / `cancelText` 默认参数支持，**不需要改实现**。这一步只需要确认测试通过。

- [ ] **Step 2.4: 重新运行测试，确认 6 个全部通过**

```bash
cd agenthub/frontend && npx vitest run components/ui/__tests__/ConfirmDialog.test.tsx
```

Expected: 6 tests passing。

- [ ] **Step 2.5: 提交**

```bash
cd ../.. && git add agenthub/frontend/components/ui/__tests__/ConfirmDialog.test.tsx
git commit -m "test(frontend): add ConfirmDialog button click tests

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: ESC 键与 isLoading 状态

**Files:**
- Modify: `agenthub/frontend/components/ui/__tests__/ConfirmDialog.test.tsx`
- Modify: `agenthub/frontend/components/ui/ConfirmDialog.tsx`

- [ ] **Step 3.1: 在测试文件追加 3 个测试**

在 `describe("ConfirmDialog", ...)` 末尾追加：

```tsx
  it("calls onCancel when Escape is pressed", () => {
    const onCancel = vi.fn();
    render(
      <ConfirmDialog
        open
        title="X"
        message="Y"
        onCancel={onCancel}
        onConfirm={vi.fn()}
      />,
    );
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("does not call onCancel on Escape when isLoading is true", () => {
    const onCancel = vi.fn();
    render(
      <ConfirmDialog
        open
        title="X"
        message="Y"
        isLoading
        onCancel={onCancel}
        onConfirm={vi.fn()}
      />,
    );
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onCancel).not.toHaveBeenCalled();
  });

  it("disables both buttons when isLoading is true", () => {
    render(
      <ConfirmDialog
        open
        title="X"
        message="Y"
        isLoading
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "确定" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "取消" })).toBeDisabled();
  });
```

- [ ] **Step 3.2: 运行测试，确认新增的失败**

```bash
cd agenthub/frontend && npx vitest run components/ui/__tests__/ConfirmDialog.test.tsx
```

Expected: 9 total — 6 pass + 3 fail（ESC 和 disabled 相关）。

- [ ] **Step 3.3: 在 ConfirmDialog 添加 ESC 监听和 isLoading 行为**

替换 `agenthub/frontend/components/ui/ConfirmDialog.tsx` 的整个文件：

```tsx
"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: ReactNode;
  confirmText?: string;
  cancelText?: string;
  danger?: boolean;
  isLoading?: boolean;
  error?: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmText = "确定",
  cancelText = "取消",
  isLoading = false,
  onCancel,
  onConfirm,
}: ConfirmDialogProps) {
  // ESC 键关闭（isLoading 时忽略）
  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isLoading) onCancel();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, isLoading, onCancel]);

  if (!open) return null;

  return (
    <div role="dialog" aria-label={title} className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="bg-paper p-7 w-[500px] max-w-[90vw]">
        <h2 className="font-display text-lg font-semibold text-ink">{title}</h2>
        <div className="text-sm text-ink/65 font-body leading-relaxed mt-4">{message}</div>
        <div className="flex justify-end gap-3 mt-6">
          <button type="button" onClick={onCancel} disabled={isLoading}>
            {cancelText}
          </button>
          <button type="button" onClick={onConfirm} disabled={isLoading}>
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3.4: 重新运行测试，确认 9 个全部通过**

```bash
cd agenthub/frontend && npx vitest run components/ui/__tests__/ConfirmDialog.test.tsx
```

Expected: 9 tests passing。

- [ ] **Step 3.5: 提交**

```bash
cd ../.. && git add agenthub/frontend/components/ui/ConfirmDialog.tsx agenthub/frontend/components/ui/__tests__/ConfirmDialog.test.tsx
git commit -m "feat(frontend): ConfirmDialog ESC + isLoading

- ESC key triggers onCancel (ignored when isLoading)
- Buttons disabled when isLoading

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: 错误条

**Files:**
- Modify: `agenthub/frontend/components/ui/__tests__/ConfirmDialog.test.tsx`
- Modify: `agenthub/frontend/components/ui/ConfirmDialog.tsx`

- [ ] **Step 4.1: 在测试文件追加 1 个测试**

在 `describe("ConfirmDialog", ...)` 末尾追加：

```tsx
  it("displays error message when error prop is set", () => {
    render(
      <ConfirmDialog
        open
        title="X"
        message="Y"
        error="会话不存在"
        onCancel={vi.fn()}
        onConfirm={vi.fn()}
      />,
    );
    expect(screen.getByText("会话不存在")).toBeInTheDocument();
  });
```

- [ ] **Step 4.2: 运行测试，确认新增的失败**

```bash
cd agenthub/frontend && npx vitest run components/ui/__tests__/ConfirmDialog.test.tsx
```

Expected: 10 total — 9 pass + 1 fail（"会话不存在" 文本不存在）。

- [ ] **Step 4.3: 在 ConfirmDialog 添加错误条**

替换 `agenthub/frontend/components/ui/ConfirmDialog.tsx` 的整个文件：

```tsx
"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: ReactNode;
  confirmText?: string;
  cancelText?: string;
  danger?: boolean;
  isLoading?: boolean;
  error?: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmText = "确定",
  cancelText = "取消",
  isLoading = false,
  error,
  onCancel,
  onConfirm,
}: ConfirmDialogProps) {
  // ESC 键关闭（isLoading 时忽略）
  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isLoading) onCancel();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, isLoading, onCancel]);

  if (!open) return null;

  return (
    <div role="dialog" aria-label={title} className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="bg-paper p-7 w-[500px] max-w-[90vw]">
        <h2 className="font-display text-lg font-semibold text-ink">{title}</h2>
        <div className="text-sm text-ink/65 font-body leading-relaxed mt-4">{message}</div>

        {error && (
          <div
            role="alert"
            className="mb-4 mt-4 p-3 bg-danger/10 border border-danger/20 rounded-lg text-sm text-danger font-body"
          >
            {error}
          </div>
        )}

        <div className="flex justify-end gap-3 mt-6">
          <button type="button" onClick={onCancel} disabled={isLoading}>
            {cancelText}
          </button>
          <button type="button" onClick={onConfirm} disabled={isLoading}>
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4.4: 重新运行测试，确认 10 个全部通过**

```bash
cd agenthub/frontend && npx vitest run components/ui/__tests__/ConfirmDialog.test.tsx
```

Expected: 10 tests passing。

- [ ] **Step 4.5: 提交**

```bash
cd ../.. && git add agenthub/frontend/components/ui/ConfirmDialog.tsx agenthub/frontend/components/ui/__tests__/ConfirmDialog.test.tsx
git commit -m "feat(frontend): ConfirmDialog error bar

Displays red error message above buttons when error prop is set.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 5: 视觉精修（印章 / 金线 / 按钮样式 / 遮罩）

**Files:**
- Modify: `agenthub/frontend/components/ui/ConfirmDialog.tsx`

无新测试（视觉细节通过 `npm run check` 类型检查 + 手动 dev server 验证）。

- [ ] **Step 5.1: 应用完整视觉规格**

替换 `agenthub/frontend/components/ui/ConfirmDialog.tsx` 的整个文件：

```tsx
"use client";

import type { ReactNode } from "react";
import { useEffect } from "react";

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: ReactNode;
  confirmText?: string;
  cancelText?: string;
  danger?: boolean;
  isLoading?: boolean;
  error?: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmText = "确定",
  cancelText = "取消",
  danger = true,
  isLoading = false,
  error,
  onCancel,
  onConfirm,
}: ConfirmDialogProps) {
  // ESC 键关闭（isLoading 时忽略）
  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isLoading) onCancel();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, isLoading, onCancel]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 遮罩层 */}
      <button
        type="button"
        aria-label="关闭"
        disabled={isLoading}
        onClick={onCancel}
        className="absolute inset-0 bg-ink/30 backdrop-blur-sm cursor-default disabled:cursor-not-allowed"
      />

      {/* 弹窗本体 */}
      <div
        role="dialog"
        aria-label={title}
        className="relative bg-paper rounded-xl shadow-2xl shadow-ink/20 border border-ink/[0.08] w-[500px] max-w-[90vw] p-7 animate-ink-drop"
      >
        {/* 标题区：印章 + 标题 + 金线 */}
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-9 h-9 flex items-center justify-center rounded-md bg-danger text-white text-[18px] font-display font-semibold shadow-md shadow-danger/30 rotate-[-4deg]">
            慎
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="font-display text-lg font-semibold text-ink">{title}</h2>
            <div className="mt-2 h-px bg-gradient-to-r from-gold/0 via-gold/40 to-gold/0" />
          </div>
        </div>

        {/* 消息区 */}
        <div className="text-sm text-ink/65 font-body leading-relaxed mt-4">
          {message}
        </div>

        {/* 错误条 */}
        {error && (
          <div
            role="alert"
            className="mb-4 mt-4 p-3 bg-danger/10 border border-danger/20 rounded-lg text-sm text-danger font-body"
          >
            {error}
          </div>
        )}

        {/* 按钮组 */}
        <div className="flex justify-end gap-3 mt-6">
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-body font-medium text-ink/60 bg-ink/[0.04] border border-ink/[0.08] rounded-lg hover:bg-ink/[0.07] disabled:opacity-40 transition-colors"
          >
            {cancelText}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={isLoading}
            className={`px-4 py-2 text-sm font-body font-medium rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
              danger
                ? "text-white bg-danger border border-danger hover:bg-danger/90"
                : "text-white bg-gold border border-gold hover:bg-gold/90"
            }`}
          >
            {isLoading ? "处理中…" : confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 5.2: 重新跑测试，确认 10 个仍然通过（视觉改动不应破坏行为）**

```bash
cd agenthub/frontend && npx vitest run components/ui/__tests__/ConfirmDialog.test.tsx
```

Expected: 10 tests passing。

- [ ] **Step 5.3: 类型检查**

```bash
cd agenthub/frontend && npm run check
```

Expected: 0 type errors。

- [ ] **Step 5.4: 视觉验证（推迟到 Task 6.8 一起做）**

本步不需要单独启动 dev server。视觉验证（印章、金线、按钮颜色等）将在 **Task 6.8** 与 ThreadList 集成后一起做端到端检查——那时组件在真实页面里被触发，能完整看到效果。Task 5 只保证代码层面（TypeScript + 测试）正确。

- [ ] **Step 5.5: 提交**

```bash
cd ../.. && git add agenthub/frontend/components/ui/ConfirmDialog.tsx
git commit -m "style(frontend): ConfirmDialog ink-wash + seal-red visual treatment

- Left-top 36x36 red seal stamp (慎, rotated -4deg, ink-shadow)
- Gold gradient line below title (transparent -> gold/40 -> transparent)
- Filled red confirm button (replaces pale-red variant)
- Square corners via rounded-xl (was 2xl)
- Width 500px (was 480)
- bg-ink/30 backdrop (was 20) for stronger focus

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: 改造 ThreadList 集成 ConfirmDialog

**Files:**
- Modify: `agenthub/frontend/components/threads/ThreadList.tsx`

- [ ] **Step 6.1: 读取当前 ThreadList 末尾的 CleanupConfirmModal 引用**

确认 `agenthub/frontend/components/threads/ThreadList.tsx` 末尾（180-185 行附近）有：

```tsx
<CleanupConfirmModal
  open={showCleanupModal}
  ...
/>
```

并将 `import { CleanupConfirmModal } from "./CleanupConfirmModal";` 替换为 `import { ConfirmDialog } from "@/components/ui/ConfirmDialog";`。

- [ ] **Step 6.2: 替换顶部 import**

在 `agenthub/frontend/components/threads/ThreadList.tsx` 顶部：

**找到**：
```tsx
import { CleanupConfirmModal } from "./CleanupConfirmModal";
```

**替换为**：
```tsx
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
```

- [ ] **Step 6.3: 新增 4 个 state**

在 `agenthub/frontend/components/threads/ThreadList.tsx` 文件内、现有 `const [isCleanupLoading, setIsCleanupLoading] = useState(false);` 之后，**新增**：

```tsx
  const [deleteTargetId, setDeleteTargetId] = useState<string | null>(null);
  const [deleteTargetTitle, setDeleteTargetTitle] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
```

- [ ] **Step 6.4: 重写 handleDeleteThread**

**找到**（约 70-93 行）：
```tsx
  const handleDeleteThread = async (threadId: string) => {
    if (!confirm("确定删除这个会话吗？")) return;
    try {
      await api.deleteThread(threadId);

      // 先获取当前状态，再更新 store
      const currentThreads = threads;
      const wasCurrentThread = currentThreadId === threadId;

      removeThread(threadId);

      // 如果删除的是当前会话，切换到下一个会话
      if (wasCurrentThread && currentThreads.length > 1) {
        const nextThread = currentThreads.find((t) => t.id !== threadId);
        if (nextThread) {
          setCurrentThreadId(nextThread.id);
          onThreadSelect(nextThread.id);
        }
      }
    } catch (err) {
      console.error("Failed to delete thread:", err);
      alert("删除会话失败，请重试");
    }
  };
```

**替换为**：
```tsx
  const handleDeleteThread = async () => {
    if (!deleteTargetId) return;
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await api.deleteThread(deleteTargetId);

      // 先获取当前状态，再更新 store
      const currentThreads = threads;
      const wasCurrentThread = currentThreadId === deleteTargetId;

      removeThread(deleteTargetId);

      // 如果删除的是当前会话，切换到下一个会话
      if (wasCurrentThread && currentThreads.length > 1) {
        const nextThread = currentThreads.find((t) => t.id !== deleteTargetId);
        if (nextThread) {
          setCurrentThreadId(nextThread.id);
          onThreadSelect(nextThread.id);
        }
      }
      setDeleteTargetId(null);
    } catch (err) {
      console.error("Failed to delete thread:", err);
      setDeleteError(err instanceof Error ? err.message : "删除失败，请重试");
    } finally {
      setIsDeleting(false);
    }
  };
```

- [ ] **Step 6.5: 修改传给 ThreadItem 的 onDelete 回调**

**找到**（约 165 行附近）：
```tsx
              onDelete={() => handleDeleteThread(thread.id)}
```

**替换为**：
```tsx
              onDelete={() => {
                setDeleteTargetId(thread.id);
                setDeleteTargetTitle(thread.title);
              }}
```

- [ ] **Step 6.6: 替换 JSX 中的 CleanupConfirmModal 为 ConfirmDialog**

**找到**（约 172-183 行）：
```tsx
      <CleanupConfirmModal
        open={showCleanupModal}
        deletableCount={deletableCount}
        keepThreadTitle={keepThreadTitle}
        isLoading={isCleanupLoading}
        error={cleanupError}
        onCancel={() => {
          setShowCleanupModal(false);
          setCleanupError(null);
        }}
        onConfirm={handleCleanupAll}
      />
```

**替换为**：
```tsx
      <ConfirmDialog
        open={deleteTargetId !== null}
        title="删除会话？"
        message={
          <>
            会话「<span className="font-semibold text-ink/80">{deleteTargetTitle}</span>」及所有消息将被永久删除。
            <p className="text-danger/85 font-semibold text-xs mt-2">此操作不可撤销。</p>
          </>
        }
        confirmText="删除"
        isLoading={isDeleting}
        error={deleteError}
        onCancel={() => {
          setDeleteTargetId(null);
          setDeleteError(null);
        }}
        onConfirm={handleDeleteThread}
      />

      <ConfirmDialog
        open={showCleanupModal}
        title="清理其他会话"
        message={
          <>
            <p>将删除 <span className="font-semibold text-danger">{deletableCount}</span> 个会话（包括置顶的）。</p>
            <p className="mt-1">当前会话「<span className="font-semibold text-ink/80">{keepThreadTitle}</span>」将保留。</p>
            <p className="text-danger/85 font-semibold text-xs mt-2">此操作不可撤销。</p>
          </>
        }
        confirmText="确定清理"
        isLoading={isCleanupLoading}
        error={cleanupError}
        onCancel={() => {
          setShowCleanupModal(false);
          setCleanupError(null);
        }}
        onConfirm={handleCleanupAll}
      />
```

- [ ] **Step 6.7: 类型检查**

```bash
cd agenthub/frontend && npm run check
```

Expected: 0 type errors。如果有错误，根据提示修复（常见问题：未使用的 import、props 拼写错误）。

- [ ] **Step 6.8: 启动 dev server 做集成验证**

```bash
cd agenthub/frontend && npm run dev
```

打开 http://localhost:7000 ，需要至少 2 个会话才能看到清理按钮。

**手动验证清单**：
- [ ] **单条删除**：列表中 hover 单条会话 → 右侧出现 🗑️ → 点击 → **新 ConfirmDialog 居中弹出**（不是浏览器原生 confirm）
- [ ] **单条删除取消**：点"取消"或按 ESC → 弹窗关闭，列表无变化
- [ ] **单条删除确认**：点"删除" → 列表立即少一条，弹窗关闭
- [ ] **单条删除失败**：模拟后端 500（修改 `api.deleteThread` 临时抛错）→ 弹窗内显示红色错误条，**不弹原生 alert**
- [ ] **批量清理**：点击头部 🗑️ → 弹窗显示 N 个会话被删除的提示
- [ ] **批量清理确认**：点"确定清理" → 列表只剩当前会话
- [ ] **批量清理失败**：模拟后端 500 → 弹窗内显示错误条
- [ ] **互斥**：单条删除弹窗和批量清理弹窗不会同时显示

- [ ] **Step 6.9: 提交**

```bash
cd ../.. && git add agenthub/frontend/components/threads/ThreadList.tsx
git commit -m "feat(frontend): use ConfirmDialog for thread deletion

- Replace native confirm()/alert() with reusable ConfirmDialog
- Add 4 states: deleteTargetId, deleteTargetTitle, isDeleting, deleteError
- Refactor handleDeleteThread to use state instead of native dialogs
- Two ConfirmDialog instances: single delete + batch cleanup

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 7: 删除旧 CleanupConfirmModal

**Files:**
- Delete: `agenthub/frontend/components/threads/CleanupConfirmModal.tsx`

- [ ] **Step 7.1: 确认无引用**

```bash
cd "D:/AAComputerCourse/AACode/muiltAgent" && grep -r "CleanupConfirmModal" --include="*.ts" --include="*.tsx" agenthub/frontend/ agenthub/backend/
```

Expected: 0 matches（Task 6 已移除 import）。

如果有残留 import，先清理再继续。

- [ ] **Step 7.2: 删除文件**

```bash
cd "D:/AAComputerCourse/AACode/muiltAgent" && rm agenthub/frontend/components/threads/CleanupConfirmModal.tsx
```

- [ ] **Step 7.3: 类型检查 + 测试**

```bash
cd agenthub/frontend && npm run check
```

Expected: 0 type errors。

```bash
cd agenthub/frontend && npx vitest run
```

Expected: 全部测试通过（包括所有现有 modal 测试 + 新增的 ConfirmDialog 10 个测试）。

- [ ] **Step 7.4: 提交**

```bash
cd ../.. && git add -A
git commit -m "refactor(frontend): remove CleanupConfirmModal (replaced by ConfirmDialog)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 8: 最终手动验证

**Files:** 无（验证步骤）

- [ ] **Step 8.1: 跑全套验证**

```bash
cd agenthub/frontend && npm run check
```

Expected: 0 errors（Biome + TypeScript）。

```bash
cd agenthub/frontend && npx vitest run
```

Expected: 全部测试通过。

- [ ] **Step 8.2: 启动 dev server 做端到端验证**

```bash
cd agenthub/frontend && npm run dev
```

打开 http://localhost:7000 ，运行以下场景：

| # | 场景 | 期望 |
|---|---|---|
| 1 | 创建 2+ 个会话 | 列表显示多个会话 |
| 2 | hover 单条会话 → 点击 🗑️ | 弹窗居中弹出，有印章、金线、警示句、实心红按钮 |
| 3 | 点"取消" | 弹窗关闭，列表无变化 |
| 4 | 按 ESC | 弹窗关闭 |
| 5 | 重新打开 → 点"删除" | 列表少一条，弹窗关闭 |
| 6 | 删除当前活跃会话 | 自动切换到列表中其他会话 |
| 7 | 点击头部 🗑️（"清理其他"） | 弹窗显示 N 个会话被删除 |
| 8 | 点"确定清理" | 列表只剩当前会话 |
| 9 | 在 700px 宽窗口下打开弹窗 | 弹窗不超出屏幕 |
| 10 | 在 1920px 宽窗口下打开弹窗 | 弹窗在视口正中（不是左上角） |

- [ ] **Step 8.3: 提交（如果之前有未提交的修复）**

```bash
cd ../.. && git status --short --untracked-files=no
```

如果有未提交改动：

```bash
git add -A
git commit -m "fix(frontend): post-verification tweaks

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

如果没改动，跳过此步。

---

## Definition of Done

- [ ] `ConfirmDialog.tsx` 存在于 `agenthub/frontend/components/ui/`
- [ ] `ConfirmDialog.test.tsx` 包含 10 个测试，全部通过
- [ ] `ThreadList.tsx` 不再引用 `confirm()` / `alert()` / `CleanupConfirmModal`
- [ ] `CleanupConfirmModal.tsx` 文件已删除
- [ ] `npm run check` 0 errors
- [ ] `npx vitest run` 全部通过
- [ ] 手动验证 10 个场景全部通过
- [ ] 8 个原子提交（每个 task 1-2 个 commit）记录在 git log
