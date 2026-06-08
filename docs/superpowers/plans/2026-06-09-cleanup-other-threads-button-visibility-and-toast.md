# Cleanup-Other-Threads Button Visibility + Toast Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the "清理其他" cleanup button always visible (with two semantic states) and show a 2-second toast on successful cleanup, per the spec at `docs/superpowers/specs/2026-06-09-cleanup-other-threads-button-visibility-and-toast-design.md`.

**Architecture:** Two surgical edits in `agenthub/frontend/components/threads/ThreadList.tsx` (header button becomes always-visible two-state + new toast state/effect/JSX) and appending six new test cases in `__tests__/ThreadList.test.tsx`. The cleanup modal, the backend endpoint, the API client, and the store stay unchanged. TDD order: button → toast → error regression → final acceptance.

**Tech Stack:** Next.js 15, React 19, TypeScript 5.5, Zustand 5, Vitest 2, @testing-library/react 16, @heroicons/react 24, Tailwind v4.

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `agenthub/frontend/components/threads/ThreadList.tsx` | Header cleanup button + cleanup modal + thread list rendering | Modify (button two-state; add toast state/effect/JSX) |
| `agenthub/frontend/components/threads/__tests__/ThreadList.test.tsx` | Vitest suite for ThreadList (existing 2 cases + 6 new cases) | Modify (append 3 new `describe` blocks) |
| `docs/superpowers/specs/2026-06-09-cleanup-other-threads-button-visibility-and-toast-design.md` | Authoritative spec | Reference only (no edit) |

No backend, no API client, no store, no new file.

---

## Existing Context the Engineer Needs

- `ThreadList` already imports `useState` from `react` and uses 5 existing states (`showCleanupModal`, `cleanupError`, `isCleanupLoading`, `deleteTargetId`, `deleteTargetTitle`, `isDeleting`, `deleteError`). Two of them (`showCleanupModal`, `cleanupError`, `isCleanupLoading`) belong to the cleanup flow and are reused.
- `handleCleanupAll` (lines 109-131 in current file) already calls `api.deleteAllThreads(currentThreadId)`, refetches the thread list, and writes back to the store. The `cleanupError` and `isCleanupLoading` states are wired through the existing cleanup `<ConfirmDialog>` (lines 216-248). **We only add `setToast(...)` immediately before the existing `setShowCleanupModal(false)` on the success path.**
- `useThreadStore` exposes `setThreads`; `useFakeTimers` is not currently used in the project — this plan introduces it for the first time, but Vitest 2 supports it natively.
- The test file already mocks `@/lib/api` (lines 7-15). Reuse the same `mockedApi` pattern.

---

## Task 1: Button Always-Visible Two-State Rendering

**Files:**
- Modify: `agenthub/frontend/components/threads/__tests__/ThreadList.test.tsx` (append new `describe`)
- Modify: `agenthub/frontend/components/threads/ThreadList.tsx:144-155` (replace the conditional block)

- [ ] **Step 1: Add a new `describe` block for button visibility (A1 + A2 tests)**

Append the following `describe` after the existing two `describe` blocks in `__tests__/ThreadList.test.tsx` (keep `mockedApi`, `baseThread`, and the `beforeEach` from above intact):

```tsx
describe("ThreadList 清理其他按钮 - always-visible 两态渲染", () => {
  const threadB = { ...baseThread, id: "thread_b", title: "会话 B" };

  it("A1: 仅 1 个会话时,按钮存在但 disabled 且 tooltip 为「当前没有其他会话可清理」", async () => {
    mockedApi.getThreads.mockResolvedValueOnce({ threads: [baseThread] });

    render(<ThreadList onThreadSelect={vi.fn()} />);

    const btn = await screen.findByRole("button", { name: /当前没有其他会话可清理/ });
    expect(btn).toBeDisabled();
  });

  it("A2: 2+ 会话时,按钮 enabled 且带文字「清理其他」,点击打开 cleanup modal", async () => {
    mockedApi.getThreads.mockResolvedValueOnce({ threads: [baseThread, threadB] });

    render(<ThreadList onThreadSelect={vi.fn()} />);

    const btn = await screen.findByRole("button", { name: /^清理其他会话$/ });
    expect(btn).not.toBeDisabled();
    expect(btn).toHaveTextContent("清理其他");

    fireEvent.click(btn);

    const dialog = await screen.findByRole("dialog", { name: "清理其他会话" });
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveTextContent("1");
    expect(dialog).toHaveTextContent("会话 A");
  });
});
```

- [ ] **Step 2: Run the new tests to verify they fail against the current code**

Run: `cd agenthub/frontend && npx vitest run components/threads/__tests__/ThreadList.test.tsx -t "清理其他按钮"`
Expected:
- A1: FAIL — current code renders the button only when `threads.length > 1`, so with 1 thread the button is **absent** and `findByRole(... { name: /当前没有其他会话可清理/ })` throws.
- A2: FAIL — current button (when present with 2 threads) has `aria-label="清理其他会话"` but no `清理其他` text content, so `toHaveTextContent("清理其他")` fails.

- [ ] **Step 3: Replace the conditional header block in `ThreadList.tsx` (lines 144-155) with two-state rendering**

Open `agenthub/frontend/components/threads/ThreadList.tsx`. Inside the JSX returned by `ThreadList`, the existing block is:

```tsx
<div className="flex items-center gap-2">
  {threads.length > 1 && currentThreadId && (
    <button
      onClick={() => setShowCleanupModal(true)}
      disabled={isLoading}
      title="清理其他会话"
      aria-label="清理其他会话"
      className="flex-shrink-0 p-2 text-ink/30 hover:text-danger border border-ink/[0.08] hover:border-danger/30 rounded-lg transition-colors disabled:opacity-40"
    >
      <TrashIcon className="w-4 h-4" />
    </button>
  )}
  <div className="flex-1">
    <NewThreadButton
      onClick={handleCreateThread}
      disabled={isLoading}
    />
  </div>
</div>
```

Replace the entire `<div className="flex items-center gap-2">…</div>` block with:

```tsx
<div className="flex items-center gap-2">
  {(() => {
    const canCleanup = threads.length > 1 && currentThreadId !== null;
    if (canCleanup) {
      return (
        <button
          type="button"
          onClick={() => setShowCleanupModal(true)}
          disabled={isLoading}
          title="清理其他会话"
          aria-label="清理其他会话"
          className="flex-shrink-0 flex items-center gap-1.5 px-3 py-2 text-xs font-body text-danger/80 bg-danger/[0.06] border border-danger/15 rounded-lg hover:bg-danger/10 hover:border-danger/30 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <TrashIcon className="w-3.5 h-3.5" />
          清理其他
        </button>
      );
    }
    return (
      <button
        type="button"
        disabled
        title="当前没有其他会话可清理"
        aria-label="当前没有其他会话可清理"
        className="flex-shrink-0 flex items-center gap-1.5 px-3 py-2 text-xs font-body text-ink/25 bg-ink/[0.02] border border-ink/[0.08] rounded-lg cursor-not-allowed"
      >
        <TrashIcon className="w-3.5 h-3.5" />
        清理其他
      </button>
    );
  })()}
  <div className="flex-1">
    <NewThreadButton
      onClick={handleCreateThread}
      disabled={isLoading}
    />
  </div>
</div>
```

- [ ] **Step 4: Run the new tests to verify they now pass**

Run: `cd agenthub/frontend && npx vitest run components/threads/__tests__/ThreadList.test.tsx -t "清理其他按钮"`
Expected: A1 PASS, A2 PASS.

- [ ] **Step 5: Run the full ThreadList suite to confirm no regression**

Run: `cd agenthub/frontend && npx vitest run components/threads/__tests__/ThreadList.test.tsx`
Expected: All 4 cases pass (2 original + 2 new).

- [ ] **Step 6: Commit**

```bash
cd agenthub
git add frontend/components/threads/__tests__/ThreadList.test.tsx frontend/components/threads/ThreadList.tsx
git commit -m "feat(frontend): cleanup button always-visible two-state (active/disabled)"
```

---

## Task 2: Success Toast (3 Cases B1, B2, B3)

**Files:**
- Modify: `agenthub/frontend/components/threads/__tests__/ThreadList.test.tsx` (append new `describe`)
- Modify: `agenthub/frontend/components/threads/ThreadList.tsx` (add toast state, effect, JSX, and `setToast` call inside `handleCleanupAll`)

- [ ] **Step 1: Add a new `describe` block for toast behavior**

Append the following `describe` after the Task 1 block:

```tsx
describe("ThreadList 清理成功 toast - 显示/消失/store 同步", () => {
  const threadB = { ...baseThread, id: "thread_b", title: "会话 B" };

  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("B1: 清理成功后,屏幕出现「已清理 1 个会话」toast", async () => {
    mockedApi.getThreads.mockResolvedValueOnce({ threads: [baseThread, threadB] });
    mockedApi.deleteAllThreads.mockResolvedValue({ success: true, deleted_count: 1 });
    // refetch 后服务端只剩 A
    mockedApi.getThreads.mockResolvedValueOnce({ threads: [baseThread] });

    render(<ThreadList onThreadSelect={vi.fn()} />);

    const btn = await screen.findByRole("button", { name: /^清理其他会话$/ });
    fireEvent.click(btn);

    const confirmBtn = await screen.findByRole("button", { name: "确定清理" });
    fireEvent.click(confirmBtn);

    const toast = await screen.findByRole("status");
    expect(toast).toHaveTextContent("已清理 1 个会话");
  });

  it("B2: 2 秒后 toast 从 DOM 消失", async () => {
    mockedApi.getThreads.mockResolvedValueOnce({ threads: [baseThread, threadB] });
    mockedApi.deleteAllThreads.mockResolvedValue({ success: true, deleted_count: 1 });
    mockedApi.getThreads.mockResolvedValueOnce({ threads: [baseThread] });

    render(<ThreadList onThreadSelect={vi.fn()} />);

    const btn = await screen.findByRole("button", { name: /^清理其他会话$/ });
    fireEvent.click(btn);
    fireEvent.click(await screen.findByRole("button", { name: "确定清理" }));

    await screen.findByRole("status");

    act(() => {
      vi.advanceTimersByTime(2000);
    });

    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("B3: cleanup 后 store 必须与 refetch 后的服务端列表一致(只剩 keepThread)", async () => {
    mockedApi.getThreads.mockResolvedValueOnce({ threads: [baseThread, threadB] });
    mockedApi.deleteAllThreads.mockResolvedValue({ success: true, deleted_count: 1 });
    mockedApi.getThreads.mockResolvedValueOnce({ threads: [baseThread] });

    render(<ThreadList onThreadSelect={vi.fn()} />);

    const btn = await screen.findByRole("button", { name: /^清理其他会话$/ });
    fireEvent.click(btn);
    fireEvent.click(await screen.findByRole("button", { name: "确定清理" }));

    await waitFor(() => {
      const state = useThreadStore.getState();
      expect(state.threads.map((t) => t.id)).toEqual(["thread_a"]);
    });
  });
});
```

Also update the top-of-file `import` line for `@testing-library/react` to add `act`:

```tsx
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `cd agenthub/frontend && npx vitest run components/threads/__tests__/ThreadList.test.tsx -t "toast"`
Expected: All 3 cases FAIL — no toast state/effect/JSX exists yet, so `findByRole("status")` throws.

- [ ] **Step 3: Add the toast state and effect to `ThreadList.tsx`**

Locate the line `const [isDeleting, setIsDeleting] = useState(false);` inside the `ThreadList` function body. Immediately after it (and before `const [deleteError, setDeleteError] = useState<string | null>(null);`), insert:

```tsx
const [toast, setToast] = useState<string | null>(null);
```

Then locate the existing `useEffect` that calls `loadThreads` (the one with `}, []);` on its own line). Immediately after its closing `}, []);` line, add a second `useEffect`:

```tsx
useEffect(() => {
  if (!toast) return;
  const id = setTimeout(() => setToast(null), 2000);
  return () => clearTimeout(id);
}, [toast]);
```

- [ ] **Step 4: Add `setToast(...)` on the cleanup success path**

Locate the `handleCleanupAll` function. The current body (lines 109-131) is:

```tsx
const handleCleanupAll = async () => {
  if (!currentThreadId) return;
  setCleanupError(null);
  setIsCleanupLoading(true);
  try {
    await api.deleteAllThreads(currentThreadId);

    // 防御性同步: 批量清理后从服务端拉取最新列表
    const { threads: latestThreads } = await api.getThreads();
    setThreads(latestThreads || []);

    // 兜底: 若当前会话不在最新列表里(异常情况),清空选中
    if (!latestThreads?.some((t) => t.id === currentThreadId)) {
      setCurrentThreadId(null);
    }
    setShowCleanupModal(false);
  } catch (err) {
    console.error("Failed to cleanup threads:", err);
    setCleanupError(err instanceof Error ? err.message : "清理失败，请重试");
  } finally {
    setIsCleanupLoading(false);
  }
};
```

Replace the `setShowCleanupModal(false);` line with:

```tsx
    setShowCleanupModal(false);
    setToast(`已清理 ${deletableCount} 个会话`);
```

(`deletableCount` is the `const` already declared on line 135 — `const deletableCount = Math.max(0, threads.length - 1);` — which sits BELOW `handleCleanupAll` in the source. JavaScript hoists `const` declarations only as a TDZ; referencing it inside a function that runs **after** render is safe because by the time the user clicks, the entire component body has executed. No reordering needed.)

- [ ] **Step 5: Add the toast JSX inside the component's returned tree**

First, modify the outer wrapper div so the absolutely-positioned toast anchors to the sidebar (not the viewport). Change:

```tsx
<div className="w-64 flex flex-col border-r border-ink/[0.08] bg-paper-dark/50">
```

to:

```tsx
<div className="w-64 relative flex flex-col border-r border-ink/[0.08] bg-paper-dark/50">
```

(only the className changes; the rest of the wrapper stays identical.)

Then, immediately after that opening `<div>` tag, add the toast element:

```tsx
      {/* Toast - 清理成功轻量提示 */}
      {toast && (
        <div
          role="status"
          aria-live="polite"
          className="absolute top-2 left-1/2 -translate-x-1/2 z-50 px-3 py-1.5 text-xs font-body text-gold-dim bg-gold/[0.08] border border-gold/20 rounded-md shadow-sm"
        >
          {toast}
        </div>
      )}
```

- [ ] **Step 6: Run the new tests to verify they pass**

Run: `cd agenthub/frontend && npx vitest run components/threads/__tests__/ThreadList.test.tsx -t "toast"`
Expected: B1 PASS, B2 PASS, B3 PASS.

- [ ] **Step 7: Run the full ThreadList suite to confirm no regression**

Run: `cd agenthub/frontend && npx vitest run components/threads/__tests__/ThreadList.test.tsx`
Expected: All 7 cases pass (2 original + 2 from Task 1 + 3 new).

- [ ] **Step 8: Commit**

```bash
cd agenthub
git add frontend/components/threads/__tests__/ThreadList.test.tsx frontend/components/threads/ThreadList.tsx
git commit -m "feat(frontend): 2s inline toast on cleanup success"
```

---

## Task 3: Cleanup Failure → No Toast (Case C1, Regression)

**Files:**
- Modify: `agenthub/frontend/components/threads/__tests__/ThreadList.test.tsx` (append new `describe`)

- [ ] **Step 1: Add a new `describe` block for failure behavior**

Append the following `describe` after the Task 2 block:

```tsx
describe("ThreadList 清理失败 - modal 错误显示 + 不弹 toast", () => {
  const threadB = { ...baseThread, id: "thread_b", title: "会话 B" };

  it("C1: deleteAllThreads 抛错时,modal 显示错误条,且 toast 不出现", async () => {
    mockedApi.getThreads.mockResolvedValueOnce({ threads: [baseThread, threadB] });
    mockedApi.deleteAllThreads.mockRejectedValue(new Error("网络异常,请重试"));

    render(<ThreadList onThreadSelect={vi.fn()} />);

    const btn = await screen.findByRole("button", { name: /^清理其他会话$/ });
    fireEvent.click(btn);
    fireEvent.click(await screen.findByRole("button", { name: "确定清理" }));

    // 错误条出现 (ConfirmDialog 内部用 role="alert" 渲染错误)
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("网络异常,请重试");

    // toast 不应出现
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run the new test**

Run: `cd agenthub/frontend && npx vitest run components/threads/__tests__/ThreadList.test.tsx -t "清理失败"`
Expected: PASS — the existing `handleCleanupAll` catch block sets `cleanupError`, which the existing `<ConfirmDialog error={cleanupError}>` already renders. `setToast` is **not** called on the failure path, so no `role="status"` element appears. No production code change is needed for this task.

- [ ] **Step 3: Run the full ThreadList suite**

Run: `cd agenthub/frontend && npx vitest run components/threads/__tests__/ThreadList.test.tsx`
Expected: All 8 cases pass (2 original + 2 from Task 1 + 3 from Task 2 + 1 from Task 3).

- [ ] **Step 4: Commit**

```bash
cd agenthub
git add frontend/components/threads/__tests__/ThreadList.test.tsx
git commit -m "test(frontend): cleanup failure shows modal error and no toast"
```

---

## Task 4: Type Check + Manual Verification

**Files:** none (verification only)

- [ ] **Step 1: Run the type checker and linter**

Run: `cd agenthub/frontend && npm run check`
Expected: `tsc --noEmit` reports 0 errors. Biome may auto-format imports / quote style; if it does, re-run the same command to confirm a clean second pass. If Biome rewrites files, commit the rewrites:

```bash
cd agenthub
git add frontend/components/threads/ThreadList.tsx frontend/components/threads/__tests__/ThreadList.test.tsx
git diff --cached --stat
git commit -m "style(frontend): biome auto-format from npm run check"
```

(Skip this commit if Biome reports no changes.)

- [ ] **Step 2: Run the full frontend test suite to catch any cross-file regression**

Run: `cd agenthub/frontend && npx vitest run`
Expected: All component + hook + lib tests pass (no new failures attributable to this change).

- [ ] **Step 3: Start the dev servers and manually verify**

Start backend: `cd agenthub/backend && python main.py` (requires `.env` with `PORT=7010`, `DASHSCOPE_API_KEY`, `LLM_PROVIDER=bailian` per `CLAUDE.md`).
Start frontend: `cd agenthub/frontend && npm run dev` (port 7000).

Then in the browser at `http://localhost:7000`:

1. **Empty state (0 threads)**: refresh page → sidebar shows the disabled "清理其他" button with grey styling and tooltip "当前没有其他会话可清理".
2. **1-thread state**: create a thread via "+ 新建会话" → header now shows the enabled red "清理其他" button.
3. **2+ threads state**: create a second thread → button is still enabled and red. Hover shows the danger-tinted hover background.
4. **Cleanup success**: click "清理其他" → confirm dialog appears with "将删除 1 个会话（包括置顶的）。当前会话「{title}」将保留。此操作不可撤销。" and a red "确定清理" button → click it → modal closes, list collapses to just the kept thread, gold toast "已清理 1 个会话" appears at the top of the sidebar for ~2s.
5. **Cleanup failure**: temporarily break the API (e.g. kill the backend) → repeat step 4 → modal stays open with a red error bar containing the failure message, **no toast** appears.
6. **Keyboard**: Tab to "清理其他" button → press Enter → confirm modal opens as in step 4.

- [ ] **Step 4: Final commit if any manual-fix code changed**

If steps 1-3 surfaced any tweak (typo, off-by-one in `deletableCount`, animation glitch), commit it as `fix(frontend): cleanup button manual QA fixes`. Otherwise no commit is needed.

---

## Acceptance Checklist

- [ ] `npx vitest run components/threads/__tests__/ThreadList.test.tsx` → 8/8 pass
- [ ] `npx vitest run` (full suite) → 0 new failures
- [ ] `npm run check` → 0 TypeScript errors
- [ ] Browser manual: button always visible in all 3 thread-count states with correct active/disabled styling
- [ ] Browser manual: cleanup success shows gold toast for ~2s
- [ ] Browser manual: cleanup failure shows inline modal error and **no** toast
- [ ] Git history: 3-4 atomic commits with Conventional Commits messages (`feat(frontend): …`, `test(frontend): …`, optional `style(frontend): biome auto-format`, optional `fix(frontend): …`)
- [ ] No backend, no API client, no store, no modal-component changes were needed

## Out of Scope (deferred to a follow-up spec)

- The 2026-06-05 spec §5.4 required `useMessageStore.getState().reset()` after cleanup. The current implementation does **not** call it. If the kept thread's message store still holds stale messages from other threads (likely only after a re-mount edge case), wire it in a follow-up spec — **not** this one.
- The 2026-06-05 spec §5.2 originally called for an independent `CleanupConfirmModal` with a "type 确认" guard. The current implementation correctly reuses the shared `<ConfirmDialog>` and is what the user has seen in the browser. The supersede map in `2026-06-09-…-design.md` §6 records this.
