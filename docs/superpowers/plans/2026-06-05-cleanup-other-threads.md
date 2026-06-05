# 清理其他会话按钮 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在会话列表头部新增"清理"按钮，删除除当前活跃会话外的所有会话（含置顶），用"输入确认"二次确认弹窗保证安全。

**Architecture:** 后端新增 `DELETE /api/threads?keep=<id>` 端点 + `SQLiteManager.delete_all_except()` 方法（单条 SQL + ON DELETE CASCADE）；前端新增独立 `CleanupConfirmModal` 组件（不与现有 modal 共享基础组件）+ `api.deleteAllThreads()` + `ThreadList` 头部按钮 + 状态联动。

**Tech Stack:** FastAPI + aiosqlite (后端)、Next.js 15 + React + Zustand (前端)、Tailwind v4 (样式)、pytest (后端测试)、Biome (前端类型检查)。

---

## File Structure

| 文件 | 操作 | 职责 |
|------|------|------|
| `agenthub/backend/services/sqlite_manager.py` | 修改 | 新增 `delete_all_except()` 方法 |
| `agenthub/backend/routers/threads.py` | 修改 | 新增 `DELETE /api/threads` 端点 |
| `agenthub/backend/tests/test_sqlite_manager.py` | 修改 | 新增 `delete_all_except` 单元测试 |
| `agenthub/backend/tests/test_threads_api.py` | 修改 | 新增 3 个 API 集成测试 |
| `agenthub/frontend/lib/api.ts` | 修改 | 新增 `deleteAllThreads()` 方法 |
| `agenthub/frontend/components/threads/CleanupConfirmModal.tsx` | 新建 | 独立 Modal 组件（输入"确认"才能确认） |
| `agenthub/frontend/components/threads/ThreadList.tsx` | 修改 | 头部新增按钮 + 弹窗状态 + handler |

---

## Task 1: 后端 - 添加 `SQLiteManager.delete_all_except` 方法

**Files:**
- Modify: `agenthub/backend/services/sqlite_manager.py:145-154`（在 `delete_thread` 之后）
- Test: `agenthub/backend/tests/test_sqlite_manager.py`（在文件末尾追加）

- [ ] **Step 1: 写失败的测试**

在 `agenthub/backend/tests/test_sqlite_manager.py` 末尾追加：

```python
@pytest.mark.asyncio
async def test_delete_all_except_keeps_specified_thread(db):
    """delete_all_except 删除除指定会话外的所有会话"""
    id1 = await db.create_thread(title="Keep", user_id="user1")
    id2 = await db.create_thread(title="Delete 1", user_id="user1")
    id3 = await db.create_thread(title="Delete 2", user_id="user1")

    deleted_count = await db.delete_all_except(id1)

    assert deleted_count == 2
    assert await db.get_thread(id1) is not None
    assert await db.get_thread(id2) is None
    assert await db.get_thread(id3) is None


@pytest.mark.asyncio
async def test_delete_all_except_returns_zero_when_only_keep_exists(db):
    """只有一个会话时 delete_all_except 返回 0"""
    id1 = await db.create_thread(title="Only", user_id="user1")

    deleted_count = await db.delete_all_except(id1)

    assert deleted_count == 0
    assert await db.get_thread(id1) is not None


@pytest.mark.asyncio
async def test_delete_all_except_cascades_messages(db):
    """delete_all_except 级联删除被删会话的消息"""
    keep_id = await db.create_thread(title="Keep", user_id="user1")
    del_id = await db.create_thread(title="Delete", user_id="user1")
    await db.add_message(thread_id=del_id, role="user", content="bye")

    # 确认消息存在
    msgs_before = await db.get_messages(del_id)
    assert len(msgs_before) == 1

    await db.delete_all_except(keep_id)

    # 消息应被级联删除
    msgs_after = await db.get_messages(del_id)
    assert msgs_after == []
    assert await db.get_thread(keep_id) is not None
```

- [ ] **Step 2: 运行测试确认它们失败**

Run: `cd agenthub/backend && python -m pytest tests/test_sqlite_manager.py::test_delete_all_except_keeps_specified_thread tests/test_sqlite_manager.py::test_delete_all_except_returns_zero_when_only_keep_exists tests/test_sqlite_manager.py::test_delete_all_except_cascades_messages -v`
Expected: 3 个 FAILED，错误信息包含 `'SQLiteManager' object has no attribute 'delete_all_except'`

- [ ] **Step 3: 实现方法**

在 `agenthub/backend/services/sqlite_manager.py` 第 154 行（`delete_thread` 方法结束之后）追加：

```python
    async def delete_all_except(self, keep_thread_id: str) -> int:
        """删除除指定会话外的所有会话（级联删除消息）。

        Returns: 删除的会话数量
        """
        db = _require_db(self._db)
        cursor = await db.execute(
            "DELETE FROM threads WHERE id != ?", (keep_thread_id,)
        )
        await db.commit()
        return cursor.rowcount
```

- [ ] **Step 4: 重新运行测试确认通过**

Run: `cd agenthub/backend && python -m pytest tests/test_sqlite_manager.py -v`
Expected: 所有 `test_delete_all_except_*` 测试 PASS，其他既有测试仍 PASS

- [ ] **Step 5: 提交**

```bash
git add agenthub/backend/services/sqlite_manager.py agenthub/backend/tests/test_sqlite_manager.py
git commit -m "feat(backend): add SQLiteManager.delete_all_except"
```

---

## Task 2: 后端 - 添加 `DELETE /api/threads` 端点

**Files:**
- Modify: `agenthub/backend/routers/threads.py:106-107`（在 `delete_thread` 之后追加新端点）
- Test: `agenthub/backend/tests/test_threads_api.py`（在 `TestThreadsAPI` 类内追加）

- [ ] **Step 1: 写失败的测试**

在 `agenthub/backend/tests/test_threads_api.py` 的 `TestThreadsAPI` 类末尾追加（参考 `test_delete_thread` 的风格）：

```python
    def test_delete_all_threads_except_keep(self):
        """DELETE /api/threads?keep=<id> 删除除指定会话外的所有会话"""
        t1 = self._create_thread("保留")
        t2 = self._create_thread("待删 1")
        t3 = self._create_thread("待删 2")

        response = client.delete(
            f"/api/threads?keep={t1['id']}",
            headers=HEADERS,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["deleted_count"] == 2

        # 验证只剩 t1
        response = client.get("/api/threads", headers=HEADERS)
        assert response.status_code == 200
        ids = [t["id"] for t in response.json()["threads"]]
        assert t1["id"] in ids
        assert t2["id"] not in ids
        assert t3["id"] not in ids

    def test_delete_all_threads_keep_missing_returns_404(self):
        """DELETE /api/threads?keep=<不存在> 返回 404"""
        response = client.delete(
            "/api/threads?keep=thread_nonexistent",
            headers=HEADERS,
        )
        assert response.status_code == 404

    def test_delete_all_threads_cascades_messages(self):
        """DELETE /api/threads 级联删除被删会话的消息"""
        import asyncio
        from agenthub.backend.routers.threads import sqlite_manager

        keep_thread = self._create_thread("保留会话")
        doomed_thread = self._create_thread("待删会话")

        async def _add_test_message():
            await sqlite_manager.init_db()
            await sqlite_manager.add_message(
                thread_id=doomed_thread["id"],
                role="user",
                content="待删消息",
                agent_id="user",
                sender_name="用户",
            )
        asyncio.run(_add_test_message())

        # 确认消息存在
        async def _verify_message_exists():
            return await sqlite_manager.get_messages(doomed_thread["id"])
        msgs_before = asyncio.run(_verify_message_exists())
        assert len(msgs_before) == 1

        # 调用 bulk delete
        response = client.delete(
            f"/api/threads?keep={keep_thread['id']}",
            headers=HEADERS,
        )
        assert response.status_code == 200

        # 验证被删会话的消息已被级联清空
        async def _verify_message_cascaded():
            return await sqlite_manager.get_messages(doomed_thread["id"])
        msgs_after = asyncio.run(_verify_message_cascaded())
        assert msgs_after == []
```

- [ ] **Step 2: 运行新测试确认它们失败**

Run: `cd agenthub/backend && python -m pytest tests/test_threads_api.py::TestThreadsAPI::test_delete_all_threads_except_keep tests/test_threads_api.py::TestThreadsAPI::test_delete_all_threads_keep_missing_returns_404 tests/test_threads_api.py::TestThreadsAPI::test_delete_all_threads_cascades_messages -v`
Expected: 3 个 FAILED，错误包含 `404` 或 `405`（端点未注册）

- [ ] **Step 3: 实现端点**

在 `agenthub/backend/routers/threads.py` 第 106 行（`delete_thread` 函数结束之后）追加：

```python
@router.delete("/threads")
async def delete_all_threads(keep: str = Query(..., description="要保留的会话 ID")):
    """清理除指定会话外的所有会话（包括置顶的）"""
    db = await _get_db()

    # 验证 keep 指向的会话存在
    existing = await db.get_thread(keep)
    if existing is None:
        raise HTTPException(status_code=404, detail="Thread to keep not found")

    deleted_count = await db.delete_all_except(keep)
    return {"success": True, "deleted_count": deleted_count}
```

- [ ] **Step 4: 重新运行测试确认通过**

Run: `cd agenthub/backend && python -m pytest tests/test_threads_api.py -v`
Expected: 所有 `test_delete_all_threads_*` 测试 PASS，其他既有测试仍 PASS

- [ ] **Step 5: 提交**

```bash
git add agenthub/backend/routers/threads.py agenthub/backend/tests/test_threads_api.py
git commit -m "feat(backend): add DELETE /api/threads bulk cleanup endpoint"
```

---

## Task 3: 前端 - 添加 `api.deleteAllThreads` 方法

**Files:**
- Modify: `agenthub/frontend/lib/api.ts:121-131`（在 `deleteThread` 之后）

- [ ] **Step 1: 添加方法**

在 `agenthub/frontend/lib/api.ts` 第 131 行（`deleteThread` 方法结束之后）追加：

```typescript
  async deleteAllThreads(
    keepThreadId: string,
  ): Promise<{ success: boolean; deleted_count: number }> {
    const res = await fetch(
      `${API_BASE}/api/threads?keep=${encodeURIComponent(keepThreadId)}`,
      {
        method: "DELETE",
        headers,
      },
    );
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${res.status}`);
    }
    return res.json();
  },
```

- [ ] **Step 2: 验证类型**

Run: `cd agenthub/frontend && npm run check`
Expected: 无错误（Biome + TypeScript）

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/lib/api.ts
git commit -m "feat(frontend): add api.deleteAllThreads client method"
```

---

## Task 4: 前端 - 创建 `CleanupConfirmModal` 组件

**Files:**
- Create: `agenthub/frontend/components/threads/CleanupConfirmModal.tsx`

- [ ] **Step 1: 创建组件文件**

新建 `agenthub/frontend/components/threads/CleanupConfirmModal.tsx`，写入：

```tsx
"use client";

import { useEffect, useState } from "react";
import { XMarkIcon } from "@heroicons/react/24/outline";

interface CleanupConfirmModalProps {
  open: boolean;
  deletableCount: number;
  keepThreadTitle: string;
  isLoading: boolean;
  error: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}

export function CleanupConfirmModal({
  open,
  deletableCount,
  keepThreadTitle,
  isLoading,
  error,
  onCancel,
  onConfirm,
}: CleanupConfirmModalProps) {
  const [confirmText, setConfirmText] = useState("");

  // 打开时清空输入框
  useEffect(() => {
    if (open) {
      setConfirmText("");
    }
  }, [open]);

  // ESC 键关闭
  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isLoading) onCancel();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, isLoading, onCancel]);

  if (!open) return null;

  const canConfirm = confirmText === "确认" && !isLoading;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* 遮罩层 */}
      <div
        className="absolute inset-0 bg-ink/30 backdrop-blur-sm"
        onClick={isLoading ? undefined : onCancel}
      />

      {/* Modal 内容 */}
      <div className="relative bg-paper rounded-2xl shadow-2xl shadow-ink/10 border border-ink/[0.08] w-[480px] max-w-[90vw] p-6 animate-ink-drop">
        {/* 标题栏 */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display text-lg font-semibold text-ink tracking-wide">
            清理其他会话
          </h2>
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="text-ink/30 hover:text-ink/60 transition-colors disabled:opacity-30"
            aria-label="关闭"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* 副文本 */}
        <div className="mb-5 text-sm text-ink/60 font-body leading-relaxed">
          <p>
            将删除{" "}
            <span className="font-semibold text-danger">{deletableCount}</span>{" "}
            个会话（包括置顶的）。
          </p>
          <p className="mt-2">
            当前会话「
            <span className="font-semibold text-ink/80">
              {keepThreadTitle}
            </span>
            」将保留。
          </p>
          <p className="mt-3 text-danger/80 font-semibold">
            此操作不可撤销。
          </p>
        </div>

        {/* 输入框 */}
        <div className="mb-5">
          <label className="block text-xs font-body font-medium text-ink/50 mb-1.5 tracking-wide">
            请输入「确认」以启用按钮
          </label>
          <input
            type="text"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            placeholder="确认"
            disabled={isLoading}
            className="w-full px-3 py-2 bg-white border border-ink/[0.1] rounded-lg text-sm text-ink placeholder:text-ink/30 focus:outline-none focus:border-gold/40 transition-colors font-body disabled:opacity-50"
          />
        </div>

        {/* 错误条 */}
        {error && (
          <div className="mb-4 p-3 bg-danger/10 border border-danger/20 rounded-lg text-sm text-danger font-body">
            {error}
          </div>
        )}

        {/* 按钮组 */}
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-body font-medium text-ink/50 bg-ink/[0.04] border border-ink/[0.08] rounded-lg hover:bg-ink/[0.06] disabled:opacity-40 transition-colors"
          >
            取消
          </button>
          <button
            onClick={onConfirm}
            disabled={!canConfirm}
            className={`px-4 py-2 text-sm font-body font-medium rounded-lg transition-colors ${
              canConfirm
                ? "text-danger bg-danger/10 border border-danger/30 hover:bg-danger/20"
                : "text-ink/25 bg-ink/[0.03] border border-ink/[0.08] cursor-not-allowed"
            }`}
          >
            {isLoading ? "清理中…" : "确定清理"}
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 验证类型与样式**

Run: `cd agenthub/frontend && npm run check`
Expected: 无错误

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/components/threads/CleanupConfirmModal.tsx
git commit -m "feat(frontend): add CleanupConfirmModal component"
```

---

## Task 5: 前端 - 在 `ThreadList` 头部接入按钮和 Modal

**Files:**
- Modify: `agenthub/frontend/components/threads/ThreadList.tsx`

- [ ] **Step 1: 导入新增依赖**

替换 `agenthub/frontend/components/threads/ThreadList.tsx` 顶部 import（第 1-7 行）：

```tsx
"use client";

import { useEffect, useState } from "react";
import { TrashIcon } from "@heroicons/react/24/outline";
import { api } from "@/lib/api";
import { useThreadStore } from "@/lib/stores/threadStore";
import { useMessageStore } from "@/lib/stores/messageStore";
import { CleanupConfirmModal } from "./CleanupConfirmModal";
import { NewThreadButton } from "./NewThreadButton";
import { ThreadItem } from "./ThreadItem";
```

- [ ] **Step 2: 在组件内增加 state 和 handler**

在 `ThreadList` 函数体的第 17 行（`}: ThreadListProps) {` 之后）添加 state：

```tsx
  const [showCleanupModal, setShowCleanupModal] = useState(false);
  const [cleanupError, setCleanupError] = useState<string | null>(null);
  const [isCleanupLoading, setIsCleanupLoading] = useState(false);
```

在 `handleDeleteThread` 函数之后（第 79 行）追加 `handleCleanupAll`：

```tsx
  const handleCleanupAll = async () => {
    if (!currentThreadId) return;
    setCleanupError(null);
    setIsCleanupLoading(true);
    try {
      await api.deleteAllThreads(currentThreadId);
      const keepThread = threads.find((t) => t.id === currentThreadId);
      setThreads(keepThread ? [keepThread] : []);
      useMessageStore.getState().reset();
      setShowCleanupModal(false);
    } catch (err) {
      console.error("Failed to cleanup threads:", err);
      setCleanupError(
        err instanceof Error ? err.message : "清理失败，请重试",
      );
    } finally {
      setIsCleanupLoading(false);
    }
  };

  const keepThreadTitle =
    threads.find((t) => t.id === currentThreadId)?.title ?? "当前会话";
  const deletableCount = Math.max(0, threads.length - 1);
```

- [ ] **Step 3: 修改头部 JSX**

替换第 86-94 行（`<div className="w-64 ...">` 内的 Header 块）：

```tsx
      {/* Header */}
      <div className="p-4 border-b border-ink/[0.08]">
        <h2 className="font-display text-sm font-semibold text-ink/80 mb-3 tracking-wide">
          会话列表
        </h2>
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
            <NewThreadButton onClick={handleCreateThread} disabled={isLoading} />
          </div>
        </div>
      </div>
```

- [ ] **Step 4: 在 return 末尾、组件结束前插入 Modal**

在最后 `</div>` 之前（第 119 行 `</div>` 之后、组件 `);` 结束之前）追加：

```tsx>
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

- [ ] **Step 5: 验证类型**

Run: `cd agenthub/frontend && npm run check`
Expected: 无错误

- [ ] **Step 6: 手动验证（如果前后端都已启动）**

1. 启动后端：`cd agenthub/backend && python main.py`
2. 启动前端：`cd agenthub/frontend && npm run dev`
3. 创建至少 2 个会话
4. 在列表头部点击垃圾桶按钮 → 应弹出 Modal
5. 输入"确认" → 「确定清理」按钮启用
6. 点击「确定清理」→ 列表应只剩当前活跃会话
7. 验证：刷新页面，只剩当前会话，置顶的也被删除

- [ ] **Step 7: 提交**

```bash
git add agenthub/frontend/components/threads/ThreadList.tsx
git commit -m "feat(frontend): wire up cleanup button in ThreadList header"
```

---

## 验证清单

完成所有任务后：

- [ ] 后端：`cd agenthub/backend && python -m pytest tests/test_sqlite_manager.py tests/test_threads_api.py -v` → 全部 PASS
- [ ] 前端：`cd agenthub/frontend && npm run check` → 无错误
- [ ] 手动验证：清理按钮可见（threads > 1 时）、弹窗工作、输入"确认"启用按钮、清理后只剩当前会话
