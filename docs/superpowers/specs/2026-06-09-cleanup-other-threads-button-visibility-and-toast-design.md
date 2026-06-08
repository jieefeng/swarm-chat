# 清理其他会话按钮 — 可见性与 Toast 修订设计

**日期**：2026-06-09
**状态**：设计完成
**修订对象**：[2026-06-05-cleanup-other-threads-design.md](./2026-06-05-cleanup-other-threads-design.md)
**对应需求**：用户反馈「清理其他会话」按钮"根本看不到"；希望清理成功后加 toast 反馈

---

## 1. 背景

### 1.1 与 2026-06-05 spec 的关系

2026-06-05 spec 设计了完整链路（后端端点 + 前端 modal + 按钮），但 2026-06-09 收到用户反馈后，**前端实现与原 spec 在两点上不一致**：

| 2026-06-05 spec 原文 | 实际实现 | 偏离原因 |
|---|---|---|
| §5.2 新建独立 `CleanupConfirmModal.tsx`，输入"确认"才能启用按钮 | 复用通用 `ConfirmDialog`，普通确认 modal | 复用现有组件，与项目里其他 modal 风格统一 |
| §5.3 按钮 `threads.length > 1 && currentThreadId` 时显示 | 同 | 按 spec 实现 |
| §5.4 清理后调 `useMessageStore.getState().reset()` 清空消息视图 | **未调用** | 实现遗漏（待补） |
| §7 "前端不写新组件单元测试" | 实际有 `ThreadList.test.tsx` | 与本 spec 无关，不在本次修订范围 |

### 1.2 用户新反馈

1. **「根本看不到」按钮**：测试时无法定位按钮。两个可能原因：
   - `threads.length === 1` 时按钮不渲染（满足 `> 1` 条件才显示）
   - 图标按钮颜色 `text-ink/30` 在 paper-dark 背景上太浅
2. **清理成功无反馈**：modal 关闭 + 列表刷新就完了，用户不确定操作是否生效

### 1.3 目标

- **按钮 always-visible**：让"清理其他"在所有状态（0/1/N 会话）下都可见，仅通过 disabled 状态表达"无操作可执行"
- **按钮带文字"清理其他"**：从纯图标升级为图标+文字，匹配 NewThreadButton 的可发现性
- **加 toast**：清理成功后顶部滑出 2s 轻量提示
- **不破坏 2026-06-05 spec 已实现的部分**（modal 文案、handler 链路、refetch 防御性同步）

---

## 2. 改动范围

| 文件 | 改动 |
|---|---|
| `agenthub/frontend/components/threads/ThreadList.tsx` | (a) 头部按钮：去 `threads.length > 1` 守卫；带文字"清理其他"；分两态（active / disabled）。 (b) 新增 `toast` state + 2s 定时器 + 内联 JSX。 (c) `handleCleanupAll` 成功后 `setToast("已清理 N 个会话")` |
| `agenthub/frontend/components/threads/__tests__/ThreadList.test.tsx` | 新增 3 个 describe：① 按钮渲染（always-visible、disabled 状态、tooltip）；② 清理成功 toast 出现并 2s 后消失；③ 清理失败 modal 错误显示 |

**不变：**
- 后端（`SQLiteManager.delete_all_except` + `DELETE /api/threads?keep=`）✅
- `api.deleteAllThreads()` 客户端 ✅
- `<ConfirmDialog>` cleanup modal 渲染 ✅
- `handleCleanupAll` 函数主体（仅在末尾追加 `setToast`）✅

**不修订的偏离：**
- `useMessageStore.reset()` 调用缺失（2026-06-05 spec §5.4）—— 本次需求外，留作后续 follow-up

---

## 3. 关键设计

### 3.1 按钮两态渲染

**active 态**（有可清理会话：`threads.length > 1 && currentThreadId`）：

```tsx
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
```

**disabled 态**（无可清理会话）：

```tsx
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
```

**设计要点：**
- 两态都渲染同一形状（`flex items-center gap-1.5 px-3 py-2`），通过 className 切换语义颜色
- 红色 `text-danger/80 + bg-danger/[0.06]` 表达"破坏性操作"；灰色 `text-ink/25 + bg-ink/[0.02]` 表达"无操作可执行"
- `flex-shrink-0` 防止被 NewThreadButton 挤压
- `aria-label` 与 `title` 一致，便于屏幕阅读器与悬浮提示

### 3.2 Toast（内联）

```tsx
const [toast, setToast] = useState<string | null>(null);

useEffect(() => {
  if (!toast) return;
  const id = setTimeout(() => setToast(null), 2000);
  return () => clearTimeout(id);
}, [toast]);

// handleCleanupAll 成功路径中, 在 setShowCleanupModal(false) 之前:
setToast(`已清理 ${deletableCount} 个会话`);

// JSX (放在 return 树最外层 div 内顶部):
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

**设计要点：**
- `aria-live="polite"` 让屏幕阅读器在合适时机朗读
- 绝对定位浮在侧边栏顶部中央，不打断主流程
- 颜色用 `text-gold-dim + bg-gold/[0.08]`，与项目 ink/gold 风格统一
- `useEffect` cleanup `clearTimeout` 避免 setState on unmounted

**不引入新组件/不引入新 store：** toast 一次性使用场景，全局化是过度设计（YAGNI）。

### 3.3 错误处理（沿用 2026-06-05 spec §6）

| 场景 | 处理 |
|---|---|
| 后端 404（keep 不存在） | modal 内 `cleanupError` 红色错误条 |
| 后端 5xx / 网络 | modal 内显示"清理失败，请重试"；按钮恢复可点 |
| API 抛错 | 同上；toast **不**出现 |
| 用户取消 modal | 关闭即可；不清空 `toast`（清理未发生） |

---

## 4. 测试

在 `ThreadList.test.tsx` 现有 describe 后追加：

| Describe | Case | 断言 |
|---|---|---|
| A. 按钮渲染 | A1 | 仅 1 会话：按钮存在，`disabled` 属性，title 包含「当前没有其他会话可清理」 |
| A. 按钮渲染 | A2 | 2+ 会话：按钮 enabled，点击打开 cleanup modal（标题"清理其他会话"） |
| B. 清理成功 → toast | B1 | mock 2 会话 + `deleteAllThreads` 成功 → 确认 → 屏幕出现「已清理 1 个会话」 |
| B. 清理成功 → toast | B2 | `vi.useFakeTimers()` 推进 2000ms → toast 从 DOM 消失 |
| B. 清理成功 → toast | B3 | mock `getThreads` refetch 仅返回 1 条 → store 同步为 1 条 |
| C. 清理失败 | C1 | mock `deleteAllThreads` 抛错 → modal 错误条出现 → toast **不**渲染 |

**辅助：**
- `vi.useFakeTimers()` + `vi.advanceTimersByTime(2000)` 控制 setTimeout
- 复用现有 `mockedApi.getThreads.mockResolvedValueOnce` 模式
- 不引入新 mock 库

**验收：**
- `npm run check`（Biome + TypeScript）通过
- `npm test -- ThreadList.test` 全部通过
- 手动：浏览器创建 2+ 会话 → 点「清理其他」→ modal → 确认 → toast 2s → 列表仅剩当前会话

---

## 5. 风险与权衡

- **不引入 `<Toast />` 组件**：未来若有多处 toast 需求，需重构为独立组件 + `uiStore.pushToast`。当前 1 处使用，内联更优。
- **不调用 `useMessageStore.reset()`**：2026-06-05 spec 要求但当前实现遗漏。本 spec 不在范围内，但需在测试 manual 验证时确认"消息视图是否需要清空"。如果需要清空（如当前会话不重置时 messageStore 中可能残留其他 thread 的消息），应作为单独 follow-up 处理。
- **不调整 modal 风格**：仍用现有 `<ConfirmDialog>`，与项目其它删除确认一致（不向 `CleanupConfirmModal` 独立组件方向回退，避免无谓的方向反复）。

---

## 6. 取代关系

| 章节 | 状态 |
|---|---|
| 2026-06-05 spec §1-§4 | 仍生效（背景、用户流程、架构、后端） |
| 2026-06-05 spec §5.1 `api.deleteAllThreads` | 仍生效 |
| 2026-06-05 spec §5.2 独立 `CleanupConfirmModal` | **被实际实现取代**（复用 `ConfirmDialog`），本 spec 沿用该选择 |
| 2026-06-05 spec §5.3 按钮渲染 | **被本 spec §3.1 取代**（always-visible + 带文字 + 两态） |
| 2026-06-05 spec §5.4 `useMessageStore.reset()` | 仍为 spec 目标，但当前实现未做（不在本 spec 范围） |
| 2026-06-05 spec §6 错误处理 | 仍生效 |
| 2026-06-05 spec §7 测试 | **被本 spec §4 取代**（新增前端测试覆盖） |
| 2026-06-05 spec §8 实现步骤 | **被本 spec §2 取代**（变更范围收敛到仅前端两文件） |
| **新增** §3.2 Toast | 本 spec 新增 |
