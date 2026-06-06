# 每个会话支持修改默认 Agent 设计

**日期**：2026-06-06
**状态**：设计完成
**对应需求**：当前每个会话一旦设置默认 Agent 后，没有 UI 入口可以修改，只能清 localStorage。

---

## 1. 背景与目标

### 问题
`useDefaultAgent(threadId)` 用 `localStorage[agenthub_default_agent_<threadId>]` 给每个 thread 存默认 agent：
- 首次进入 thread 或新建 thread 时，强制弹 `DefaultAgentModal` 让用户选一次
- 之后切回该 thread 自动读取
- 顶部 `AgentSelector` 的点击、`@mention` 都只切 `activeAgentId`，**不写默认**
- 想换默认 agent 只能手动清 localStorage，**没有 UI 入口**

### 目标
- 在 `AgentSelector` 上提供"设为默认"的 UI 入口
- 用户点选后，弹迷你确认 toast 防止误操作
- 确认后修改 localStorage 中该 thread 的默认 agent
- 视觉上明确标识当前默认 agent（★ 标记）

---

## 2. 用户流程

### 2.1 修改当前会话的默认 Agent

```
用户在聊天区顶部看到 [PM] [架构] [开发] [QA] [编排]
                            ▲  已有默认 = 架构，★ 标记
用户 hover chip「开发」
    ↓
右上角出现「设为默认」小按钮（与现有 ⚙ 设置按钮同区域/风格）
    ↓
点击「设为默认」
    ↓
迷你确认 toast 浮现在该 chip 下方
    ┌─────────────────────┐
    │ 设为默认：开发？   │
    │ [取消]  [确定]     │
    └─────────────────────┘
    ↓
用户点「确定」
    ↓
localStorage[agenthub_default_agent_<threadId>] = "developer"
    ↓
defaultAgentId state 更新
    ↓
★ 标记从「架构」chip 移到「开发」chip
活跃 agent（activeAgentId）不变
聊天记录不变
Toast 浮一个 "已将「开发」设为默认" 1.5 秒后消失
```

### 2.2 不影响原有行为

| 行为 | 是否变化 |
|------|----------|
| 点击 chip 切换 `activeAgentId` | 不变，仍是临时切活跃 |
| `@agent` 提及 | 不变，仍是临时切活跃 |
| 无 `@` 发送消息 | 不变，仍走 `defaultAgentId` |
| 新建/首次进入 thread 弹 DefaultAgentModal | 不变 |
| 切换 thread 时同步检查默认 | 不变（已有功能） |

---

## 3. 组件设计

### 3.1 文件改动

| 文件 | 改动 |
|------|------|
| `components/agents/AgentSelector.tsx` | 加 `defaultAgentId` prop；默认 chip 显示 ★；hover 出现"设为默认"按钮（与现有 ⚙ 共存）；点击触发 `onSetDefault(agentId)` |
| `app/forum/page.tsx` | 传 `defaultAgentId` 给 AgentSelector；新增 `pendingDefaultAgentId` 状态；点"设默认"时弹 `SetDefaultConfirmToast` |
| `components/agents/SetDefaultConfirmToast.tsx`（新增） | 小型 inline toast，"将 [名字] 设为默认？" + [取消] [确定] |

### 3.2 AgentSelector 新接口

```typescript
interface AgentSelectorProps {
  agents: Agent[];
  activeAgentId: string | null;
  defaultAgentId: string | null;          // 新增
  onAgentSelect: (agentId: string) => void;
  onSetDefault: (agentId: string) => void; // 新增
}
```

### 3.3 SetDefaultConfirmToast 接口

```typescript
interface SetDefaultConfirmToastProps {
  agentName: string;          // 用于显示"将 X 设为默认？"
  anchorName: string;         // agent 元素名（可选，用于头像着色）
  onConfirm: () => void;
  onCancel: () => void;
  position: { top: number; left: number };  // 相对父容器
}
```

---

## 4. 数据流

### 4.1 数据源（不变）

- 唯一数据源：`localStorage[agenthub_default_agent_<threadId>]`
- 读写入口：`useDefaultAgent(threadId)` hook（已存在）
- 同步读：`getStoredDefaultAgentId(threadId)`（已存在）

### 4.2 状态图

```
HomePage state:
  pendingDefaultAgentId: string | null  // null = toast 关闭
  defaultAgentId: from useDefaultAgent  // 单一权威

事件流：
  AgentSelector.onSetDefault(id)
    → HomePage.setPendingDefaultAgentId(id)
  用户在 toast 里点确定
    → HomePage.setDefaultAgentId(id)  // useDefaultAgent 内部写 localStorage + 触发 state
    → setPendingDefaultAgentId(null)
  用户在 toast 里点取消 / 外部点击 / Esc
    → setPendingDefaultAgentId(null)
```

### 4.3 useDefaultAgent 不变

不修改 `useDefaultAgent.ts`。它已经：
- 从 localStorage 读
- `setDefaultAgentId(id)` 写 localStorage + 触发 state
- 错误处理（try/catch console.error）

`HomePage` 拿到 `defaultAgentId` 直接传给 `AgentSelector` 即可。

---

## 5. UI 设计

### 5.1 AgentSelector 视觉

```
[🌳 PM  🌿]  [💧 架构 💧 ★]  [⚔️ 开发 ⚔️]  [🔥 QA 🔥]  [🪨 编排 🪨]
                              ▲
                          当前默认 ★
                            
hover [⚔️ 开发] 时：
  - chip 背景高亮（现有 hover 行为）
  - 右上角出现两个小图标：⚙（已有，设置 LLM）+ ⭐/「默认」（新增）
  - 二者样式一致（opacity-0 group-hover:opacity-100）
```

### 5.2 SetDefaultConfirmToast 视觉

```
                                  ┌──────────────────────┐
                                  │ 设为默认：开发？    │
                                  │ [取消]      [确定]  │
                                  └──────────────────────┘
                                            ▲
                                  浮在被点击 chip 下方
                                  居中对齐 chip
                                  shadow + border（与 DefaultAgentModal 卡片风格一致）
```

定位：父容器 `relative`，toast `absolute`，top 紧贴 chip 底部，left 居中。

### 5.3 视觉风格

- 沿用 `font-display`、`font-body`
- 颜色用 `gold-dim`（与现有"确认选择"按钮同色系）
- 边框 `border-ink/[0.08]`
- 圆角 `rounded-lg`（与现有 toast 一致）

---

## 6. 边界情况

| 场景 | 处理 |
|------|------|
| 切换 thread 后，localStorage 里的 agentId 不在新的 `agents` 列表 | `defaultAgentId` 仍存在（state 同步滞后于 agents 加载），但 ★ 标记只在该 agent 存在时显示。`handleSendMessage` 已用 `agents[0]` 兜底（现状） |
| 用户点 chip 切换 active（不改默认） | 与"设为默认"按钮并存，行为互不干扰 |
| toast 打开时用户点击其他 chip | 当前 toast 关闭（点确定会作用于最近一次点击的 agent）—— 简单实现：每次 `onSetDefault` 替换 pending |
| toast 打开时切换 thread | `pendingDefaultAgentId` 应该在切换 thread 时清空（避免跨 thread 误操作） |
| localStorage 写入失败 | `useDefaultAgent` 已 try/catch + console.error，额外弹一个失败 toast |
| 迷你确认 toast 5 秒未操作 | 自动关闭（与现有 toast 一致，setTimeout 清理） |

---

## 7. 实现步骤

### 7.1 新增 `SetDefaultConfirmToast.tsx`

- 接收 `agentName, onConfirm, onCancel, position`
- 渲染小型卡片，绝对定位
- 5 秒自动关闭 timer，组件 unmount 时清理

### 7.2 修改 `AgentSelector.tsx`

- 加 `defaultAgentId` 和 `onSetDefault` props
- 在现有 `⚙` 按钮**左侧**加一个 ⭐ 按钮（仅当 `agent.id !== defaultAgentId` 时显示）
- 默认 chip 的 chip 文本前加 ★ 标记（或在头像右上角加小星）

### 7.3 修改 `forum/page.tsx`

- 新增 state `pendingDefaultAgentId: string | null`
- `useDefaultAgent(currentThreadId)` 已存在，传 `defaultAgentId` 给 AgentSelector
- 实现 `handleSetDefault(id)` → 设 `pendingDefaultAgentId`
- 监听 `currentThreadId` 变化：清 `pendingDefaultAgentId`（避免跨 thread）
- 渲染 `SetDefaultConfirmToast`（当 `pendingDefaultAgentId` 非空）

### 7.4 测试

| 测试 | 期望 |
|------|------|
| `SetDefaultConfirmToast` 渲染 | 显示"将 X 设为默认？" + 两个按钮 |
| `SetDefaultConfirmToast` 点确定 | 调 `onConfirm` |
| `SetDefaultConfirmToast` 点取消 | 调 `onCancel` |
| `AgentSelector` 收到 `defaultAgentId` | 该 chip 显示 ★ |
| `AgentSelector` hover 非默认 chip | 出现 ⭐ 按钮，点击触发 `onSetDefault` |
| `HomePage` 点 chip 上的 ⭐ | `pendingDefaultAgentId` 被设置 |
| `HomePage` 在 toast 里点确定 | localStorage 写入新值、★ 标记移动、toast 关闭 |
| `HomePage` 切换 thread | `pendingDefaultAgentId` 被清空 |

---

## 8. 显式排除（YAGNI）

- ❌ 后端持久化（保持纯前端）
- ❌ 全局默认 agent（跨 thread）
- ❌ "清除默认"按钮（不选就 fallback 到 `agents[0]`，已实现）
- ❌ 新建/切换 thread 流程改动
- ❌ 右键菜单 / 长按
- ❌ 拖拽排序
- ❌ DefaultAgentModal 改动

---

## 9. 设计原则

- **激活态 vs 默认态分离**：`activeAgentId`（UI 焦点）独立于 `defaultAgentId`（消息路由），互不覆盖
- **复用现有 hook**：不新建状态管理，数据源仍是 `useDefaultAgent` + localStorage
- **最小化破坏**：现有 4 处用法（`handleSendMessage`、`handleThreadSelect`、`handleAgentSelect`、`DefaultAgentModal`）均不改动
- **视觉一致**：★ 按钮、迷你 toast 都沿用现有水墨风 / 金色 / ink 调色板
