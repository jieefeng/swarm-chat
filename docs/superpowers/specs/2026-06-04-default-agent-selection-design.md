# 默认 Agent 选择功能设计

**日期**：2026-06-04
**状态**：设计完成
**方案**：前端主导

---

## 1. 背景与目标

### 问题
当前系统中，用户不使用@指令发送消息时，消息会广播给所有 Agent（苍龙、玄冥、啸风、炎翎、瑞麟），导致：
- 所有 Agent 同时响应，造成混乱
- 用户无法聚焦于特定 Agent 的对话
- 资源浪费（多个 LLM 同时调用）

### 目标
- 每个会话（thread）支持设置默认 Agent
- 无@指令时，消息只发给默认 Agent
- 有@指令时，@覆盖默认 Agent
- 首次进入新会话时引导用户选择

---

## 2. 用户流程

```
用户打开首页
    ↓
点击"新建会话"或选择已有会话
    ↓
如果是新建会话 → 弹窗选择默认 Agent
    ↓
选择 Agent → 保存到 localStorage (key: `agenthub_default_agent_{threadId}`)
    ↓
进入会话，发送消息
    ↓
前端从 localStorage 读取默认 Agent，传给后端 agent_id
    ↓
后端使用前端传的 agent_id，跳过广播逻辑
```

### 关键点
- 每个 thread 独立的默认 Agent
- 选择后立即生效，无需刷新
- @指令仍然可以覆盖默认 Agent

---

## 3. 组件设计

### 3.1 新建组件：`DefaultAgentModal.tsx`

```
┌─────────────────────────────────────┐
│         选择默认 Agent              │
│                                     │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │
│  │ 🐉  │ │ 🐢  │ │ 🐯  │ │ 🦅  │   │
│  │苍龙 │ │玄冥 │ │啸风 │ │炎翎 │   │
│  │ PM  │ │架构 │ │开发 │ │ QA  │   │
│  └─────┘ └─────┘ └─────┘ └─────┘   │
│                                     │
│           [ 确认选择 ]               │
└─────────────────────────────────────┘
```

**Props**：
```typescript
interface DefaultAgentModalProps {
  agents: Agent[];                    // 可选 Agent 列表
  onSelect: (agentId: string) => void; // 选择回调
  onSkip?: () => void;                // 跳过（使用默认）
}
```

### 3.2 修改现有组件

| 组件 | 修改内容 |
|------|----------|
| `ThreadList.tsx` | 新建 thread 时触发弹窗 |
| `page.tsx` | 管理弹窗状态 |
| `api.ts` | `sendMessage` 增加 `agent_id` 参数 |

---

## 4. 状态管理

### 4.1 localStorage 结构

```typescript
// key: `agenthub_default_agent_{threadId}`
// value: agentId (string)
"agenthub_default_agent_thread_abc123": "pm"
```

### 4.2 新增 hook：`useDefaultAgent.ts`

```typescript
export function useDefaultAgent(threadId: string) {
  // 从 localStorage 读取默认 Agent
  // 提供 setDefaultAgent 方法
  // 提供 clearDefaultAgent 方法
}
```

### 4.3 修改 store：`threadStore.ts`

```typescript
interface ThreadState {
  // 现有字段...
  defaultAgentId: string | null;  // 新增：当前 thread 的默认 Agent
  setDefaultAgentId: (id: string) => void;
}
```

### 4.4 消息发送流程

```typescript
const handleSendMessage = (content: string) => {
  // 1. 检查是否有@指令
  const mentionMatch = content.match(/@(\w+)/);
  if (mentionMatch?.[1]) {
    // 有@，使用@指定的 Agent
    sendMessage(content);
  } else {
    // 无@，使用默认 Agent
    const defaultAgentId = getDefaultAgent(threadId);
    sendMessage(content, defaultAgentId);
  }
};
```

---

## 5. API 调用

### 5.1 修改 `api.ts`

```typescript
async sendMessage(content: string, agentId?: string): Promise<SendMessageResponse> {
  const res = await fetch(`${API_BASE}/api/messages`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      content,
      sender: "user",
      sender_name: "用户",
      agent_id: agentId || undefined,  // 新增：传递默认 Agent
    }),
  });
  // ...
}
```

### 5.2 后端已有支持（无需修改）

```python
# messages.py:182-183
if req.agent_id:
    targets = [req.agent_id]
```

### 5.3 SSE 事件

无需修改，后端会正常广播 Agent 响应。

---

## 6. 边界情况

| 场景 | 处理方式 |
|------|----------|
| 首次访问，无 localStorage | 弹窗选择默认 Agent |
| localStorage 有值，但 Agent 被删除 | 弹窗重新选择 |
| 切换 thread | 从 localStorage 读取该 thread 的默认 Agent |
| 用户手动@某人 | @指令覆盖默认 Agent |
| 用户清空浏览器数据 | 下次访问时重新弹窗选择 |
| 多个浏览器标签页 | 各自独立，localStorage 共享 |
| 弹窗关闭（点击遮罩/X） | 使用第一个 Agent 作为默认 |

### 错误处理

- localStorage 读取失败：降级为广播模式（当前行为）
- Agent ID 无效：弹窗重新选择

---

## 7. 实现步骤

### 7.1 前端改动

1. **新建 `DefaultAgentModal.tsx`**
   - Agent 卡片选择界面
   - 确认/跳过按钮

2. **新建 `useDefaultAgent.ts` hook**
   - localStorage 读写
   - Agent 有效性验证

3. **修改 `ThreadList.tsx`**
   - 新建 thread 时触发弹窗

4. **修改 `page.tsx`**
   - 管理弹窗状态
   - 传递默认 Agent 给 MessageInput

5. **修改 `api.ts`**
   - `sendMessage` 增加 `agent_id` 参数

6. **修改 `MessageInput.tsx`**
   - 接收默认 Agent，传递给 `onSubmit`

### 7.2 后端改动

**无需修改**，已有 `agent_id` 参数支持。

---

## 8. 测试用例

| 测试场景 | 预期结果 |
|----------|----------|
| 首次新建 thread | 弹窗选择默认 Agent |
| 选择默认 Agent 后发送消息 | 消息只发给选中的 Agent |
| 使用@指令 | 消息发给@指定的 Agent |
| 切换 thread | 读取该 thread 的默认 Agent |
| localStorage 被清空 | 重新弹窗选择 |
| Agent 被删除 | 重新弹窗选择 |

---

## 9. 未来扩展

- **跨设备同步**：后端 thread 表增加 `default_agent_id` 字段
- **批量设置**：支持为所有 thread 设置默认 Agent
- **智能推荐**：根据消息内容自动推荐 Agent
