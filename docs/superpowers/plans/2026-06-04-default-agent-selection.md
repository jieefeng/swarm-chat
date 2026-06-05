# 默认 Agent 选择功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现默认 Agent 选择功能，避免消息广播给所有 Agent

**Architecture:** 前端主导方案，通过 localStorage 存储每个 thread 的默认 Agent，发送消息时传递 `agent_id` 给后端，后端已有支持无需修改

**Tech Stack:** React, Zustand, localStorage, Tailwind CSS

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `agenthub/frontend/components/agents/DefaultAgentModal.tsx` | 新建 | 默认 Agent 选择弹窗组件 |
| `agenthub/frontend/lib/hooks/useDefaultAgent.ts` | 新建 | localStorage 读写 hook |
| `agenthub/frontend/lib/api.ts` | 修改 | `sendMessage` 增加 `agent_id` 参数 |
| `agenthub/frontend/components/threads/ThreadList.tsx` | 修改 | 新建 thread 时触发弹窗 |
| `agenthub/frontend/app/page.tsx` | 修改 | 管理弹窗状态，传递默认 Agent |
| `agenthub/frontend/components/chat/MessageInput.tsx` | 修改 | 接收默认 Agent，传递给 `onSubmit` |

---

### Task 1: 创建 useDefaultAgent hook

**Files:**
- Create: `agenthub/frontend/lib/hooks/useDefaultAgent.ts`
- Test: 手动测试 localStorage 读写

- [ ] **Step 1: 创建 useDefaultAgent hook**

```typescript
// agenthub/frontend/lib/hooks/useDefaultAgent.ts
"use client";

import { useCallback, useEffect, useState } from "react";

const STORAGE_PREFIX = "agenthub_default_agent_";

function getStorageKey(threadId: string): string {
  return `${STORAGE_PREFIX}${threadId}`;
}

export function useDefaultAgent(threadId: string | null) {
  const [defaultAgentId, setDefaultAgentIdState] = useState<string | null>(null);

  // 从 localStorage 读取
  useEffect(() => {
    if (!threadId) {
      setDefaultAgentIdState(null);
      return;
    }

    try {
      const stored = localStorage.getItem(getStorageKey(threadId));
      setDefaultAgentIdState(stored || null);
    } catch (err) {
      console.error("Failed to read default agent from localStorage:", err);
      setDefaultAgentIdState(null);
    }
  }, [threadId]);

  // 设置默认 Agent
  const setDefaultAgentId = useCallback(
    (agentId: string) => {
      if (!threadId) return;

      try {
        localStorage.setItem(getStorageKey(threadId), agentId);
        setDefaultAgentIdState(agentId);
      } catch (err) {
        console.error("Failed to save default agent to localStorage:", err);
      }
    },
    [threadId]
  );

  // 清除默认 Agent
  const clearDefaultAgentId = useCallback(() => {
    if (!threadId) return;

    try {
      localStorage.removeItem(getStorageKey(threadId));
      setDefaultAgentIdState(null);
    } catch (err) {
      console.error("Failed to clear default agent from localStorage:", err);
    }
  }, [threadId]);

  return {
    defaultAgentId,
    setDefaultAgentId,
    clearDefaultAgentId,
  };
}
```

- [ ] **Step 2: 验证 hook 创建成功**

检查文件语法：`npx tsc --noEmit agenthub/frontend/lib/hooks/useDefaultAgent.ts`

- [ ] **Step 3: Commit**

```bash
git add agenthub/frontend/lib/hooks/useDefaultAgent.ts
git commit -m "feat: add useDefaultAgent hook for localStorage persistence"
```

---

### Task 2: 创建 DefaultAgentModal 组件

**Files:**
- Create: `agenthub/frontend/components/agents/DefaultAgentModal.tsx`
- Test: 手动测试弹窗显示和选择

- [ ] **Step 1: 创建 DefaultAgentModal 组件**

```typescript
// agenthub/frontend/components/agents/DefaultAgentModal.tsx
"use client";

import { useState } from "react";
import type { Agent } from "@/lib/types";

interface DefaultAgentModalProps {
  agents: Agent[];
  onSelect: (agentId: string) => void;
  onSkip?: () => void;
}

export function DefaultAgentModal({
  agents,
  onSelect,
  onSkip,
}: DefaultAgentModalProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const handleConfirm = () => {
    if (selectedId) {
      onSelect(selectedId);
    }
  };

  const handleSkip = () => {
    // 默认选择第一个 Agent
    if (agents.length > 0) {
      onSelect(agents[0]!.id);
    }
    onSkip?.();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/30 backdrop-blur-sm">
      <div className="bg-paper rounded-2xl shadow-2xl shadow-ink/10 border border-ink/[0.08] p-6 w-[480px] max-w-[90vw]">
        {/* 标题 */}
        <div className="text-center mb-6">
          <h2 className="font-display text-xl font-semibold text-ink">
            选择默认 Agent
          </h2>
          <p className="font-body text-sm text-ink/50 mt-2">
            选择一个 Agent 作为当前会话的默认对话对象
          </p>
        </div>

        {/* Agent 卡片列表 */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          {agents.map((agent) => (
            <button
              key={agent.id}
              type="button"
              onClick={() => setSelectedId(agent.id)}
              className={`flex flex-col items-center p-4 rounded-xl border-2 transition-all duration-200 ${
                selectedId === agent.id
                  ? "border-gold/50 bg-gold/5 shadow-lg shadow-gold/10"
                  : "border-ink/[0.08] hover:border-ink/[0.15] hover:bg-ink/[0.02]"
              }`}
            >
              {/* Avatar */}
              <div className="text-3xl mb-2">{agent.avatar || "🤖"}</div>

              {/* Name */}
              <div className="font-display text-sm font-medium text-ink">
                {agent.nickname || agent.name}
              </div>

              {/* Role */}
              <div className="font-body text-xs text-ink/40 mt-1">
                {agent.role}
              </div>

              {/* Element badge */}
              {agent.element && (
                <div className="mt-2 px-2 py-0.5 rounded-full bg-ink/[0.05] text-ink/30 text-[10px] font-body">
                  {agent.element}
                </div>
              )}
            </button>
          ))}
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-3">
          {onSkip && (
            <button
              type="button"
              onClick={handleSkip}
              className="flex-1 px-4 py-2.5 rounded-xl border border-ink/[0.1] text-ink/50 font-body text-sm hover:bg-ink/[0.02] transition-colors"
            >
              跳过（使用默认）
            </button>
          )}
          <button
            type="button"
            onClick={handleConfirm}
            disabled={!selectedId}
            className={`flex-1 px-4 py-2.5 rounded-xl font-display text-sm font-medium transition-all duration-200 ${
              selectedId
                ? "bg-gold/15 text-gold-dim border border-gold/25 hover:bg-gold/25 hover:shadow-lg hover:shadow-gold/10"
                : "bg-ink/[0.03] text-ink/25 border border-ink/[0.08] cursor-not-allowed"
            }`}
          >
            确认选择
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 验证组件创建成功**

检查文件语法：`npx tsc --noEmit agenthub/frontend/components/agents/DefaultAgentModal.tsx`

- [ ] **Step 3: Commit**

```bash
git add agenthub/frontend/components/agents/DefaultAgentModal.tsx
git commit -m "feat: add DefaultAgentModal component"
```

---

### Task 3: 修改 api.ts 支持 agent_id 参数

**Files:**
- Modify: `agenthub/frontend/lib/api.ts:18-33`

- [ ] **Step 1: 修改 sendMessage 方法**

在 `api.ts` 的 `sendMessage` 方法中添加 `agentId` 参数：

```typescript
async sendMessage(content: string, agentId?: string): Promise<SendMessageResponse> {
  const res = await fetch(`${API_BASE}/api/messages`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      content,
      sender: "user",
      sender_name: "用户",
      agent_id: agentId || undefined,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.message || `HTTP ${res.status}`);
  }
  return res.json();
},
```

- [ ] **Step 2: 验证修改成功**

检查文件语法：`npx tsc --noEmit agenthub/frontend/lib/api.ts`

- [ ] **Step 3: Commit**

```bash
git add agenthub/frontend/lib/api.ts
git commit -m "feat: add agent_id parameter to sendMessage API"
```

---

### Task 4: 修改 ThreadList 支持新建 thread 时触发弹窗

**Files:**
- Modify: `agenthub/frontend/components/threads/ThreadList.tsx`

- [ ] **Step 1: 修改 ThreadList 组件**

添加 `onThreadCreate` 回调，让父组件控制新建 thread 的逻辑：

```typescript
"use client";

import { useEffect } from "react";
import { api } from "@/lib/api";
import { useThreadStore } from "@/lib/stores/threadStore";
import { NewThreadButton } from "./NewThreadButton";
import { ThreadItem } from "./ThreadItem";

interface ThreadListProps {
  onThreadSelect: (threadId: string) => void;
  onThreadCreate?: () => void;  // 新增：新建 thread 回调
}

export function ThreadList({ onThreadSelect, onThreadCreate }: ThreadListProps) {
  const {
    threads,
    currentThreadId,
    isLoading,
    setThreads,
    setCurrentThreadId,
    removeThread,
    setLoading,
  } = useThreadStore();

  useEffect(() => {
    loadThreads();
  }, []);

  const loadThreads = async () => {
    setLoading(true);
    try {
      const data = await api.getThreads();
      setThreads(data.threads || []);
      if (!currentThreadId && data.threads && data.threads.length > 0) {
        setCurrentThreadId(data.threads[0]!.id);
        onThreadSelect(data.threads[0]!.id);
      }
    } catch (err) {
      console.error("Failed to load threads:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateThread = async () => {
    // 如果有外部回调，使用外部逻辑
    if (onThreadCreate) {
      onThreadCreate();
      return;
    }

    // 否则使用原有逻辑
    try {
      const newThread = await api.createThread();
      setThreads([newThread, ...threads]);
      setCurrentThreadId(newThread.id);
      onThreadSelect(newThread.id);
    } catch (err) {
      console.error("Failed to create thread:", err);
    }
  };

  const handleDeleteThread = async (threadId: string) => {
    if (!confirm("确定删除这个会话吗？")) return;
    try {
      await api.deleteThread(threadId);
      removeThread(threadId);
      if (currentThreadId === threadId && threads.length > 1) {
        const nextThread = threads.find((t) => t.id !== threadId);
        if (nextThread) {
          setCurrentThreadId(nextThread.id);
          onThreadSelect(nextThread.id);
        }
      }
    } catch (err) {
      console.error("Failed to delete thread:", err);
    }
  };

  const handleThreadClick = (threadId: string) => {
    setCurrentThreadId(threadId);
    onThreadSelect(threadId);
  };

  return (
    <div className="w-64 flex flex-col border-r border-ink/[0.08] bg-paper-dark/50">
      {/* Header */}
      <div className="p-4 border-b border-ink/[0.08]">
        <h2 className="font-display text-sm font-semibold text-ink/80 mb-3 tracking-wide">
          会话列表
        </h2>
        <NewThreadButton onClick={handleCreateThread} disabled={isLoading} />
      </div>

      {/* Thread List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {isLoading ? (
          <div className="text-center text-xs text-ink/30 py-6 font-body">
            加载中…
          </div>
        ) : threads.length === 0 ? (
          <div className="text-center text-xs text-ink/25 py-6 font-body">
            暂无会话，点击上方按钮创建
          </div>
        ) : (
          threads.map((thread) => (
            <ThreadItem
              key={thread.id}
              thread={thread}
              isActive={thread.id === currentThreadId}
              onClick={() => handleThreadClick(thread.id)}
              onDelete={() => handleDeleteThread(thread.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 验证修改成功**

检查文件语法：`npx tsc --noEmit agenthub/frontend/components/threads/ThreadList.tsx`

- [ ] **Step 3: Commit**

```bash
git add agenthub/frontend/components/threads/ThreadList.tsx
git commit -m "feat: add onThreadCreate callback to ThreadList"
```

---

### Task 5: 修改 page.tsx 集成弹窗和默认 Agent 逻辑

**Files:**
- Modify: `agenthub/frontend/app/page.tsx`

- [ ] **Step 1: 修改 page.tsx**

集成 DefaultAgentModal 和 useDefaultAgent：

```typescript
"use client";

import { useEffect, useState } from "react";
import { DefaultAgentModal } from "@/components/agents/DefaultAgentModal";
import { AgentSelector } from "@/components/agents/AgentSelector";
import { MessageInput } from "@/components/chat/MessageInput";
import { MessageList } from "@/components/chat/MessageList";
import { ModelEditor } from "@/components/chat/ModelEditor";
import { ThreadList } from "@/components/threads/ThreadList";
import { api } from "@/lib/api";
import { useChatStream } from "@/lib/hooks/useChatStream";
import { useDefaultAgent } from "@/lib/hooks/useDefaultAgent";
import { useAgentStore } from "@/lib/stores/agentStore";
import { useMessageStore } from "@/lib/stores/messageStore";
import { useThreadStore } from "@/lib/stores/threadStore";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:7005";

export default function HomePage() {
  const [activeAgentId, setActiveAgentId] = useState<string | null>(null);
  const [showAgentModal, setShowAgentModal] = useState(false);
  const [pendingThreadId, setPendingThreadId] = useState<string | null>(null);

  const agents = useAgentStore((s) => s.agents);
  const setAgents = useAgentStore((s) => s.setAgents);
  const messages = useMessageStore((s) => s.messages);
  const currentThreadId = useThreadStore((s) => s.currentThreadId);

  const { defaultAgentId, setDefaultAgentId } = useDefaultAgent(currentThreadId);

  const { sendMessage, connectionState, lastError } = useChatStream({
    agentId: null,
    baseUrl: API_BASE,
  });

  const handleThreadSelect = async (threadId: string) => {
    useThreadStore.getState().setCurrentThreadId(threadId);
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

  const handleThreadCreate = async () => {
    try {
      const newThread = await api.createThread();
      useThreadStore.getState().addThread(newThread);
      useThreadStore.getState().setCurrentThreadId(newThread.id);
      setPendingThreadId(newThread.id);
      setShowAgentModal(true);
    } catch (err) {
      console.error("Failed to create thread:", err);
    }
  };

  const handleAgentSelect = (agentId: string) => {
    setDefaultAgentId(agentId);
    setActiveAgentId(agentId);
    setShowAgentModal(false);

    if (pendingThreadId) {
      handleThreadSelect(pendingThreadId);
      setPendingThreadId(null);
    }
  };

  const handleAgentModalSkip = () => {
    setShowAgentModal(false);

    if (pendingThreadId) {
      handleThreadSelect(pendingThreadId);
      setPendingThreadId(null);
    }
  };

  const handleSendMessage = (content: string) => {
    const mentionMatch = content.match(/@(\w+)/);
    if (mentionMatch?.[1]) {
      setActiveAgentId(mentionMatch[1]);
      sendMessage(content);
    } else {
      // 使用默认 Agent
      const agentId = defaultAgentId || (agents.length > 0 ? agents[0]!.id : undefined);
      sendMessage(content, agentId);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      try {
        const [msgsRes, agentsRes] = await Promise.all([
          api.getMessages(),
          api.getAgents(),
        ]);
        useMessageStore.getState().reset();
        msgsRes.messages?.forEach((m) => {
          useMessageStore.getState().addMessage(m);
        });
        setAgents(agentsRes.agents || []);
      } catch (err) {
        console.error("Failed to load data:", err);
      }
    };
    loadData();
  }, [setAgents]);

  const connectionLabel = {
    connected: {
      dot: "bg-emerald-400",
      text: "已连接",
      glow: "shadow-emerald-400/40",
    },
    connecting: {
      dot: "bg-amber-400",
      text: "连接中…",
      glow: "shadow-amber-400/40",
    },
    reconnecting: {
      dot: "bg-amber-400",
      text: "重连中…",
      glow: "shadow-amber-400/40",
    },
    error: { dot: "bg-red-400", text: "连接失败", glow: "shadow-red-400/40" },
    idle: { dot: "bg-gray-500", text: "空闲", glow: "" },
  }[connectionState] ?? { dot: "bg-gray-500", text: "空闲", glow: "" };

  return (
    <div className="flex flex-col h-screen">
      {/* ── 顶部栏 ── */}
      <header className="flex justify-between items-center px-6 py-3 border-b border-ink/[0.08] bg-paper/80 backdrop-blur-sm">
        <div className="flex items-center gap-5">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="relative">
              <span className="text-2xl leading-none">🐉</span>
              <div className="absolute -inset-1 bg-gold/10 rounded-full blur-md -z-10" />
            </div>
            <div>
              <h1 className="font-display text-lg font-semibold text-ink tracking-wide">
                AgentHub
              </h1>
              <p className="font-display text-[10px] text-gold-dim/60 tracking-[0.3em] -mt-0.5">
                五行神兽
              </p>
            </div>
          </div>

          {/* 模型编辑器 */}
          {agents.length > 0 && (
            <div className="flex items-center gap-2 pl-5 border-l border-ink/[0.08]">
              <span className="text-xs text-ink/40 font-body">模型</span>
              <ModelEditor
                agentId={
                  activeAgentId && agents.some((a) => a.id === activeAgentId)
                    ? activeAgentId
                    : agents[0]!.id
                }
                agentName={
                  (activeAgentId &&
                    agents.find((a) => a.id === activeAgentId)?.name) ||
                  agents[0]!.name
                }
              />
            </div>
          )}
        </div>

        {/* 连接状态 */}
        <div className="flex items-center gap-2">
          <div
            className={`w-1.5 h-1.5 rounded-full ${connectionLabel.dot} shadow-sm ${connectionLabel.glow}`}
          />
          <span className="text-xs text-ink/50 font-body">
            {connectionLabel.text}
          </span>
        </div>
      </header>

      {/* ── 主内容区 ── */}
      <div className="flex flex-1 overflow-hidden">
        {/* 会话列表 */}
        <ThreadList
          onThreadSelect={handleThreadSelect}
          onThreadCreate={handleThreadCreate}
        />

        {/* 聊天区域 */}
        <div className="flex-1 flex flex-col bg-paper relative">
          {/* 微妙的光晕背景 */}
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-gold/[0.04] rounded-full blur-[100px]" />
          </div>

          <div className="relative flex-shrink-0 border-b border-ink/[0.06]">
            <AgentSelector
              agents={agents}
              activeAgentId={activeAgentId}
              onAgentSelect={setActiveAgentId}
            />
          </div>
          <div className="relative flex-1 flex flex-col">
            <MessageList messages={messages} agentId={null} />
            <MessageInput
              onSubmit={handleSendMessage}
              disabled={connectionState === "connecting"}
              mentionCandidates={agents.map((a) => ({
                id: a.id,
                label: a.nickname || a.name,
                avatar: a.avatar,
                beast: a.beast,
                element: a.element,
                color: a.color,
              }))}
            />
          </div>
        </div>
      </div>

      {/* 默认 Agent 选择弹窗 */}
      {showAgentModal && (
        <DefaultAgentModal
          agents={agents}
          onSelect={handleAgentSelect}
          onSkip={handleAgentModalSkip}
        />
      )}

      {/* 错误提示 */}
      {lastError && (
        <div className="absolute bottom-20 left-1/2 -translate-x-1/2 bg-danger/90 text-white px-5 py-2.5 rounded-lg shadow-lg shadow-danger/20 backdrop-blur-sm border border-danger/30 font-body text-sm animate-fade-in-up">
          {lastError}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: 验证修改成功**

检查文件语法：`npx tsc --noEmit agenthub/frontend/app/page.tsx`

- [ ] **Step 3: Commit**

```bash
git add agenthub/frontend/app/page.tsx
git commit -m "feat: integrate DefaultAgentModal and useDefaultAgent in page"
```

---

### Task 6: 修改 MessageInput 支持传递默认 Agent

**Files:**
- Modify: `agenthub/frontend/components/chat/MessageInput.tsx`

- [ ] **Step 1: 修改 MessageInput 组件**

添加 `defaultAgentId` prop：

```typescript
"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import {
  type SendMessageInput,
  sendMessageSchema,
} from "@/lib/schemas/message";
import type { MentionCandidate } from "@/lib/types";
import { MentionDropdown } from "./MentionDropdown";

interface MessageInputProps {
  onSubmit: (content: string, agentId?: string) => void;  // 修改：添加 agentId 参数
  disabled: boolean;
  mentionCandidates: MentionCandidate[];
  defaultAgentId?: string | null;  // 新增：默认 Agent ID
}

interface MentionState {
  isActive: boolean;
  filterText: string;
  startIndex: number;
  cursorPos: number;
}

export function MessageInput({
  onSubmit,
  disabled,
  mentionCandidates,
  defaultAgentId,
}: MessageInputProps) {
  const [input, setInput] = useState("");
  const [mentionState, setMentionState] = useState<MentionState>({
    isActive: false,
    filterText: "",
    startIndex: -1,
    cursorPos: 0,
  });
  const inputRef = useRef<HTMLInputElement>(null);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
    reset,
  } = useForm<SendMessageInput>({
    resolver: zodResolver(sendMessageSchema),
  });

  const filteredAgents = mentionState.isActive
    ? mentionCandidates.filter((agent) =>
        agent.label
          .toLowerCase()
          .includes(mentionState.filterText.toLowerCase()),
      )
    : [];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const cursorPos = e.target.selectionStart ?? 0;

    setInput(value);
    setValue("content", value, { shouldValidate: false });

    const textBeforeCursor = value.slice(0, cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf("@");

    if (lastAtIndex !== -1) {
      const textAfterAt = textBeforeCursor.slice(lastAtIndex + 1);
      if (!textAfterAt.includes(" ")) {
        setMentionState({
          isActive: true,
          filterText: textAfterAt,
          startIndex: lastAtIndex,
          cursorPos: cursorPos,
        });
        return;
      }
    }

    setMentionState({
      isActive: false,
      filterText: "",
      startIndex: -1,
      cursorPos: 0,
    });
  };

  const handleSelect = (candidate: MentionCandidate) => {
    if (mentionState.startIndex === -1) return;

    const beforeMention = input.slice(0, mentionState.startIndex);
    const afterMention = input.slice(mentionState.cursorPos);
    const mentionInsert = `@${candidate.label} `;

    const newValue = beforeMention + mentionInsert + afterMention;
    setInput(newValue);
    setValue("content", newValue, { shouldValidate: false });
    setMentionState({
      isActive: false,
      filterText: "",
      startIndex: -1,
      cursorPos: 0,
    });

    setTimeout(() => {
      inputRef.current?.focus();
      const newCursorPos = beforeMention.length + mentionInsert.length;
      inputRef.current?.setSelectionRange(newCursorPos, newCursorPos);
    }, 0);
  };

  const onFormSubmit = (data: SendMessageInput) => {
    // 检查是否有@指令
    const mentionMatch = data.content.match(/@(\w+)/);
    if (mentionMatch?.[1]) {
      onSubmit(data.content);
    } else {
      onSubmit(data.content, defaultAgentId || undefined);
    }
    setInput("");
    reset();
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (mentionState.isActive && inputRef.current) {
        const target = e.target as HTMLElement;
        if (
          !inputRef.current.contains(target) &&
          !target.closest(".mention-dropdown")
        ) {
          setMentionState({
            isActive: false,
            filterText: "",
            startIndex: -1,
            cursorPos: 0,
          });
        }
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [mentionState.isActive]);

  return (
    <form
      onSubmit={handleSubmit(onFormSubmit)}
      className="flex p-4 border-t border-ink/[0.06] bg-paper/60 backdrop-blur-sm"
    >
      <div className="flex-1 relative">
        <input
          {...register("content")}
          ref={inputRef}
          type="text"
          value={input}
          onChange={handleChange}
          placeholder={disabled ? "等待回复…" : "输入消息，@某人可定向发送"}
          disabled={disabled}
          className="w-full px-5 py-3 bg-white border border-ink/[0.1] rounded-xl text-ink placeholder:text-ink/30 focus:outline-none focus:border-gold/40 focus:bg-white transition-all duration-200 font-body text-sm"
        />
        {errors.content && (
          <p className="text-danger text-xs mt-1.5 font-body">
            {errors.content.message}
          </p>
        )}
        {mentionState.isActive && (
          <div className="mention-dropdown absolute bottom-full mb-2 w-full">
            <MentionDropdown
              candidates={filteredAgents}
              onSelect={handleSelect}
            />
          </div>
        )}
      </div>
      <button
        type="submit"
        disabled={disabled || !input.trim()}
        className={`ml-3 px-6 py-3 rounded-xl font-display font-medium text-sm transition-all duration-200 ${
          input.trim() && !disabled
            ? "bg-gold/15 text-gold-dim border border-gold/25 hover:bg-gold/25 hover:shadow-lg hover:shadow-gold/10"
            : "bg-ink/[0.03] text-ink/25 border border-ink/[0.08] cursor-not-allowed"
        }`}
      >
        发送
      </button>
    </form>
  );
}
```

- [ ] **Step 2: 验证修改成功**

检查文件语法：`npx tsc --noEmit agenthub/frontend/components/chat/MessageInput.tsx`

- [ ] **Step 3: Commit**

```bash
git add agenthub/frontend/components/chat/MessageInput.tsx
git commit -m "feat: add defaultAgentId prop to MessageInput"
```

---

### Task 7: 修改 useChatStream 支持 agent_id 参数

**Files:**
- Modify: `agenthub/frontend/lib/hooks/useChatStream.ts`

- [ ] **Step 1: 修改 useChatStream hook**

修改 `sendMessage` 方法支持 `agentId` 参数：

```typescript
// 找到 sendMessage 函数，修改为：
const sendMessage = async (content: string, agentId?: string) => {
  // ... 现有代码 ...
  await api.sendMessage(content, agentId);
  // ... 现有代码 ...
};
```

- [ ] **Step 2: 验证修改成功**

检查文件语法：`npx tsc --noEmit agenthub/frontend/lib/hooks/useChatStream.ts`

- [ ] **Step 3: Commit**

```bash
git add agenthub/frontend/lib/hooks/useChatStream.ts
git commit -m "feat: add agent_id support to useChatStream"
```

---

### Task 8: 测试完整功能

- [ ] **Step 1: 启动前端开发服务器**

```bash
cd agenthub/frontend && npm run dev
```

- [ ] **Step 2: 测试新建 thread 流程**

1. 点击"新建会话"按钮
2. 验证弹窗显示所有 Agent
3. 选择一个 Agent
4. 验证弹窗关闭，进入新会话

- [ ] **Step 3: 测试消息发送**

1. 在新会话中发送消息（不使用@）
2. 验证消息只发给选中的默认 Agent
3. 使用@指令发送消息
4. 验证消息发给@指定的 Agent

- [ ] **Step 4: 测试 thread 切换**

1. 切换到其他会话
2. 验证每个会话有独立的默认 Agent

- [ ] **Step 5: Commit 测试结果**

```bash
git add -A
git commit -m "test: verify default agent selection feature"
```

---

## 完成

所有任务完成后，运行最终检查：

```bash
cd agenthub/frontend && npm run check
```

确保没有 TypeScript 错误和 lint 警告。
