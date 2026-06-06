# 删除会话确认弹窗重构设计

**日期**：2026-06-06
**状态**：设计完成
**对应需求**：删除会话的弹窗应该居中显示 + 弹窗 UI 现在太丑了

---

## 1. 背景与目标

### 问题

当前项目"删除会话"流程存在两类入口，**两类入口确认体验都不达标**：

| 入口 | 当前实现 | 问题 |
|---|---|---|
| 单条删除（`ThreadItem` 右侧 🗑️） | 浏览器原生 `confirm("确定删除这个会话吗？")` | 1) 居中靠浏览器决定，跨平台不一致；2) 原生 UI 与项目墨韵设计语言割裂 |
| 批量清理（`ThreadList` 头部 🗑️） | 自定义 `CleanupConfirmModal` | 1) 居中代码已写但视觉上仍显粗糙（无警示图标、按钮区分度差、输入框繁琐）；2) 必须输入"确认"两字才解锁，体感重 |

### 目标

- 抽出**一个可复用的 `ConfirmDialog` 组件**，单条删除与批量清理共用
- 弹窗真正**视觉居中**（容器在视口正中央，不依赖浏览器）
- 视觉风格升级：**墨韵底子 + 印章红警示**——保留项目 `paper/ink/gold` 调色板，加入左上方 36×36 红色印章方块 + 标题下金线渐变 + 实心红色确认按钮
- **移除"输入确认"流程**：所有删除场景改为"标题 + 警示文案 + 取消/确认按钮"，点确认即生效
- 替换所有原生 `confirm()` / `alert()`，统一风格

---

## 2. 用户流程

### 2.1 单条删除

```
用户在 ThreadItem 右侧点击 🗑️
        │
        ▼
[ThreadList] 设置 deleteTargetId = thread.id, deleteTargetTitle = thread.title
        │
        ▼
[ConfirmDialog] 居中弹出
  ┌──────────────────────────────────────┐
  │ ┌──┐                                │
  │ │慎│  删除会话？                     │
  │ └──┘  ────── ── ── ── ── ── ──      │
  │                                      │
  │   会话「<会话标题>」及所有消息        │
  │   将被永久删除。                       │
  │                                      │
  │   此操作不可撤销。                     │
  │                                      │
  │                  [ 取消 ]  [ 删 除 ] │
  └──────────────────────────────────────┘
        │
        ├─ 取消 / ESC → 关闭，状态不变
        │
        └─ 确认 → api.deleteThread(id)
                  成功 → removeThread(id) + 切到下一会话（如果删的是当前）
                  失败 → 弹窗内红色错误条，不关闭
```

### 2.2 批量清理

```
用户在 ThreadList 头部点击 🗑️
        │
        ▼
[ThreadList] 设置 showCleanupModal = true
        │
        ▼
[ConfirmDialog] 居中弹出
  ┌──────────────────────────────────────┐
  │ ┌──┐                                │
  │ │慎│  清理其他会话                   │
  │ └──┘  ────── ── ── ── ── ── ──      │
  │                                      │
  │   将删除 N 个会话（包括置顶的）。      │
  │   当前会话「<标题>」将保留。          │
  │                                      │
  │   此操作不可撤销。                     │
  │                                      │
  │                  [ 取消 ]  [确定清理] │
  └──────────────────────────────────────┘
        │
        ├─ 取消 / ESC → 关闭
        │
        └─ 确认 → api.deleteAllThreads(currentThreadId)
                  成功 → setThreads([keepThread]) + 关闭
                  失败 → 弹窗内错误条
```

---

## 3. 架构概览

### 3.1 改动范围

| 层 | 改动 |
|---|---|
| 新增 | `agenthub/frontend/components/ui/ConfirmDialog.tsx`（通用确认弹窗） |
| 新增 | `agenthub/frontend/components/ui/__tests__/ConfirmDialog.test.tsx` |
| 删除 | `agenthub/frontend/components/threads/CleanupConfirmModal.tsx`（被 ConfirmDialog 取代） |
| 修改 | `agenthub/frontend/components/threads/ThreadList.tsx`（替换 confirm/alert + CleanupConfirmModal 引用） |

**后端 / API / store / types：均无改动。**

### 3.2 组件树

```
ThreadList
├── ThreadItem[] (无变化)
├── NewThreadButton (无变化)
└── ConfirmDialog (×2 实例)
    ├── 单条删除实例：受 deleteTargetId !== null 控制
    └── 批量清理实例：受 showCleanupModal 控制
```

---

## 4. 组件设计 — `ConfirmDialog`

文件：`agenthub/frontend/components/ui/ConfirmDialog.tsx`

### 4.1 Props

```typescript
interface ConfirmDialogProps {
  open: boolean;
  title: string;                // 弹窗标题，"删除会话？" / "清理其他会话"
  message: React.ReactNode;     // 副文案，支持 JSX（含高亮文字、警示句）
  confirmText?: string;         // 默认 "确定"
  cancelText?: string;          // 默认 "取消"
  danger?: boolean;             // 默认 true（删除类操作走红按钮）
  isLoading?: boolean;
  error?: string | null;        // 错误条内容，null/undefined 不显示
  onCancel: () => void;
  onConfirm: () => void;
}
```

### 4.2 内部行为

- `open=true` 时渲染一个 `fixed inset-0 z-50` 容器（与现有 `CleanupConfirmModal` 一致，不使用 portal）
- `Escape` 键关闭（`isLoading=true` 时忽略，沿用现状）
- 进入动画 `animate-ink-drop`（与现有 modal 一致）
- `open` 从 `true` → `false` 时不做退出动画（保持简单，不引入 framer-motion）

### 4.3 视觉规格

**容器**：

| 属性 | 值 |
|---|---|
| 背景 | `bg-paper` |
| 圆角 | `rounded-xl` |
| 阴影 | `shadow-2xl shadow-ink/20` |
| 边框 | `border border-ink/[0.08]` |
| 宽度 | `w-[500px] max-w-[90vw]` |
| 内边距 | `p-7` |
| 定位 | `fixed inset-0 z-50 flex items-center justify-center`（明确写死居中） |

**遮罩层**：

| 属性 | 值 |
|---|---|
| 实现 | `absolute inset-0 bg-ink/30 backdrop-blur-sm` |
| 行为 | 透明 `<button>`，点击触发 `onCancel`（`isLoading` 时禁用） |
| 层级 | 弹窗内容下层 |

**印章方块**（左上角，36×36）：

| 属性 | 值 |
|---|---|
| 背景 | `bg-danger` (#B23A48) |
| 文字 | "慎"（`text-white text-[18px] font-display font-semibold`） |
| 旋转 | `rotate(-4deg)` |
| 阴影 | `shadow-md shadow-danger/30`（模拟印泥外溢） |
| 容器类 | `w-9 h-9 flex items-center justify-center rounded-md` |

**标题区**：

| 元素 | 样式 |
|---|---|
| 标题 | `font-display text-lg font-semibold text-ink` |
| 金线 | `<div className="mt-2 h-px bg-gradient-to-r from-gold/0 via-gold/40 to-gold/0" />` |

**消息区**（由 `message` prop 传入）：

| 元素 | 样式 |
|---|---|
| 容器 | `text-sm text-ink/65 font-body leading-relaxed mt-4` |
| 警示句 | `text-danger/85 font-semibold text-xs mt-2`（"此操作不可撤销。"） |

**按钮组**（右下角）：

| 元素 | 样式 |
|---|---|
| 容器 | `flex justify-end gap-3 mt-6`（确认按钮在右、取消按钮在左，间距 12px，与消息区保持 24px 间距） |
| 取消 | `px-4 py-2 text-sm font-body font-medium text-ink/60 bg-ink/[0.04] border border-ink/[0.08] rounded-lg hover:bg-ink/[0.07] disabled:opacity-40` |
| 确认（danger=true） | `px-4 py-2 text-sm font-body font-medium text-white bg-danger border border-danger rounded-lg hover:bg-danger/90 disabled:opacity-40 disabled:cursor-not-allowed` |
| 确认（danger=false） | `px-4 py-2 text-sm font-body font-medium text-white bg-gold border border-gold rounded-lg hover:bg-gold/90`（预留，非删除场景用） |

**错误条**（`error` 非空时显示）：

| 属性 | 值 |
|---|---|
| 位置 | 消息区下方、按钮组上方 |
| 样式 | `mb-4 p-3 bg-danger/10 border border-danger/20 rounded-lg text-sm text-danger font-body` |

### 4.4 键盘交互

| 键 | 行为 |
|---|---|
| `Escape` | 触发 `onCancel`（`isLoading` 时不响应） |
| `Enter` | 本期不绑定（避免用户在输入框时误触） |

### 4.5 焦点管理

- 打开时不自动 focus 确认按钮（避免误触）
- 关闭后焦点回到触发元素（本期不实现，靠浏览器默认行为）
- 弹窗内不使用 `<form>`，无 tab 循环限制

---

## 5. 集成设计 — `ThreadList`

文件：`agenthub/frontend/components/threads/ThreadList.tsx`

### 5.1 状态变更

| 现状 | 改造后 |
|---|---|
| `const [showCleanupModal, setShowCleanupModal] = useState(false)` | 保留 |
| `const [cleanupError, setCleanupError] = useState<string \| null>(null)` | 保留 |
| `const [isCleanupLoading, setIsCleanupLoading] = useState(false)` | 保留 |
| （无） | 新增 `const [deleteTargetId, setDeleteTargetId] = useState<string \| null>(null)` |
| （无） | 新增 `const [deleteTargetTitle, setDeleteTargetTitle] = useState("")` |
| （无） | 新增 `const [isDeleting, setIsDeleting] = useState(false)` |
| （无） | 新增 `const [deleteError, setDeleteError] = useState<string \| null>(null)` |

### 5.2 `handleDeleteThread` 重写

```typescript
const handleDeleteThread = async () => {
  if (!deleteTargetId) return;
  setIsDeleting(true);
  setDeleteError(null);
  try {
    await api.deleteThread(deleteTargetId);

    const currentThreads = threads;
    const wasCurrentThread = currentThreadId === deleteTargetId;
    removeThread(deleteTargetId);

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

**注意**：函数不再接收 `threadId` 参数——从 `deleteTargetId` state 取值。这样 `onClick` 只需设置 state，弹窗确认时才真正发起请求。

### 5.3 `onDelete` 回调（传给 ThreadItem）

```typescript
onDelete={() => {
  setDeleteTargetId(thread.id);
  setDeleteTargetTitle(thread.title);
}}
```

### 5.4 JSX 改造

```tsx
{/* 单条删除弹窗 */}
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

{/* 批量清理弹窗 */}
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

### 5.5 `CleanupConfirmModal` 处理

**直接删除** `agenthub/frontend/components/threads/CleanupConfirmModal.tsx`，其功能被 ConfirmDialog 完整覆盖。`ThreadList.tsx` 顶部 import 同步移除。

---

## 6. 视觉对比

### 6.1 旧 vs 新

| 维度 | 旧（CleanupConfirmModal / native confirm） | 新（ConfirmDialog） |
|---|---|---|
| 居中 | 依赖 `flex items-center justify-center`（单条删除是浏览器决定） | 明确 `fixed inset-0 flex items-center justify-center`，且通过 `z-50` 浮在所有内容之上 |
| 警示元素 | 仅 ✕ 关闭按钮 | 36×36 红色印章方块 + 标题下金线 + 实心红按钮 |
| 按钮区分度 | 取消/确认都是同色系描边按钮 | 取消浅灰、确认实心红，危险感明确 |
| 文案强度 | 单条删除是"确定删除这个会话吗？" | "删除会话？" 标题 + 详细消息 + 警示句，分层清晰 |
| 跨平台一致 | 原生 `confirm()` 在 Chrome/Firefox/Safari 表现不一 | 完全自己渲染，所有平台一致 |

### 6.2 与项目其他 Modal 协调

- `AgentConfigModal` / `DefaultAgentModal`：白底+圆角，**保持现状不动**（不在本设计范围）
- `ConfirmDialog`：墨色文字 + paper 底，与 ThreadList 视觉更搭（与 CleanupConfirmModal 一致的设计语言）

---

## 7. 错误处理

| 场景 | 处理 |
|---|---|
| API 返回 4xx/5xx | `try/catch` → `setXxxError(err.message)` → 弹窗内红色错误条 |
| 网络断开 | 同上（`fetch` 抛 TypeError） |
| 未知异常 | fallback 文案："删除失败，请重试" / "清理失败，请重试" |
| 删除进行中按 ESC | 忽略（`isLoading=true` 时 `onCancel` 不响应） |
| 删除进行中点取消/遮罩 | 取消按钮 disabled、遮罩 disabled |
| 删除成功后重新打开 | `onCancel` 中 `setXxxError(null)` 重置 |
| 错误状态下点重试 | `onConfirm` 开头 `setXxxError(null)`，新一次错误自然覆盖 |

**移除的"丑陋"行为**：

- ❌ 原生 `alert("删除会话失败，请重试")` → 替换为弹窗内错误条
- ❌ 原生 `confirm("确定删除这个会话吗？")` → 替换为 ConfirmDialog

---

## 8. 测试

新文件：`agenthub/frontend/components/ui/__tests__/ConfirmDialog.test.tsx`

| # | 场景 | 断言 |
|---|---|---|
| 1 | `open=true` 时渲染 | 印章方块（"慎"）、标题、消息、按钮可见 |
| 2 | `open=false` 时不渲染 | `queryByRole("dialog")` 为 null |
| 3 | 点确认按钮 | `onConfirm` 被调用 1 次 |
| 4 | 点取消按钮 | `onCancel` 被调用 1 次 |
| 5 | 按 ESC | `onCancel` 被调用 |
| 6 | `isLoading=true` 时按 ESC | `onCancel` **不**被调用 |
| 7 | `isLoading=true` 时按钮 disabled | 取消 + 确认按钮都有 `disabled` 属性 |
| 8 | `error="会话不存在"` | 错误条显示该文本 |
| 9 | 自定义 `confirmText` / `cancelText` | 按钮文字正确 |
| 10 | `danger=true` 时确认按钮是红底白字 | 包含 `bg-danger` 和 `text-white` 类 |

**手动验证清单**：

- [ ] 列表点单条 🗑️ → 弹窗**视口正中**显示，有印章、金线、警示句
- [ ] 列表点单条 🗑️ → 删除成功，列表立即少一条
- [ ] 列表点单条 🗑️ → 模拟 API 失败（断网 / mock 500），弹窗内显示错误条，不弹原生 alert
- [ ] 顶部点"清理其他" → 弹窗显示 N 个会话被删除的提示
- [ ] 顶部点"清理其他" → 加载中时按钮 disabled、ESC 无效
- [ ] 按 ESC → 弹窗关闭
- [ ] 700px 宽度窗口 → 弹窗不超出屏幕（`max-w-[90vw]` 生效）
- [ ] 单条删除弹窗 + 批量清理弹窗不会同时显示（互斥控制正确）

**未覆盖（明确不做）**：

- `ThreadList` 没有现成测试文件，本期不补（超出范围）
- 视觉回归（金线渐变、印章旋转）属于 CSS 细节，不写
- `AgentConfigModal` / `DefaultAgentModal` 不在本次范围，不动

---

## 9. 实现步骤

按以下顺序执行，每步完成后跑 `npm run check` 验证类型：

### 9.1 新建 `ConfirmDialog` 组件

文件：`agenthub/frontend/components/ui/ConfirmDialog.tsx`

- 定义 `ConfirmDialogProps` interface
- 实现 props 解构、ESC 监听、印章 + 标题 + 金线 + 消息 + 错误条 + 按钮组
- 复用 `animate-ink-drop`（globals.css 已定义）
- 不引入新依赖

### 9.2 新建测试

文件：`agenthub/frontend/components/ui/__tests__/ConfirmDialog.test.tsx`

- 10 个测试用例（见 §8）
- 使用 vitest + @testing-library/react（与项目现有测试一致）

### 9.3 改造 `ThreadList`

文件：`agenthub/frontend/components/threads/ThreadList.tsx`

- 移除 `import { CleanupConfirmModal }`
- 引入 `import { ConfirmDialog } from "@/components/ui/ConfirmDialog"`
- 新增 4 个 state（`deleteTargetId` / `deleteTargetTitle` / `isDeleting` / `deleteError`）
- 重写 `handleDeleteThread`
- 修改传给 `ThreadItem` 的 `onDelete` 回调
- JSX：移除 `<CleanupConfirmModal>`，新增 2 个 `<ConfirmDialog>` 实例
- 移除对 `confirm()` 和 `alert()` 的调用

### 9.4 删除 `CleanupConfirmModal`

- 删除文件 `agenthub/frontend/components/threads/CleanupConfirmModal.tsx`

### 9.5 验证

- `npm run check`（Biome + TypeScript）
- `npm test`（跑 ConfirmDialog 新测试）
- 手动跑通 §8 验证清单

---

## 10. 设计原则

- **复用优先**：抽出 `ConfirmDialog` 让单条删除与批量清理共享同一组件，UI 一致
- **删除流程去重**：移除"输入确认"输入框，依赖"印章 + 警示文案 + 实心红按钮"三重信号传递危险感
- **居中显式**：不依赖浏览器默认行为，用 `fixed inset-0 flex items-center justify-center` 强制视口居中
- **设计语言一致**：保留项目 `paper/ink/gold` 调色板，印章红 = 已有 `danger` token，零新增色板
- **范围最小化**：不动后端、不动 API、不动 store、不动其他 modal（`AgentConfigModal` / `DefaultAgentModal`）
- **可测试性**：`ConfirmDialog` 接收纯函数式 props，无 store 依赖，10 个单元测试覆盖核心行为
