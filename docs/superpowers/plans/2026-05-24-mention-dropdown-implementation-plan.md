# @Agent Mention 下拉菜单实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在消息输入框中实现 @mention 自动完成功能，用户输入 `@` 时显示 Agent 列表供选择

**Architecture:** 使用 React hooks (useState, useRef, useEffect) 实现本地状态管理，通过 onChange 监听输入框变化，检测 `@` 触发下拉菜单，通过 onClick/onKeyDown 处理选项选择和插入

**Tech Stack:** React (Next.js), TypeScript, Tailwind CSS

---

## 文件结构

```
agenthub/frontend/components/chat/
├── MentionDropdown.tsx    # 新增：下拉菜单组件
└── MessageInput.tsx      # 修改：添加 mention 逻辑
```

---

## Task 1: 创建 MentionDropdown 组件

**Files:**
- Create: `agenthub/frontend/components/chat/MentionDropdown.tsx`

**Agent 数据类型 (from types.ts):**
```typescript
interface Agent {
  id: string;    // "pm"
  name: string;   // "产品经理"
  role: string;  // "产品经理（PM）"
}
```

- [ ] **Step 1: 创建 MentionDropdown.tsx 文件**

```tsx
'use client';

import { Agent } from '@/lib/types';

interface MentionDropdownProps {
  options: Agent[];
  onSelect: (agent: Agent) => void;
  position?: { top: number; left: number };
}

export function MentionDropdown({ options, onSelect }: MentionDropdownProps) {
  if (options.length === 0) {
    return (
      <div className="absolute bottom-full mb-2 w-full bg-white rounded-lg shadow-lg border border-gray-200 p-4 text-center text-gray-500 text-sm">
        无匹配Agent
      </div>
    );
  }

  return (
    <div className="absolute bottom-full mb-2 w-full bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden">
      {options.slice(0, 5).map((agent) => (
        <button
          key={agent.id}
          onClick={() => onSelect(agent)}
          className="w-full px-4 py-3 text-left hover:bg-blue-50 flex items-center gap-3 transition-colors"
        >
          <div className="flex-1">
            <div className="font-medium text-gray-800">{agent.name}</div>
            <div className="text-xs text-gray-500">{agent.role}</div>
          </div>
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: 验证文件创建成功**

Run: `ls -la agenthub/frontend/components/chat/MentionDropdown.tsx`
Expected: 文件存在

- [ ] **Step 3: 提交**
```bash
git add agenthub/frontend/components/chat/MentionDropdown.tsx
git commit -m "feat(frontend): add MentionDropdown component"
```

---

## Task 2: 修改 MessageInput.tsx 添加 mention 逻辑

**Files:**
- Modify: `agenthub/frontend/components/chat/MessageInput.tsx`

**需要添加的逻辑:**
1. 监听 input onChange，检测 `@` 字符
2. 解析 `@` 后的过滤文本
3. 根据过滤文本筛选 Agent 列表
4. 显示/隐藏 MentionDropdown
5. 处理选项选中，插入 `@产品经理 ` 到光标位置
6. 处理 ESC 和点击外部关闭

- [ ] **Step 1: 读取当前 MessageInput.tsx 内容**

```typescript
'use client';

import { useState } from 'react';

interface MessageInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
}

export function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;
    onSend(input.trim());
    setInput('');
  };

  return (
    <form onSubmit={handleSubmit} className="flex p-4 border-t bg-white">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder={disabled ? "等待回复..." : "输入消息，@某人可定向发送"}
        disabled={disabled}
        className="flex-1 px-4 py-3 rounded-full border border-gray-300 focus:outline-none focus:border-blue-500"
      />
      <button
        type="submit"
        disabled={!input.trim() || disabled}
        className={`ml-3 px-6 py-3 rounded-full font-medium ${
          input.trim() && !disabled
            ? 'bg-blue-500 text-white hover:bg-blue-600'
            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
        }`}
      >
        发送
      </button>
    </form>
  );
}
```

- [ ] **Step 2: 写入完整的 MessageInput.tsx 实现**

```typescript
'use client';

import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { Agent } from '@/lib/types';
import { MentionDropdown } from './MentionDropdown';

interface MessageInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  agents?: Agent[];
}

interface MentionState {
  isActive: boolean;
  filterText: string;
  startIndex: number;
}

export function MessageInput({ onSend, disabled, agents = [] }: MessageInputProps) {
  const [input, setInput] = useState('');
  const [mentionState, setMentionState] = useState<MentionState>({
    isActive: false,
    filterText: '',
    startIndex: -1,
  });
  const inputRef = useRef<HTMLInputElement>(null);

  // 过滤 Agent 列表
  const filteredAgents = mentionState.isActive
    ? agents.filter((agent) =>
        agent.name.includes(mentionState.filterText) ||
        agent.role.includes(mentionState.filterText)
      )
    : [];

  // 处理输入变化
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const cursorPos = e.target.selectionStart ?? 0;

    setInput(value);

    // 查找 @ 的位置
    const textBeforeCursor = value.slice(0, cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf('@');

    if (lastAtIndex !== -1) {
      // 检查 @ 后面是否有空格（如果有则为无效 mention）
      const textAfterAt = textBeforeCursor.slice(lastAtIndex + 1);
      if (!textAfterAt.includes(' ')) {
        // 有效的 mention 触发
        setMentionState({
          isActive: true,
          filterText: textAfterAt,
          startIndex: lastAtIndex,
        });
        return;
      }
    }

    setMentionState({
      isActive: false,
      filterText: '',
      startIndex: -1,
    });
  };

  // 处理选项选中
  const handleSelect = (agent: Agent) => {
    if (mentionState.startIndex === -1) return;

    const beforeMention = input.slice(0, mentionState.startIndex);
    const afterMention = input.slice(inputRef.current?.selectionStart ?? mentionState.startIndex);
    const mentionInsert = `@${agent.name} `;

    setInput(beforeMention + mentionInsert + afterMention);
    setMentionState({
      isActive: false,
      filterText: '',
      startIndex: -1,
    });

    // 聚焦回输入框
    setTimeout(() => {
      inputRef.current?.focus();
      const newCursorPos = beforeMention.length + mentionInsert.length;
      inputRef.current?.setSelectionRange(newCursorPos, newCursorPos);
    }, 0);
  };

  // 处理键盘事件
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') {
      setMentionState({
        isActive: false,
        filterText: '',
        startIndex: -1,
      });
      e.preventDefault();
    }
  };

  // 点击外部关闭
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (mentionState.isActive && inputRef.current) {
        const target = e.target as HTMLElement;
        if (!inputRef.current.contains(target) && !target.closest('.mention-dropdown')) {
          setMentionState({
            isActive: false,
            filterText: '',
            startIndex: -1,
          });
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [mentionState.isActive]);

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      if (!input.trim() || disabled) return;
      onSend(input.trim());
      setInput('');
    }} className="flex p-4 border-t bg-white">
      <div className="flex-1 relative">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? "等待回复..." : "输入消息，@某人可定向发送"}
          disabled={disabled}
          className="w-full px-4 py-3 rounded-full border border-gray-300 focus:outline-none focus:border-blue-500"
        />
        {mentionState.isActive && (
          <div className="mention-dropdown absolute bottom-full mb-2 w-full">
            <MentionDropdown
              options={filteredAgents}
              onSelect={handleSelect}
            />
          </div>
        )}
      </div>
      <button
        type="submit"
        disabled={!input.trim() || disabled}
        className={`ml-3 px-6 py-3 rounded-full font-medium ${
          input.trim() && !disabled
            ? 'bg-blue-500 text-white hover:bg-blue-600'
            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
        }`}
      >
        发送
      </button>
    </form>
  );
}
```

- [ ] **Step 3: 运行 TypeScript 检查**

Run: `cd agenthub/frontend && npx tsc --noEmit 2>&1 | head -50`
Expected: 无错误（或仅已有错误）

- [ ] **Step 4: 提交**
```bash
git add agenthub/frontend/components/chat/MessageInput.tsx
git commit -m "feat(frontend): add @mention autocomplete to MessageInput"
```

---

## Task 3: 修改 page.tsx 传递 agents 数据给 MessageInput

**Files:**
- Modify: `agenthub/frontend/app/page.tsx`

- [ ] **Step 1: 读取 page.tsx 确认当前结构**

从之前读取的内容，MessageInput 在第71行调用，缺少 agents prop。

- [ ] **Step 2: 修改 MessageInput 调用，添加 agents prop**

找到第71行:
```tsx
<MessageInput onSend={handleSend} disabled={loading} />
```

改为:
```tsx
<MessageInput onSend={handleSend} disabled={loading} agents={agents} />
```

- [ ] **Step 3: 提交**
```bash
git add agenthub/frontend/app/page.tsx
git commit -m "feat(frontend): pass agents to MessageInput for @mention"
```

---

## 验证

1. 启动前端开发服务器: `cd agenthub/frontend && npm run dev`
2. 在输入框输入 `@`
3. 应显示 Agent 下拉列表（pm 产品经理、architect 架构师）
4. 输入过滤文本如 `@产品` 应过滤显示
5. 点击选项应插入 `@产品经理 ` 到输入框
6. 按 ESC 应关闭下拉菜单