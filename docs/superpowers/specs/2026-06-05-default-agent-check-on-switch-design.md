# 切换会话时检查默认 Agent 设计

**日期**：2026-06-05
**状态**：设计完成
**对应需求**：每次新建/切换会话，查看当前会话是否存在默认 agent，如果没有让用户选择

---

## 1. 背景与目标

### 问题
当前默认 Agent 选择功能已在新会话创建时实现，但**切换已有会话时没有检查**默认 Agent：
- 用户切换到一个之前没有设置默认 Agent 的会话
- 发送消息时系统直接使用第一个 Agent，用户无感知
- 应该像新建会话一样引导用户选择

### 目标
- 切换会话时同步检查 localStorage 中是否存有该线程的默认 Agent
- 无默认 Agent 时弹出 `DefaultAgentModal` 引导用户选择
- 有默认 Agent 时正常切换

---

## 2. 用户流程

### 2.1 切换到已有会话

```
用户点击某个已有会话
    ↓
handleThreadSelect(threadId)
    ↓
检查 localStorage[agenthub_default_agent_{threadId}]
    ├── 有值 → setCurrentThreadId + 加载消息
    └── 无值 → setPendingThreadId + setShowAgentModal(true)
              ↓
        用户选择 Agent（选择后 / 跳过）
              ↓
        handleAgentSelect(agentId) / handleAgentModalSkip()
              ↓
        setDefaultAgentId → setCurrentThreadId + 加载消息
```

### 2.2 新建会话（已有流程，保持不变）

```
用户点击"新建会话"
    ↓
handleThreadCreate()
    ↓
api.createThread() → setPendingThreadId + 弹窗
    ↓
用户选择 Agent
    ↓
handleAgentSelect → setDefaultAgentId → handleThreadSelect(pending) → 加载消息
```

---

## 3. 组件设计

### 3.1 修改文件

| 文件 | 改动内容 |
|------|----------|
| `page.tsx` | 修改 `handleThreadSelect`：同步检查 localStorage，无默认 Agent 则弹窗 |
| `page.tsx` | 修复 `handleAgentSelect`：`pendingThreadId` 路径需要调用 `handleThreadSelect` 完成切换 |
| `useDefaultAgent.ts` | 新增同步函数 `getStoredDefaultAgentId(threadId)`，供 `handleThreadSelect` 调用 |

### 3.2状态管理

```typescript
// page.tsx 现有状态（不变）
const [activeAgentId, setActiveAgentId] = useState<string | null>(null);
const [showAgentModal, setShowAgentModal] = useState(false);
const [pendingThreadId, setPendingThreadId] = useState<string | null>(null);

// useDefaultAgent 新增导出
function getStoredDefaultAgentId(threadId: string): string | null {
  // 同步读取 localStorage，无依赖 React状态
  return localStorage.getItem(getStorageKey(threadId));
}
```

---

## 4. API / 数据流

### 4.1 localStorage 结构（已存在）

```typescript
// key: `agenthub_default_agent_{threadId}`
// value: agentId (string)
"agenthub_default_agent_thread_abc123": "pm"
```

### 4.2 handleThreadSelect 改动

```typescript
const handleThreadSelect = async (threadId: string) => {
  // 新增：同步检查默认 Agent
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

### 4.3 handleAgentSelect 修复

**问题**：`pendingThreadId` 存在时，`handleThreadSelect`不会被调用，导致线程切换未完成。

```typescript
const handleAgentSelect = (agentId: string) => {
  setDefaultAgentId(agentId);
  setActiveAgentId(agentId);
  setShowAgentModal(false);

  if (pendingThreadId) {
    // 之前：直接调用 handleThreadSelect
    // 修复后：使用临时变量保存，handleThreadSelect 内部处理
    handleThreadSelect(pendingThreadId);
    setPendingThreadId(null);
  }
};
```

注意：`handleThreadSelect` 内部会设置 `setCurrentThreadId`，所以在 `pendingThreadId` 路径下不需要重复调用。

### 4.4首次加载（ThreadList mount）

**保持现有行为不变**：ThreadList 在 mount 时自动选中第一个线程，不触发弹窗检查。这是因为初始加载时 `useDefaultAgent` 的 `useEffect` 会在下一个渲染周期读取状态，而同步检查函数用于 `handleThreadSelect` 的交互式切换。

---

## 5. 边界情况

| 场景 | 处理方式 |
|------|----------|
| 切换到无默认 Agent 的旧会话 | 弹窗选择，用户选择后加载消息 |
| 切换到有默认 Agent 的会话 | 正常切换，直接加载消息 |
| 用户关闭弹窗（跳过） | 使用第一个 Agent，继续切换并加载消息 |
| 首次加载页面（自动选中第一个线程） | 不触发弹窗，现有行为 |
| 新建会话 | 现有流程不变 |
| ThreadList mount 后第一个线程 | 不触发弹窗（初始加载路径不同） |

---

## 6. 实现步骤

### 6.1 修改 `useDefaultAgent.ts`

- 新增同步函数 `getStoredDefaultAgentId(threadId: string): string | null`
- 直接读取 localStorage，不依赖 React 状态

### 6.2 修改 `page.tsx`

- `handleThreadSelect`：增加 localStorage 检查，无值则弹窗
- `handleAgentSelect`：确保 `pendingThreadId` 路径正确调用切换逻辑

### 6.3 测试验证

| 测试场景 | 预期结果 |
|----------|----------|
| 切换到无默认 Agent 的会话 | 弹窗选择，选择后正常切换 |
| 切换到有默认 Agent 的会话 |正常切换，不弹窗 |
| 新建会话 | 现有流程，选择后正常切换 |
| 首次加载页面 | 不弹窗，正常显示 |

---

## 7. 设计原则

- **同步检查**：避免竞态条件，用户点击切换时立即决定是否弹窗
- **无破坏性修改**：现有新建会话流程完全保持不变
- **最小改动**：只改 `page.tsx` 和 `useDefaultAgent.ts`