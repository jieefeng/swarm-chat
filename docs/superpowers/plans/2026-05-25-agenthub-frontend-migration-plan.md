# AgentHub Frontend Migration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 AgentHub 前端从 Next.js 14 (Pages Router) 迁移到 Next.js 15 (App Router)，技术栈升级为 Tailwind v4 + Zustand + Biome + Zod + React Hook Form

**Architecture:** 功能驱动迁移，Phase 0 基础设施先行确保规范约束，后续 Phase 逐步迁移静态页面 → SSE 传输层 → 聊天 UI → 表单增强

**Tech Stack:** Next.js 15, Tailwind CSS v4, Zustand, Biome 2.1, Zod, React Hook Form, react-markdown

---

## 文件结构概览

```
agenthub/frontend/
├── app/                          # 新 App Router 目录
│   ├── layout.tsx               # 根布局 (RSC)
│   ├── page.tsx                 # 主聊天页面 (RSC)
│   ├── globals.css              # Tailwind v4 + @theme
│   └── agents/
│       └── page.tsx            # Agent 列表页 (RSC)
├── components/                   # Client Components ('use client')
│   ├── agents/
│   │   └── AgentList.tsx
│   └── chat/
│       ├── MessageList.tsx
│       ├── MessageBubble.tsx
│       ├── MessageInput.tsx
│       └── MentionDropdown.tsx
├── lib/
│   ├── api.ts                  # HTTP 请求
│   ├── sse.ts                  # SSE 连接管理
│   ├── types.ts                # 类型定义（含 MentionCandidate）
│   ├── stores/
│   │   ├── messageStore.ts
│   │   ├── agentStore.ts
│   │   └── uiStore.ts
│   ├── hooks/
│   │   └── useChatStream.ts
│   └── schemas/
│       └── message.ts          # Zod schemas
├── biome.json                  # Biome 配置
├── postcss.config.mjs          # @tailwindcss/postcss
└── package.json               # 更新依赖
```

---

## Phase 0: 基础设施准备

**目标:** 所有后续 Phase 生成的代码自动符合规范

**质量门禁:** `npx @biomejs/biome check --write .` → 0 errors + `npx tsc --noEmit` → 0 type errors

---

### Task 0.1: 更新 package.json

**Files:**
- Modify: `agenthub/frontend/package.json`

**Steps:**

- [ ] **Step 1: 更新 package.json 依赖**

```json
{
  "name": "agenthub-frontend",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "next dev -p 7000",
    "build": "next build",
    "start": "next start",
    "check": "biome check --write . && tsc --noEmit"
  },
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-markdown": "^9.0.1",
    "tailwindcss": "^4.1.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4.1.0",
    "@biomejs/biome": "^2.0.0",
    "@hookform/resolvers": "^3.9.0",
    "react-hook-form": "^7.53.0",
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "typescript": "^5.5.0",
    "vitest": "^2.0.0",
    "@testing-library/react": "^16.0.0"
  }
}
```

- [ ] **Step 2: 运行 npm install**

Run: `cd agenthub/frontend && npm install`
Expected: 所有依赖安装成功，无警告

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/package.json agenthub/frontend/package-lock.json
git commit -m "chore: update dependencies for Phase 0 - Next.js 15, Tailwind v4, Biome 2.1"
```

---

### Task 0.2: 创建 biome.json

**Files:**
- Create: `agenthub/frontend/biome.json`

**Steps:**

- [ ] **Step 1: 创建 biome.json**

```json
{
  "$schema": "https://biomejs.dev/schemas/2.1.0/schema.json",
  "organizeImports": { "enabled": true },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "correctness": {
        "noUnusedVariables": "error",
        "useExhaustiveDependencies": "warn"
      },
      "suspicious": {
        "noExplicitAny": "error"
      },
      "style": {
        "noNonNullAssertion": "warn"
      }
    }
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2
  },
  "javascript": {
    "formatter": { "quoteStyle": "single", "semicolons": "asNeeded" }
  },
  "files": {
    "ignore": [".next/", "node_modules/", "*.md"]
  }
}
```

- [ ] **Step 2: 运行 biome check**

Run: `cd agenthub/frontend && npx @biomejs/biome check --write .`
Expected: 0 errors

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/biome.json
git commit -m "chore: add Biome 2.1 configuration for linting and formatting"
```

---

### Task 0.3: 重写 postcss.config.mjs

**Files:**
- Create: `agenthub/frontend/postcss.config.mjs`

**Steps:**

- [ ] **Step 1: 创建 postcss.config.mjs**

```js
// postcss.config.mjs
// Required for Next.js 15 Turbopack compatibility
// Do NOT use CommonJS (module.exports) or array format
export default {
  plugins: {
    '@tailwindcss/postcss': {},
  },
};
```

- [ ] **Step 2: 验证文件格式**

Run: `head -5 agenthub/frontend/postcss.config.mjs`
Expected: 第一行是注释，export default 存在

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/postcss.config.mjs
git commit -m "chore: configure PostCSS for Tailwind v4 with Turbopack compatibility"
```

---

### Task 0.4: 重写 app/globals.css

**Files:**
- Create: `agenthub/frontend/app/globals.css`
- Delete: `agenthub/frontend/tailwind.config.ts` (如果存在)

**Steps:**

- [ ] **Step 1: 创建 app/globals.css**

```css
@import "tailwindcss";

@theme {
  --color-primary: #3b82f6;
  --color-secondary: #EC4899;
  --font-sans: "Inter", system-ui, sans-serif;

  /* 响应式断点 - 必须显式声明，否则 md:, lg: 等类失效 */
  --breakpoint-sm: 640px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
}
```

- [ ] **Step 2: 删除旧的 tailwind.config.ts**

Run: `rm -f agenthub/frontend/tailwind.config.ts`

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/app/globals.css
git rm agenthub/frontend/tailwind.config.ts 2>/dev/null || true
git commit -m "chore: migrate Tailwind from v3 config to v4 CSS-first @theme"
```

---

### Task 0.5: 更新 tsconfig.json

**Files:**
- Modify: `agenthub/frontend/tsconfig.json`

**Steps:**

- [ ] **Step 1: 更新 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 2: 运行 TypeScript 检查**

Run: `cd agenthub/frontend && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/tsconfig.json
git commit -m "chore: enable TypeScript strict mode and noUncheckedIndexedAccess"
```

---

### Task 0.6: Phase 0 质量门禁

**Steps:**

- [ ] **Step 1: 运行完整质量门禁**

Run:
```bash
cd agenthub/frontend && \
npx @biomejs/biome check --write . && \
npx tsc --noEmit
```
Expected: 0 errors on both

- [ ] **Step 2: 验证 Tailwind v4 正常工作**

创建临时测试文件 `test-tailwind.tsx`:
```tsx
export default function Test() {
  return <div className="bg-primary text-white p-4 md:p-6">Test</div>;
}
```

Run: `cd agenthub/frontend && npm run build 2>&1 | head -20`
Expected: 构建成功，无 CSS 错误

- [ ] **Step 3: 清理并提交 Phase 0**

```bash
git add -A
git commit -m "chore(Phase 0): complete infrastructure setup

- Next.js 15 + React 19
- Tailwind CSS v4 (CSS-first @theme)
- Biome 2.1 linting/formatting
- TypeScript strict mode
- PostCSS Turbopack compatibility

Quality gate: biome check + tsc --noEmit both pass"
```

---

## Phase 1: 静态页面迁移

**目标:** 验证 App Router + Tailwind v4 + Biome 基础链路

---

### Task 1.1: 创建 app/layout.tsx

**Files:**
- Create: `agenthub/frontend/app/layout.tsx`

**Steps:**

- [ ] **Step 1: 创建 app/layout.tsx (RSC)**

```tsx
import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AgentHub',
  description: '多Agent协作聊天平台',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
```

- [ ] **Step 2: 验证构建**

Run: `cd agenthub/frontend && npm run dev &` 然后 `sleep 5 && curl -s http://localhost:7000 | head -20`
Expected: 页面渲染成功，无错误

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/app/layout.tsx
git commit -m "feat(Phase 1): create app/layout.tsx root layout"
```

---

### Task 1.2: 创建 app/page.tsx (主聊天页面容器)

**Files:**
- Create: `agenthub/frontend/app/page.tsx`

**Steps:**

- [ ] **Step 1: 创建 app/page.tsx**

```tsx
'use client';

import { useState } from 'react';
import { AgentList } from '@/components/agents/AgentList';
import { MessageList } from '@/components/chat/MessageList';
import { MessageInput } from '@/components/chat/MessageInput';
import { useAgentStore } from '@/lib/stores/agentStore';
import type { Agent } from '@/lib/types';

export default function HomePage() {
  const agents = useAgentStore((s) => s.agents);
  const [messages, setMessages] = useState<Message[]>([]);

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200 bg-white">
        <h1 className="text-xl font-semibold">AgentHub</h1>
        <div className="text-sm text-gray-500">多Agent协作平台</div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        <AgentList agents={agents} />
        <div className="flex-1 flex flex-col">
          <MessageList messages={messages} agentId={null} />
          <MessageInput
            onSubmit={(content) => console.log('submit:', content)}
            disabled={false}
            mentionCandidates={agents}
          />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 运行 biome check**

Run: `cd agenthub/frontend && npx @biomejs/biome check --write .`
Expected: 0 errors

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/app/page.tsx
git commit -m "feat(Phase 1): create app/page.tsx main chat page container"
```

---

### Task 1.3: 迁移 components/agents/AgentList.tsx

**Files:**
- Create: `agenthub/frontend/components/agents/AgentList.tsx`
- Modify: `agenthub/frontend/lib/types.ts` (添加 MentionCandidate)

**Steps:**

- [ ] **Step 1: 更新 lib/types.ts**

```typescript
export interface Message {
  id: string;
  sender: string;
  sender_name?: string;
  content: string;
  timestamp: number;
  type: 'user' | 'agent';
  agent_id?: string;
}

export interface Agent {
  id: string;
  name: string;
  role: string;
}

export interface MentionCandidate {
  id: string;
  label: string;
  avatar?: string;
}

export interface SendMessageResponse {
  success: boolean;
  message_id: string;
  is_broadcast?: boolean;
  is_termination?: boolean;
}
```

- [ ] **Step 2: 创建 components/agents/AgentList.tsx**

```tsx
'use client';

import type { Agent } from '@/lib/types';

interface AgentListProps {
  agents: Agent[];
}

export function AgentList({ agents }: AgentListProps) {
  return (
    <div className="w-48 bg-white border-r border-gray-200 p-4">
      <div className="text-sm font-semibold text-gray-700 pb-3 border-b border-gray-200">
        Agent 列表
      </div>
      {agents.map((agent) => (
        <div key={agent.id} className="py-3 border-b border-gray-100">
          <div className="text-sm font-medium text-gray-800">{agent.name}</div>
          <div className="text-xs text-gray-500 mt-0.5">{agent.role}</div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 3: 运行检查**

Run: `cd agenthub/frontend && npx @biomejs/biome check --write . && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 4: 提交**

```bash
git add agenthub/frontend/lib/types.ts agenthub/frontend/components/agents/AgentList.tsx
git commit -m "feat(Phase 1): migrate AgentList to App Router with 'use client'"
```

---

### Task 1.4: 创建基础组件桩文件

**Files:**
- Create: `agenthub/frontend/components/chat/MessageList.tsx`
- Create: `agenthub/frontend/components/chat/MessageBubble.tsx`
- Create: `agenthub/frontend/components/chat/MessageInput.tsx`
- Create: `agenthub/frontend/components/chat/MentionDropdown.tsx`

**Steps:**

- [ ] **Step 1: 创建 MessageList.tsx**

```tsx
'use client';

import { useEffect, useRef } from 'react';
import type { Message } from '@/lib/types';
import { MessageBubble } from './MessageBubble';

interface MessageListProps {
  messages: Message[];
  agentId: string | null;
  scrollRef?: React.RefObject<HTMLDivElement> | null;
}

export function MessageList({ messages, scrollRef }: MessageListProps) {
  const internalRef = useRef<HTMLDivElement>(null);
  const ref = scrollRef ?? internalRef;

  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  }, [messages, ref]);

  return (
    <div
      ref={ref}
      className="flex-1 overflow-y-auto p-4 bg-gray-50"
    >
      {messages.length === 0 ? (
        <div className="text-center text-gray-400 mt-20">
          暂无消息，开始对话吧
        </div>
      ) : (
        messages.map((msg, index) => (
          <MessageBubble key={msg.id || `msg-${index}-${msg.timestamp}`} message={msg} isStreaming={false} />
        ))
      )}
    </div>
  );
}
```

- [ ] **Step 2: 创建 MessageBubble.tsx**

```tsx
'use client';

import type { Message } from '@/lib/types';
import ReactMarkdown from 'react-markdown';

interface MessageBubbleProps {
  message: Message;
  isStreaming: boolean;
  onCopySuccess?: () => void;
}

export function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.type === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-2 ${
          isUser
            ? 'bg-primary text-white'
            : 'bg-white text-gray-800 border border-gray-200'
        }`}
      >
        {!isUser && (
          <div className="text-xs font-medium text-gray-500 mb-1">
            {message.sender_name || message.sender}
          </div>
        )}
        <div className=" prose prose-sm max-w-none">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        {isStreaming && (
          <span className="inline-block w-2 h-4 bg-current ml-1 animate-pulse" />
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: 创建 MessageInput.tsx (含 RHF + Zod)**

```tsx
'use client';

import { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import type { Agent, MentionCandidate } from '@/lib/types';
import { MentionDropdown } from './MentionDropdown';

const sendMessageSchema = z.object({
  content: z.string()
    .min(1, '消息不能为空')
    .max(5000, '消息过长'),
});

export type SendMessageInput = z.infer<typeof sendMessageSchema>;

interface MessageInputProps {
  onSubmit: (content: string) => void;
  disabled: boolean;
  mentionCandidates: MentionCandidate[];
}

interface MentionState {
  isActive: boolean;
  filterText: string;
  startIndex: number;
  cursorPos: number;
}

export function MessageInput({ onSubmit, disabled, mentionCandidates }: MessageInputProps) {
  const [input, setInput] = useState('');
  const [mentionState, setMentionState] = useState<MentionState>({
    isActive: false,
    filterText: '',
    startIndex: -1,
    cursorPos: 0,
  });
  const inputRef = useRef<HTMLInputElement>(null);

  const { register, handleSubmit, formState: { errors }, reset } = useForm<SendMessageInput>({
    resolver: zodResolver(sendMessageSchema),
  });

  const filteredAgents = mentionState.isActive
    ? mentionCandidates.filter((agent) =>
        agent.label.toLowerCase().includes(mentionState.filterText.toLowerCase())
      )
    : [];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    const cursorPos = e.target.selectionStart ?? 0;

    setInput(value);

    const textBeforeCursor = value.slice(0, cursorPos);
    const lastAtIndex = textBeforeCursor.lastIndexOf('@');

    if (lastAtIndex !== -1) {
      const textAfterAt = textBeforeCursor.slice(lastAtIndex + 1);
      if (!textAfterAt.includes(' ')) {
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
      filterText: '',
      startIndex: -1,
      cursorPos: 0,
    });
  };

  const handleSelect = (candidate: MentionCandidate) => {
    if (mentionState.startIndex === -1) return;

    const beforeMention = input.slice(0, mentionState.startIndex);
    const afterMention = input.slice(mentionState.cursorPos);
    const mentionInsert = `@${candidate.label} `;

    setInput(beforeMention + mentionInsert + afterMention);
    setMentionState({
      isActive: false,
      filterText: '',
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
    onSubmit(data.content);
    reset();
  };

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (mentionState.isActive && inputRef.current) {
        const target = e.target as HTMLElement;
        if (!inputRef.current.contains(target) && !target.closest('.mention-dropdown')) {
          setMentionState({
            isActive: false,
            filterText: '',
            startIndex: -1,
            cursorPos: 0,
          });
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [mentionState.isActive]);

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="flex p-4 border-t bg-white">
      <div className="flex-1 relative">
        <input
          {...register('content')}
          ref={inputRef}
          type="text"
          value={input}
          onChange={handleChange}
          placeholder={disabled ? "等待回复..." : "输入消息，@某人可定向发送"}
          disabled={disabled}
          className="w-full px-4 py-3 rounded-full border border-gray-300 focus:outline-none focus:border-blue-500"
        />
        {errors.content && (
          <p className="text-red-500 text-sm mt-1">{errors.content.message}</p>
        )}
        {mentionState.isActive && (
          <div className="mention-dropdown absolute bottom-full mb-2 w-full">
            <MentionDropdown
              candidates={filteredAgents}
              query={mentionState.filterText}
              onSelect={handleSelect}
              onClose={() => setMentionState((s) => ({ ...s, isActive: false }))}
              anchorRect={null}
            />
          </div>
        )}
      </div>
      <button
        type="submit"
        disabled={disabled || !input.trim()}
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

- [ ] **Step 4: 创建 MentionDropdown.tsx**

```tsx
'use client';

import type { MentionCandidate } from '@/lib/types';

interface MentionDropdownProps {
  candidates: MentionCandidate[];
  query: string;
  onSelect: (candidate: MentionCandidate) => void;
  onClose: () => void;
  anchorRect: DOMRect | null;
}

export function MentionDropdown({ candidates, onSelect, onClose }: MentionDropdownProps) {
  if (candidates.length === 0) {
    return null;
  }

  return (
    <div
      role="listbox"
      aria-label="选择 Agent"
      className="bg-white rounded-lg shadow-lg border border-gray-200 py-1"
    >
      {candidates.map((candidate) => (
        <button
          key={candidate.id}
          role="option"
          aria-selected={false}
          onClick={() => onSelect(candidate)}
          className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center gap-2"
        >
          {candidate.avatar && (
            <img src={candidate.avatar} alt="" className="w-6 h-6 rounded-full" />
          )}
          <span className="text-sm font-medium text-gray-800">{candidate.label}</span>
        </button>
      ))}
    </div>
  );
}
```

- [ ] **Step 5: 运行检查**

Run: `cd agenthub/frontend && npx @biomejs/biome check --write . && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 6: 提交**

```bash
git add agenthub/frontend/components/chat/MessageList.tsx
git add agenthub/frontend/components/chat/MessageBubble.tsx
git add agenthub/frontend/components/chat/MessageInput.tsx
git add agenthub/frontend/components/chat/MentionDropdown.tsx
git commit -m "feat(Phase 1): create all chat components with 'use client' and Zod validation"
```

---

### Task 1.5: Phase 1 质量门禁

**Steps:**

- [ ] **Step 1: 运行完整质量门禁**

Run:
```bash
cd agenthub/frontend && \
npx @biomejs/biome check --write . && \
npx tsc --noEmit
```
Expected: 0 errors on both

- [ ] **Step 2: 手动验证页面渲染**

Run: `cd agenthub/frontend && npm run dev`
Expected: 访问 http://localhost:7000 显示 AgentHub 界面，Agent 列表和消息输入框可见

- [ ] **Step 3: 提交 Phase 1 完成**

```bash
git tag -a phase-1-complete -m "Phase 1: Static page migration complete - App Router + Tailwind v4 verified"
git commit --allow-empty -m "chore(Phase 1): phase 1 complete - all static pages migrated"
```

---

## Phase 2a: SSE 传输层独立验证

**目标:** SSE 连接管理逻辑独立验证通过

---

### Task 2.1: 创建 lib/sse.ts

**Files:**
- Create: `agenthub/frontend/lib/sse.ts`

**Steps:**

- [ ] **Step 1: 创建 lib/sse.ts**

```typescript
const MAX_RETRIES = 5;
const BASE_DELAY = 1000;

export type SSEEventType = 'message' | 'termination' | 'error';

export interface SSEMessage {
  id?: string;
  sender?: string;
  sender_name?: string;
  agent_id?: string;
  role?: string;
  content?: string;
  timestamp?: number;
  type?: string;
  keyword?: string;
}

export interface SSEConnectionOptions {
  baseUrl: string;
  onMessage: (data: SSEMessage) => void;
  onTermination: (keyword: string) => void;
  onError: (error: string) => void;
}

export function createSSEConnection(options: SSEConnectionOptions) {
  let aborted = false;
  let retryDelay = BASE_DELAY;
  let retryCount = 0;

  const API_KEY = 'dev-secret-key';

  const connect = async () => {
    try {
      const response = await fetch(`${options.baseUrl}/api/events`, {
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
        },
        cache: 'no-store',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || trimmed.startsWith(':')) continue;

          if (trimmed.startsWith('data:')) {
            const data = trimmed.slice(5).trim();
            if (data) {
              try {
                const parsed = JSON.parse(data);
                if (parsed.keyword || parsed.type === 'termination') {
                  options.onTermination(parsed.keyword || '');
                } else {
                  options.onMessage(parsed);
                }
              } catch {
                options.onMessage(data as unknown as SSEMessage);
              }
            }
          }
        }
      }
    } catch (err) {
      if (aborted) return;

      retryCount++;
      if (retryCount > MAX_RETRIES) {
        options.onError(`连接失败，已达到最大重试次数 (${MAX_RETRIES})`);
        return;
      }

      options.onError(`连接断开，${retryDelay / 1000}s 后重试... (${retryCount}/${MAX_RETRIES})`);
      setTimeout(connect, retryDelay);
      retryDelay = Math.min(retryDelay * 2, 16000);
    }
  };

  connect();

  return {
    close: () => {
      aborted = true;
    },
  };
}
```

- [ ] **Step 2: 运行检查**

Run: `cd agenthub/frontend && npx @biomejs/biome check --write . && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/lib/sse.ts
git commit -m "feat(Phase 2a): create SSE transport layer with retry logic (5 retries, exponential backoff)"
```

---

### Task 2.2: 创建 lib/stores/

**Files:**
- Create: `agenthub/frontend/lib/stores/messageStore.ts`
- Create: `agenthub/frontend/lib/stores/agentStore.ts`
- Create: `agenthub/frontend/lib/stores/uiStore.ts`

**Steps:**

- [ ] **Step 1: 创建 lib/stores/messageStore.ts**

```typescript
import { create } from 'zustand';
import type { Message } from '@/lib/types';

interface MessageState {
  messages: Message[];
  isStreaming: boolean;
  addMessage: (msg: Message) => void;
  appendStreamChunk: (messageId: string, chunk: string) => void;
  setStreaming: (v: boolean) => void;
  reset: () => void;
}

export const useMessageStore = create((set) => ({
  messages: [],
  isStreaming: false,
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  appendStreamChunk: (id, chunk) =>
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === id ? { ...m, content: m.content + chunk } : m
      ),
    })),
  setStreaming: (v) => set({ isStreaming: v }),
  reset: () => set({ messages: [], isStreaming: false }),
}));
```

- [ ] **Step 2: 创建 lib/stores/agentStore.ts**

```typescript
import { create } from 'zustand';
import type { Agent } from '@/lib/types';

interface AgentState {
  agents: Agent[];
  setAgents: (agents: Agent[]) => void;
}

export const useAgentStore = create((set) => ({
  agents: [],
  setAgents: (agents) => set({ agents }),
}));
```

- [ ] **Step 3: 创建 lib/stores/uiStore.ts**

```typescript
import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  activeAgentId: string | null;
  toggleSidebar: () => void;
  setActiveAgent: (id: string | null) => void;
}

export const useUIStore = create((set) => ({
  sidebarOpen: true,
  activeAgentId: null,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setActiveAgent: (id) => set({ activeAgentId: id }),
}));
```

- [ ] **Step 4: 运行检查**

Run: `cd agenthub/frontend && npx @biomejs/biome check --write . && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 5: 提交**

```bash
git add agenthub/frontend/lib/stores/messageStore.ts
git add agenthub/frontend/lib/stores/agentStore.ts
git add agenthub/frontend/lib/stores/uiStore.ts
git commit -m "feat(Phase 2a): create Zustand stores (message, agent, ui) with pure function actions"
```

---

### Task 2.3: 创建 lib/api.ts

**Files:**
- Create: `agenthub/frontend/lib/api.ts`

**Steps:**

- [ ] **Step 1: 创建 lib/api.ts**

```typescript
import type { Message, Agent, SendMessageResponse } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7005';
const API_KEY = 'dev-secret-key';

const headers = {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY,
};

export const api = {
  async sendMessage(content: string): Promise<SendMessageResponse> {
    const res = await fetch(`${API_BASE}/api/messages`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        content,
        sender: 'user',
        sender_name: '用户',
      }),
    });
    return res.json();
  },

  async getMessages(limit: number = 50): Promise<{ messages: Message[] }> {
    const res = await fetch(`${API_BASE}/api/messages?limit=${limit}`, { headers });
    return res.json();
  },

  async getAgents(): Promise<{ agents: Agent[] }> {
    const res = await fetch(`${API_BASE}/api/agents`, { headers });
    return res.json();
  },
};
```

- [ ] **Step 2: 运行检查**

Run: `cd agenthub/frontend && npx @biomejs/biome check --write . && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/lib/api.ts
git commit -m "feat(Phase 2a): create API module for HTTP requests (不含 SSE)"
```

---

### Task 2.4: Phase 2a 质量门禁

**Steps:**

- [ ] **Step 1: 运行完整质量门禁**

Run:
```bash
cd agenthub/frontend && \
npx @biomejs/biome check --write . && \
npx tsc --noEmit
```
Expected: 0 errors on both

- [ ] **Step 2: 验证 SSE 类型定义**

检查 lib/sse.ts 中的 SSEMessage 接口与 lib/types.ts 中的 Message 接口一致

- [ ] **Step 3: 提交**

```bash
git tag -a phase-2a-complete -m "Phase 2a: SSE transport layer complete - stores and API separated"
git commit --allow-empty -m "chore(Phase 2a): phase 2a complete - SSE transport layer verified"
```

---

## Phase 2b: 聊天 UI 集成

**目标:** 流式消息端到端正常

---

### Task 2.5: 创建 lib/hooks/useChatStream.ts

**Files:**
- Create: `agenthub/frontend/lib/hooks/useChatStream.ts`

**Steps:**

- [ ] **Step 1: 创建 lib/hooks/useChatStream.ts**

```typescript
'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { createSSEConnection } from '@/lib/sse';
import { useMessageStore } from '@/lib/stores/messageStore';
import { api } from '@/lib/api';
import type { Message } from '@/lib/types';

interface UseChatStreamOptions {
  agentId: string | null;
  baseUrl: string;
}

interface UseChatStreamReturn {
  sendMessage: (content: string) => Promise<void>;
  disconnect: () => void;
  connectionState: 'idle' | 'connecting' | 'connected' | 'reconnecting' | 'error';
  lastError: string | null;
}

export function useChatStream(options: UseChatStreamOptions): UseChatStreamReturn {
  const { agentId, baseUrl } = options;
  const [connectionState, setConnectionState] = useState<'idle' | 'connecting' | 'connected' | 'reconnecting' | 'error'>('idle');
  const [lastError, setLastError] = useState<string | null>(null);
  const connectionRef = useRef<ReturnType<typeof createSSEConnection> | null>(null);

  const addMessage = useMessageStore((s) => s.addMessage);
  const appendStreamChunk = useMessageStore((s) => s.appendStreamChunk);
  const setStreaming = useMessageStore((s) => s.setStreaming);
  const messages = useMessageStore((s) => s.messages);

  const disconnect = useCallback(() => {
    if (connectionRef.current) {
      connectionRef.current.close();
      connectionRef.current = null;
    }
    setConnectionState('idle');
  }, []);

  const sendMessage = useCallback(async (content: string) => {
    if (!agentId) {
      setLastError('请先选择一个 Agent');
      setConnectionState('error');
      return;
    }

    // 乐观更新：添加用户消息
    const tempId = `temp-${Date.now()}`;
    const timestamp = Math.floor(Date.now() / 1000);
    const userMessage: Message = {
      id: tempId,
      sender: 'user',
      sender_name: '用户',
      content,
      timestamp,
      type: 'user',
    };
    addMessage(userMessage);

    // 断开旧连接
    disconnect();

    setConnectionState('connecting');
    setStreaming(true);
    setLastError(null);

    try {
      const result = await api.sendMessage(content);
      if (!result.success) {
        throw new Error('发送消息失败');
      }

      setConnectionState('connected');

      // 建立 SSE 连接
      connectionRef.current = createSSEConnection({
        baseUrl,
        onMessage: (data) => {
          if (data.id && data.content) {
            // 检查是否有待替换的 temp 消息
            const existingIndex = messages.findIndex((m) => m.id.startsWith('temp-') && m.content === content);
            if (existingIndex >= 0) {
              // 替换 temp 消息
              useMessageStore.getState().messages[existingIndex] = data as Message;
            } else {
              addMessage(data as Message);
            }
          }
        },
        onTermination: (keyword) => {
          setStreaming(false);
          setConnectionState('idle');
        },
        onError: (error) => {
          setLastError(error);
          setConnectionState('reconnecting');
        },
      });
    } catch (err) {
      setLastError(err instanceof Error ? err.message : '发送失败');
      setConnectionState('error');
      setStreaming(false);
    }
  }, [agentId, baseUrl, addMessage, appendStreamChunk, setStreaming, disconnect, messages]);

  // 组件卸载时断开连接
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return { sendMessage, disconnect, connectionState, lastError };
}
```

- [ ] **Step 2: 运行检查**

Run: `cd agenthub/frontend && npx @biomejs/biome check --write . && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/lib/hooks/useChatStream.ts
git commit -m "feat(Phase 2b): create useChatStream hook - SSE + Store orchestration"
```

---

### Task 2.6: 创建 lib/schemas/message.ts

**Files:**
- Create: `agenthub/frontend/lib/schemas/message.ts`

**Steps:**

- [ ] **Step 1: 创建 lib/schemas/message.ts**

```typescript
import { z } from 'zod';

export const sendMessageSchema = z.object({
  content: z.string()
    .min(1, '消息不能为空')
    .max(5000, '消息过长'),
});

export type SendMessageInput = z.infer<typeof sendMessageSchema>;
```

- [ ] **Step 2: 更新 MessageInput.tsx 使用 schemas**

```tsx
// 替换 MessageInput.tsx 中的内联 schema 为导入
import { sendMessageSchema, type SendMessageInput } from '@/lib/schemas/message';
```

- [ ] **Step 3: 运行检查**

Run: `cd agenthub/frontend && npx @biomejs/biome check --write . && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 4: 提交**

```bash
git add agenthub/frontend/lib/schemas/message.ts
git commit -m "feat(Phase 2b): create Zod schema for message validation"
```

---

### Task 2.7: 更新 app/page.tsx 集成 useChatStream

**Files:**
- Modify: `agenthub/frontend/app/page.tsx`

**Steps:**

- [ ] **Step 1: 更新 app/page.tsx**

```tsx
'use client';

import { useEffect } from 'react';
import { AgentList } from '@/components/agents/AgentList';
import { MessageList } from '@/components/chat/MessageList';
import { MessageInput } from '@/components/chat/MessageInput';
import { useAgentStore } from '@/lib/stores/agentStore';
import { useMessageStore } from '@/lib/stores/messageStore';
import { useChatStream } from '@/lib/hooks/useChatStream';
import { api } from '@/lib/api';
import type { Message } from '@/lib/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:7005';

export default function HomePage() {
  const agents = useAgentStore((s) => s.agents);
  const setAgents = useAgentStore((s) => s.setAgents);
  const messages = useMessageStore((s) => s.messages);
  const { sendMessage, connectionState, lastError } = useChatStream({
    agentId: null,
    baseUrl: API_BASE,
  });

  useEffect(() => {
    // 加载初始数据
    const loadData = async () => {
      try {
        const [msgsRes, agentsRes] = await Promise.all([
          api.getMessages(),
          api.getAgents(),
        ]);
        useMessageStore.getState().reset();
        msgsRes.messages?.forEach((m) => useMessageStore.getState().addMessage(m));
        setAgents(agentsRes.agents || []);
      } catch (err) {
        console.error('Failed to load data:', err);
      }
    };
    loadData();
  }, [setAgents]);

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <div className="flex justify-between items-center px-6 py-4 border-b border-gray-200 bg-white">
        <h1 className="text-xl font-semibold">AgentHub</h1>
        <div className="text-sm text-gray-500">
          {connectionState === 'connected' ? '🟢 已连接' : connectionState === 'connecting' ? '🟡 连接中...' : '⚪ 空闲'}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        <AgentList agents={agents} />
        <div className="flex-1 flex flex-col">
          <MessageList messages={messages} agentId={null} />
          <MessageInput
            onSubmit={sendMessage}
            disabled={connectionState === 'connecting'}
            mentionCandidates={agents.map((a) => ({ id: a.id, label: a.name }))}
          />
        </div>
      </div>

      {lastError && (
        <div className="absolute bottom-20 left-1/2 transform -translate-x-1/2 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg">
          {lastError}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: 运行检查**

Run: `cd agenthub/frontend && npx @biomejs/biome check --write . && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/app/page.tsx
git commit -m "feat(Phase 2b): integrate useChatStream in page.tsx with connection status"
```

---

### Task 2.8: Phase 2b 质量门禁

**Steps:**

- [ ] **Step 1: 运行完整质量门禁**

Run:
```bash
cd agenthub/frontend && \
npx @biomejs/biome check --write . && \
npx tsc --noEmit
```
Expected: 0 errors on both

- [ ] **Step 2: 手动验证 SSE 功能**

Run: `cd agenthub/frontend && npm run dev`
1. 访问 http://localhost:7000
2. 输入消息测试发送
3. 观察 SSE 连接状态变化
4. 验证消息是否正确显示

- [ ] **Step 3: 提交**

```bash
git tag -a phase-2b-complete -m "Phase 2b: Chat UI integration complete - SSE streaming verified"
git commit --allow-empty -m "chore(Phase 2b): phase 2b complete - chat UI integrated with SSE"
```

---

## Phase 3: 表单增强与清理

**目标:** 完整迁移完成，零 lint/type 错误

---

### Task 3.1: 创建 Agent 列表页

**Files:**
- Create: `agenthub/frontend/app/agents/page.tsx`

**Steps:**

- [ ] **Step 1: 创建 app/agents/page.tsx**

```tsx
import { AgentList } from '@/components/agents/AgentList';
import { useAgentStore } from '@/lib/stores/agentStore';

export default async function AgentsPage() {
  // Server Component - 数据获取在 client hydrate 后通过 store 同步
  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-6">Agent 列表</h1>
      <AgentList agents={[]} />
    </div>
  );
}
```

- [ ] **Step 2: 运行检查**

Run: `cd agenthub/frontend && npx @biomejs/biome check --write . && npx tsc --noEmit`
Expected: 0 errors

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/app/agents/page.tsx
git commit -m "feat(Phase 3): create agents list page"
```

---

### Task 3.2: 删除 pages/ 目录

**Files:**
- Delete: `agenthub/frontend/pages/` 目录及所有文件

**Steps:**

- [ ] **Step 1: 删除 pages/ 目录**

Run: `rm -rf agenthub/frontend/pages`

- [ ] **Step 2: 验证没有 pages/ 引用**

Run: `grep -r "pages/" agenthub/frontend/app/ agenthub/frontend/components/ 2>/dev/null || echo "No references found"`
Expected: "No references found"

- [ ] **Step 3: 提交**

```bash
git rm -rf agenthub/frontend/pages
git commit -m "feat(Phase 3): remove pages/ directory - full App Router migration complete"
```

---

### Task 3.3: 最终质量门禁

**Steps:**

- [ ] **Step 1: 运行完整质量门禁**

Run:
```bash
cd agenthub/frontend && \
npx @biomejs/biome check --write . && \
npx tsc --noEmit
```
Expected: 0 errors on both

- [ ] **Step 2: 验证构建**

Run: `cd agenthub/frontend && npm run build`
Expected: 构建成功，无警告

- [ ] **Step 3: 最终提交**

```bash
git tag -a phase-3-complete -m "Phase 3: Migration complete - all phases verified"
git commit --allow-empty -m "chore(Phase 3): phase 3 complete - full migration finished"
```

---

## 依赖安装命令（按 Phase 拆分）

```bash
# Phase 0
cd agenthub/frontend && npm install

# Phase 1-3 无需额外依赖安装
```

---

## 回滚策略

每个 Phase 完成后会创建 git tag：
- `phase-0-complete` - 基础设施准备完成
- `phase-1-complete` - 静态页面迁移完成
- `phase-2a-complete` - SSE 传输层完成
- `phase-2b-complete` - 聊天 UI 集成完成
- `phase-3-complete` - 迁移全部完成

如需回滚到某个 Phase：
```bash
git checkout <tag-name>
cd agenthub/frontend && npm install
```

---

## 验证命令汇总

| Phase | 命令 | 预期结果 |
|-------|------|----------|
| Phase 0 | `npx @biomejs/biome check --write . && npx tsc --noEmit` | 0 errors |
| Phase 1 | `npm run dev` + 浏览器验证 | 页面正常渲染 |
| Phase 2a | `npx @biomejs/biome check --write . && npx tsc --noEmit` | 0 errors |
| Phase 2b | SSE 连接测试 | 流式消息正常显示 |
| Phase 3 | `npm run build` | 构建成功 |

---

**Plan Created:** 2026-05-25
**Spec Reference:** `docs/superpowers/specs/2026-05-25-agenthub-frontend-migration-design.md`