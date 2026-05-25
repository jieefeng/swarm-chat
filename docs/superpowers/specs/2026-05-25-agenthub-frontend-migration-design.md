# AgentHub 前端迁移设计规范

**日期：** 2026-05-25
**版本：** v1.0
**状态：** 设计完成，待执行

---

## 1. 背景与目标

### 1.1 迁移背景

AgentHub 前端目前使用 Next.js 14 (Pages Router) + 基础 useState，无状态管理库、无代码规范工具。拟迁移到 2026 年最新推荐技术栈，提升开发效率和代码质量。

### 1.2 迁移目标

- 升级到 Next.js 15 (App Router)
- 引入 Zustand 状态管理
- 引入 Tailwind CSS v4 (CSS-first 配置)
- 引入 Biome 代码规范工具
- 引入 Zod + React Hook Form 表单校验
- SSE 架构关注点分离

### 1.3 约束条件

- 一次性切换，可接受短暂不可用
- 有自动化测试覆盖
- 供个人使用，可持续开发
- 保持 react-markdown（不迁移到 unified）

---

## 2. 技术架构

### 2.1 技术栈对比

| 层级 | 当前 | 迁移后 |
|------|------|--------|
| 框架 | Next.js 14 (Pages Router) | Next.js 15 (App Router) |
| 语言 | TypeScript 5.4.5 | TypeScript 5.x (strict) |
| 状态 | useState/useRef | Zustand (领域拆分) |
| 表单校验 | 无 | Zod + React Hook Form |
| 样式 | Tailwind CSS 3.4.3 | Tailwind CSS v4 (CSS-first) |
| 代码规范 | 无 | Biome |
| Markdown | react-markdown | react-markdown (保持) |
| SSE | lib/api.ts 混合 | sse.ts + useChatStream.ts 分离 |

### 2.2 目标目录结构

```
agenthub/frontend/
├── app/                      # App Router
│   ├── layout.tsx           # 根布局 (RSC)
│   ├── page.tsx            # 主页面 (RSC)
│   ├── globals.css          # Tailwind v4 + @theme
│   └── agents/
│       └── page.tsx        # Agent 列表页 (RSC)
├── components/              # Client Components ('use client')
│   ├── agents/
│   │   └── AgentList.tsx
│   └── chat/
│       ├── ChatWindow.tsx
│       ├── MessageList.tsx
│       ├── MessageBubble.tsx
│       ├── MessageInput.tsx
│       └── MentionDropdown.tsx
├── lib/
│   ├── api.ts              # HTTP 请求（不含 SSE）
│   ├── sse.ts              # SSE 连接管理（独立）
│   ├── types.ts            # TypeScript 类型
│   ├── stores/             # Zustand stores
│   │   ├── messageStore.ts # messages[], isStreaming
│   │   ├── agentStore.ts   # agents[], setAgents
│   │   └── uiStore.ts      # sidebarOpen, activeAgentId
│   ├── hooks/
│   │   └── useChatStream.ts # SSE + Store 编排
│   └── schemas/
│       └── message.ts      # Zod schemas
├── biome.json              # Biome 配置
├── postcss.config.mjs       # @tailwindcss/postcss
└── package.json            # 更新依赖
```

---

## 3. Phase 实施计划

### Phase 0: 基础设施准备

**目标：** 所有后续 Phase 生成的代码自动符合规范

#### 任务清单

1. **更新 package.json**
   ```json
   {
     "dependencies": {
       "tailwindcss": "^4.1.0"
     },
     "devDependencies": {
       "@tailwindcss/postcss": "^4.1.0",
       "@biomejs/biome": "^2.0.0"
     }
   }
   ```
   - 移除旧 tailwindcss@3.x, autoprefixer, eslint, prettier

2. **重写 postcss.config.mjs**
   ```js
   export default {
     plugins: {
       '@tailwindcss/postcss': {},
     },
   };
   ```
   - 对象格式，无 autoprefixer（v4 内置）

3. **重写 app/globals.css**
   ```css
   @import "tailwindcss";

   @theme {
     --color-primary: #3b82f6;
     --color-secondary: #EC4899;
     --font-sans: "Inter", system-ui, sans-serif;
   }
   ```
   - 删除 tailwind.config.ts（v4 不再需要）

4. **创建 biome.json**
   ```json
   {
     "$schema": "https://biomejs.dev/schemas/2.0.0/schema.json",
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

5. **更新 tsconfig.json**
   - `strict: true`
   - `noUncheckedIndexedAccess: true`

6. **运行质量门禁**
   ```bash
   npx @biomejs/biome check --write .
   npx tsc --noEmit
   ```

### Phase 1: 静态页面迁移

**目标：** 验证 App Router + Tailwind v4 + Biome 基础链路

#### 任务清单

1. 创建 `app/layout.tsx` (RSC)
   - 替换 pages/_app.tsx + pages/_document.tsx
   - 导入 globals.css

2. 创建 `app/page.tsx` (RSC)
   - 主聊天页面容器
   - 导入 Client Components

3. 创建 `app/agents/page.tsx` (RSC)
   - Agent 列表页

4. 迁移 `components/agents/AgentList.tsx`
   - 添加 `'use client'` 首行
   - 验证样式正常

### Phase 2a: SSE 传输层独立验证

**目标：** SSE 连接管理逻辑独立验证通过

#### 任务清单

1. 创建 `lib/sse.ts`
   - SSE 连接管理
   - 重连逻辑：5 次，指数退避 (1s → 2s → 4s → 8s → 16s)
   - 类型化事件接口

2. 创建 `lib/types.ts`
   - Message, Agent, SendMessageResponse 类型

3. 编写测试或手动验证脚本
   - 验证重连、心跳、事件解析

### Phase 2b: 聊天 UI 集成

**目标：** 流式消息端到端正常

#### 任务清单

1. 创建 `lib/stores/messageStore.ts`
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

2. 创建 `lib/stores/agentStore.ts`
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

3. 创建 `lib/stores/uiStore.ts`
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

4. 创建 `lib/hooks/useChatStream.ts`
   - 组合 sse.ts + messageStore
   - 处理 SSE 消息事件

5. 创建 `lib/schemas/message.ts`
   ```typescript
   import { z } from 'zod';

   export const sendMessageSchema = z.object({
     content: z.string()
       .min(1, '消息不能为空')
       .max(5000, '消息过长'),
   });

   export type SendMessageInput = z.infer<typeof sendMessageSchema>;
   ```

6. 迁移组件
   - `MessageList.tsx`
   - `MessageBubble.tsx`
   - `MessageInput.tsx` (RHF + Zod)

### Phase 3: 表单增强与清理

**目标：** 完整迁移完成，零 lint/type 错误

#### 任务清单

1. MessageInput 接入 React Hook Form + Zod 校验
2. 删除 `pages/` 目录
3. 清理旧依赖
4. 运行质量门禁

---

## 4. 核心规则

### 4.1 RSC Boundary Rules

```
'use client' MUST be the VERY FIRST line of the file (before imports, comments, or blank lines)
ALL files under components/ directory MUST have 'use client' unless explicitly documented as server-only
ONLY these files are Server Components:
  app/layout.tsx
  app/*/page.tsx (container only, no interactive elements)
  app/*/loading.tsx, error.tsx (if purely static)
When in doubt, ADD 'use client'. Removing it later is cheaper than debugging hydration mismatches.
```

### 4.2 Server → Client Data Passing Rules

```
Server → Client data ONLY through Props
Store initialization MUST be in useEffect (not top-level getState())
Server Components MUST NOT import any use*Store
```

### 4.3 Store Rules

```
Each Store = One Hook + Pure Function Actions
UI transient state in uiStore (not mixed with business data)
Cross-store communication ONLY through Hook composition layer
Store MUST NOT import other stores
```

### 4.4 Phase Completion Checklist (MUST RUN)

```
Each phase is NOT complete until ALL pass:
1. npx @biomejs/biome check --write . → 0 errors
2. npx tsc --noEmit → 0 type errors
3. Manual verification of phase goal (document what was tested)
4. No `any` types introduced
5. No console.log left in production code
```

---

## 5. 关键技术细节

### 5.1 Tailwind v4 CSS-first 配置

```css
/* app/globals.css */
@import "tailwindcss";

@theme {
  --color-primary: #3b82f6;
  --color-secondary: #EC4899;
  --font-sans: "Inter", system-ui, sans-serif;
}
```

- 无需 tailwind.config.ts
- PostCSS 插件：`@tailwindcss/postcss`
- 版本：tailwindcss@^4.1.0, @tailwindcss/postcss@^4.1.0（必须一致）

### 5.2 SSE 重连策略

```typescript
// lib/sse.ts
const MAX_RETRIES = 5;
const BASE_DELAY = 1000;

const connect = async () => {
  let retries = 0;
  // 重连逻辑：指数退避
  // 1s → 2s → 4s → 8s → 16s
};
```

### 5.3 Zod + React Hook Form 集成

```typescript
// components/chat/MessageInput.tsx
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { sendMessageSchema } from '@/lib/schemas/message';

type FormData = z.infer<typeof sendMessageSchema>;

export function MessageInput() {
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(sendMessageSchema),
  });
  // ...
}
```

---

## 6. 禁止的模式

```typescript
// ❌ Store 间互相引用
import { useMessageStore } from './messageStore';
export const useAgentStore = create((set) => ({
  // ...
  syncMessages: () => {
    const msgs = useMessageStore.getState().messages; // 禁止！
  },
}));

// ❌ Server Component 中调用 store
// app/page.tsx (Server Component)
import { useAgentStore } from '@/lib/stores/agentStore'; // 禁止！

// ❌ 'use client' 非首行
import { something } from 'something'; // 错误！
'use client'; // 必须是首行

// ❌ Actions 使用外部闭包
export const useMessageStore = create((set, get) => ({
  addMessage: (msg) => {
    const current = get().messages; // 避免滥用，仅必要时使用
    // ...
  },
}));

// ❌ console.log 在生产代码
console.log('debug'); // 禁止！
```

---

## 7. 验证标准

| Phase | 验证标准 |
|-------|----------|
| Phase 0 | biome check + tsc --noEmit 通过 |
| Phase 1 | 页面正常渲染，样式正确 |
| Phase 2a | SSE 传输层单元测试/手动验证通过 |
| Phase 2b | 流式消息端到端正常 |
| Phase 3 | 零 lint/type 错误，pages/ 已删除 |

---

**Author:** Claude Code
**Last Updated:** 2026-05-25