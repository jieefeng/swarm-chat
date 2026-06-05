# 清理其他会话按钮设计

**日期**：2026-06-05
**状态**：设计完成
**对应需求**：在会话列表头部增加"清理"按钮，删除除当前活跃会话外的所有会话（包括置顶的）

---

## 1. 背景与目标

### 问题

当前会话列表已有「单个会话删除」功能（`ThreadItem` 上的 `TrashIcon`），但用户需要逐个删除，繁琐且容易误操作：

- 测试或调试时会产生大量临时会话
- 没有批量清理入口
- 现有 `confirm()` 弹窗对批量操作安全强度不足

### 目标

- 在 `ThreadList` 头部新增"清理"按钮，**一次性删除除当前活跃会话外的所有会话**
- 包含置顶会话（不特殊处理置顶）
- 二次确认：用户必须输入"确认"才能启用"确定"按钮
- 保留当前活跃会话不变

---

## 2. 用户流程

```
用户点击"清理"按钮（头部 TrashIcon）
    ↓
弹出 CleanupConfirmModal
    ↓
显示："将删除 N 个会话（包括置顶的）。
       当前会话「{title}」将保留。
       此操作不可撤销。"
    ↓
用户在输入框中键入"确认"
    ↓
"确定"按钮启用
    ↓
点击"确定"
    ↓
api.deleteAllThreads(currentThreadId)
    ↓
后端 DELETE /api/threads?keep=<currentThreadId>
    ↓
成功 → threadStore.setThreads([keepThread]) + 清空 messageStore
失败 → 弹窗内显示错误，不修改本地状态
```

---

## 3. 架构概览

### 3.1 数据流

```
[ThreadList 头部"清理"按钮]
        │ click
        ▼
[CleanupConfirmModal]
  - 显示将删除的会话数量
  - 用户必须输入"确认"才能启用"确定"按钮
        │ confirm
        ▼
[ThreadList.handleCleanupAll]
  - 调 api.deleteAllThreads(currentThreadId)
  - 成功后: threadStore.setThreads([keepThread]) + clearMessages()
        │
        ▼
[后端 DELETE /api/threads?keep=<currentThreadId>]
  - SQLiteManager.delete_all_except(keep_id)
  - 一条 SQL: DELETE FROM threads WHERE id != ?
  - messages 通过 ON DELETE CASCADE 自动级联删除
        │
        ▼
[返回 {success: true, deleted_count: N}]
```

### 3.2 改动范围

| 层 | 改动 |
|----|------|
| 后端 | 1 个新端点 + 1 个新方法 |
| 前端 | 1 个新 Modal 组件 + 1 个新 API 方法 + `ThreadList` 头部改动 + store 状态联动 |
| 测试 | 后端 3 个新测试用例 |

---

## 4. 后端设计

### 4.1 新增 `SQLiteManager` 方法

文件：`agenthub/backend/services/sqlite_manager.py`

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

### 4.2 新增 FastAPI 端点

文件：`agenthub/backend/routers/threads.py`

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

### 4.3 设计决策

- **`keep` 是必填 query param**：避免误调用导致全删
- **不限制 user_id**：与现有 `delete_thread` 保持一致（都按 ID 查/删）
- **不返回删除的 thread ID 列表**：前端只关心数量，简化接口
- **404 vs 空删**：如果 `keep` 指向不存在的 thread，返回 404 而不是悄悄删除其他（保护用户）

---

## 5. 前端设计

### 5.1 新增 API 方法

文件：`agenthub/frontend/lib/api.ts`

```typescript
async deleteAllThreads(keepThreadId: string): Promise<{ success: boolean; deleted_count: number }> {
  const res = await fetch(`${API_BASE}/api/threads?keep=${encodeURIComponent(keepThreadId)}`, {
    method: "DELETE",
    headers,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${res.status}`);
  }
  return res.json();
},
```

### 5.2 新增 Modal 组件

文件：`agenthub/frontend/components/threads/CleanupConfirmModal.tsx`

**为何不复用现有 modal**：项目内无共享 Modal 基础组件；`AgentConfigModal` 与 `DefaultAgentModal` 各自独立内联实现，样式不统一（`bg-white` vs `bg-paper`）。按"不强行复用"原则新建独立组件，参照 `DefaultAgentModal` 的视觉语言（`bg-paper` + `rounded-2xl`，与 `ThreadList` 协调）。

包含：

- 标题：「清理其他会话」
- 副文本：「将删除 N 个会话（包括置顶的）。当前会话「{title}」将保留。此操作不可撤销。」
- 输入框：placeholder="请输入「确认」以启用按钮"
- 实时校验：仅当输入 === "确认" 时启用「确定」按钮
- 取消 + 确定 按钮组
- 错误条：props 传入 `error` 时显示

Props：

```typescript
interface CleanupConfirmModalProps {
  open: boolean;
  deletableCount: number;
  keepThreadTitle: string;
  isLoading: boolean;
  error: string | null;
  onCancel: () => void;
  onConfirm: () => void;
}
```

### 5.3 ThreadList 改动

文件：`agenthub/frontend/components/threads/ThreadList.tsx`

- 头部布局从「`h2` + `NewThreadButton`」改为：
  ```
  [h2 "会话列表"]
  [TrashIcon 按钮]  [NewThreadButton]
  ```
- "清理"按钮：图标 `TrashIcon`，仅当 `threads.length > 1 && currentThreadId` 时显示
- 点击后：弹出 `CleanupConfirmModal`
- 错误状态由 `ThreadList` 持有（`const [cleanupError, setCleanupError] = useState<string | null>(null)`），传给 Modal 的 `error` prop；取消/重新打开时清空
- 确认后调用 `handleCleanupAll`：

```typescript
const handleCleanupAll = async () => {
  if (!currentThreadId) return;
  setCleanupError(null);
  try {
    await api.deleteAllThreads(currentThreadId);
    const keepThread = threads.find(t => t.id === currentThreadId);
    setThreads(keepThread ? [keepThread] : []);
    // 清空当前消息视图
    useMessageStore.getState().reset();
    setShowCleanupModal(false);
  } catch (err) {
    console.error("Failed to cleanup threads:", err);
    setCleanupError(err instanceof Error ? err.message : "清理失败，请重试");
  }
};
```

### 5.4 Store 改动

- `useThreadStore`（`agenthub/frontend/lib/stores/threadStore.ts`）：**不需要新方法**，直接使用现有 `setThreads([keepThread])` 即可
- `useMessageStore`（`agenthub/frontend/lib/stores/messageStore.ts`）：**已有 `reset()` 方法**（第 60 行：`reset: () => set({ messages: [], isStreaming: false, toolExecutions: {} })`），直接调用即可清空当前消息视图

---

## 6. 错误处理

| 场景 | 处理 |
|------|------|
| 后端返回 404（keep 指向不存在的 thread） | Modal 内显示「目标会话不存在，请刷新页面」红色错误条；不修改本地状态 |
| 后端 5xx / 网络错误 | Modal 内显示「清理失败，请重试」；按钮恢复可点 |
| API 成功但 `success: false` | 同上 |
| 用户在 Modal 中输入"确认"后又改回其他 | 实时禁用按钮（基于 input 状态） |
| 用户关闭 Modal（ESC / 点击遮罩） | 不修改任何状态，关闭即可 |

### 边界 case

- `threads.length <= 1` → 按钮不渲染
- `currentThreadId === null` → 按钮不渲染（防御性判断）
- 删除时如果 SSE 消息正在流式传输 → 流式消息会因为 thread 被删而自然中断（`messages` 表 ON DELETE CASCADE），无需特殊处理

---

## 7. 测试

后端（`agenthub/backend/tests/test_threads_api.py` 新增）：

| 测试 | 断言 |
|------|------|
| `test_delete_all_threads_except_keep` | 创建 3 个 thread；`DELETE /api/threads?keep=<id1>`；剩 1 个，正好是 id1；返回 `deleted_count=2` |
| `test_delete_all_threads_404_when_keep_missing` | `DELETE /api/threads?keep=thread_nonexistent`；返回 404 |
| `test_delete_all_threads_cascades_messages` | 创建 thread + 添加 message；`DELETE /api/threads?keep=<another>`；原 thread 的 message 已被删除 |

**前端不写新组件单元测试**——项目内现有 modal（`AgentConfigModal`、`DefaultAgentModal`）也都无测试，保持代码风格一致。`ThreadList` 的改动通过 `npm run check` 验证类型。

---

## 8. 实现步骤

### 8.1 后端

1. `sqlite_manager.py`：新增 `delete_all_except(keep_thread_id)` 方法
2. `routers/threads.py`：新增 `DELETE /api/threads` 端点
3. `test_threads_api.py`：新增 3 个测试用例

### 8.2 前端

1. `lib/api.ts`：新增 `deleteAllThreads(keepThreadId)` 方法
2. `components/threads/CleanupConfirmModal.tsx`：新建 Modal 组件
3. `components/threads/ThreadList.tsx`：头部布局调整 + 按钮 + handler + modal 状态（`showCleanupModal`、`cleanupError` 两个 state）

### 8.3 验证

- 后端：`pytest tests/test_threads_api.py -v`
- 前端：`npm run check`

---

## 9. 设计原则

- **原子性**：单条 SQL + 一次事务，避免半成功状态
- **二次确认**：输入"确认"才能继续，防止误操作
- **保留当前活跃**：用户正在看的会话始终保留，符合最小惊讶原则
- **无破坏性 API 扩展**：在原有 `routers/threads.py` 内新增端点，不改变现有接口
- **样式协调**：新 Modal 参照现有 `DefaultAgentModal` 视觉语言，与 `ThreadList` 协调
