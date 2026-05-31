# 网页预览功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现网页预览功能，支持在聊天界面中直接预览 Agent 生成的 HTML 代码

**Architecture:** 纯前端实现，使用 iframe sandbox 渲染自包含的 HTML 代码，通过 PreviewCard 组件集成到 MessageBubble

**Tech Stack:** React, TypeScript, TailwindCSS, iframe sandbox

---

## 文件结构

```
agenthub/frontend/
├── lib/
│   └── preview.ts                    # HTML 提取和处理工具
├── components/chat/
│   ├── PreviewCard.tsx               # 预览卡片主组件
│   ├── PreviewFrame.tsx              # iframe 沙箱
│   ├── PreviewToolbar.tsx            # 工具栏
│   └── MessageBubble.tsx             # 修改：集成预览功能
└── backend/services/
    └── session.py                    # 修改：Agent Prompt 增加预览规则
```

---

## Task 1: 创建 HTML 提取工具

**Files:**
- Create: `agenthub/frontend/lib/preview.ts`
- Test: `agenthub/frontend/lib/__tests__/preview.test.ts`

- [ ] **Step 1: 编写测试**

```typescript
// agenthub/frontend/lib/__tests__/preview.test.ts
import { describe, it, expect } from 'vitest';
import { extractHtmlFromMarkdown, processHtml } from '../preview';

describe('extractHtmlFromMarkdown', () => {
  it('从 html 代码块中提取', () => {
    const content = '一些文字\n```html\n<div>Hello</div>\n```\n更多文字';
    expect(extractHtmlFromMarkdown(content)).toBe('<div>Hello</div>');
  });

  it('提取完整 HTML 文档', () => {
    const content = '前文\n<!DOCTYPE html><html><body>Test</body></html>\n后文';
    expect(extractHtmlFromMarkdown(content)).toBe('<!DOCTYPE html><html><body>Test</body></html>');
  });

  it('无 HTML 时返回 null', () => {
    expect(extractHtmlFromMarkdown('普通文本')).toBeNull();
  });
});

describe('processHtml', () => {
  it('注入 viewport meta', () => {
    const html = '<html><head></head><body></body></html>';
    const result = processHtml(html);
    expect(result).toContain('viewport');
  });

  it('注入基础样式', () => {
    const html = '<html><head></head><body></body></html>';
    const result = processHtml(html);
    expect(result).toContain('box-sizing');
  });

  it('处理无 head 标签的 HTML', () => {
    const html = '<div>Hello</div>';
    const result = processHtml(html);
    expect(result).toContain('<html');
    expect(result).toContain('viewport');
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd agenthub/frontend && npx vitest run lib/__tests__/preview.test.ts`
Expected: FAIL with "Cannot find module '../preview'"

- [ ] **Step 3: 实现 preview.ts**

```typescript
// agenthub/frontend/lib/preview.ts

/**
 * 从 markdown 内容中提取 HTML 代码
 */
export function extractHtmlFromMarkdown(content: string): string | null {
  // 尝试从 html 代码块中提取
  const htmlMatch = content.match(/```html\n([\s\S]*?)\n```/);
  if (htmlMatch) {
    return htmlMatch[1].trim();
  }

  // 尝试提取完整 HTML 文档
  const fullHtmlMatch = content.match(/(<!DOCTYPE html>[\s\S]*<\/html>)/i);
  if (fullHtmlMatch) {
    return fullHtmlMatch[1];
  }

  // 尝试提取包含基本 HTML 标签的内容
  const basicHtmlMatch = content.match(/(<html[\s\S]*<\/html>)/i);
  if (basicHtmlMatch) {
    return basicHtmlMatch[1];
  }

  return null;
}

/**
 * 处理 HTML：注入 viewport、基础样式
 */
export function processHtml(htmlCode: string): string {
  let html = htmlCode;

  // 确保有基本的 HTML 结构
  if (!html.includes('<html')) {
    html = `<!DOCTYPE html><html><head></head><body>${html}</body></html>`;
  }

  // 确保有 DOCTYPE
  if (!html.includes('<!DOCTYPE')) {
    html = '<!DOCTYPE html>' + html;
  }

  // 注入 meta viewport（响应式）
  if (!html.includes('viewport')) {
    html = html.replace(
      /<head>/i,
      '<head><meta name="viewport" content="width=device-width, initial-scale=1.0">'
    );
  }

  // 注入基础样式（防止溢出）
  const baseStyles = `<style>
    * { box-sizing: border-box; }
    body { margin: 0; padding: 16px; font-family: system-ui, -apple-system, sans-serif; }
    img { max-width: 100%; height: auto; }
    pre { overflow-x: auto; }
  </style>`;

  if (!html.includes('box-sizing')) {
    html = html.replace(/<\/head>/i, `${baseStyles}</head>`);
  }

  return html;
}

/**
 * 从内容中提取标题
 */
export function extractTitle(content: string): string {
  // 尝试从 markdown 标题中提取
  const titleMatch = content.match(/^#\s+(.+)$/m);
  if (titleMatch) {
    return titleMatch[1];
  }

  // 尝试从 HTML title 中提取
  const htmlTitleMatch = content.match(/<title>(.+?)<\/title>/i);
  if (htmlTitleMatch) {
    return htmlTitleMatch[1];
  }

  return '预览';
}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd agenthub/frontend && npx vitest run lib/__tests__/preview.test.ts`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add agenthub/frontend/lib/preview.ts agenthub/frontend/lib/__tests__/preview.test.ts
git commit -m "feat(preview): add HTML extraction and processing utilities"
```

---

## Task 2: 创建 PreviewToolbar 组件

**Files:**
- Create: `agenthub/frontend/components/chat/PreviewToolbar.tsx`
- Test: `agenthub/frontend/components/chat/__tests__/PreviewToolbar.test.tsx`

- [ ] **Step 1: 编写测试**

```typescript
// agenthub/frontend/components/chat/__tests__/PreviewToolbar.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PreviewToolbar } from '../PreviewToolbar';

describe('PreviewToolbar', () => {
  it('渲染标题', () => {
    render(
      <PreviewToolbar
        title="登录页面"
        onCollapse={vi.fn()}
        onRefresh={vi.fn()}
        onCopy={vi.fn()}
      />
    );
    expect(screen.getByText('登录页面')).toBeInTheDocument();
  });

  it('点击折叠按钮触发回调', () => {
    const onCollapse = vi.fn();
    render(
      <PreviewToolbar
        title="预览"
        onCollapse={onCollapse}
        onRefresh={vi.fn()}
        onCopy={vi.fn()}
      />
    );
    fireEvent.click(screen.getByLabelText('折叠'));
    expect(onCollapse).toHaveBeenCalled();
  });

  it('点击刷新按钮触发回调', () => {
    const onRefresh = vi.fn();
    render(
      <PreviewToolbar
        title="预览"
        onCollapse={vi.fn()}
        onRefresh={onRefresh}
        onCopy={vi.fn()}
      />
    );
    fireEvent.click(screen.getByLabelText('刷新'));
    expect(onRefresh).toHaveBeenCalled();
  });

  it('点击复制按钮触发回调', () => {
    const onCopy = vi.fn();
    render(
      <PreviewToolbar
        title="预览"
        onCollapse={vi.fn()}
        onRefresh={vi.fn()}
        onCopy={onCopy}
      />
    );
    fireEvent.click(screen.getByLabelText('复制'));
    expect(onCopy).toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd agenthub/frontend && npx vitest run components/chat/__tests__/PreviewToolbar.test.tsx`
Expected: FAIL with "Cannot find module '../PreviewToolbar'"

- [ ] **Step 3: 实现 PreviewToolbar**

```tsx
// agenthub/frontend/components/chat/PreviewToolbar.tsx
"use client";

interface PreviewToolbarProps {
  title: string;
  isCollapsed?: boolean;
  onCollapse: () => void;
  onRefresh: () => void;
  onCopy: () => void;
  onExpand?: () => void;
}

export function PreviewToolbar({
  title,
  isCollapsed = false,
  onCollapse,
  onRefresh,
  onCopy,
  onExpand,
}: PreviewToolbarProps) {
  return (
    <div className="flex items-center justify-between bg-gray-50 px-3 py-2 border-b border-gray-200">
      <div className="flex items-center gap-2">
        <span className="text-gray-400">🖥️</span>
        <span className="text-sm font-medium text-gray-700 truncate max-w-[200px]">
          {title}
        </span>
      </div>
      <div className="flex items-center gap-1">
        <button
          onClick={onCollapse}
          aria-label="折叠"
          className="p-1.5 rounded hover:bg-gray-200 text-gray-500 hover:text-gray-700 transition-colors"
          title={isCollapsed ? "展开" : "折叠"}
        >
          <svg
            className={`w-4 h-4 transition-transform ${isCollapsed ? '-rotate-90' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        <button
          onClick={onRefresh}
          aria-label="刷新"
          className="p-1.5 rounded hover:bg-gray-200 text-gray-500 hover:text-gray-700 transition-colors"
          title="刷新预览"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
        <button
          onClick={onCopy}
          aria-label="复制"
          className="p-1.5 rounded hover:bg-gray-200 text-gray-500 hover:text-gray-700 transition-colors"
          title="复制代码"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </button>
        {onExpand && (
          <button
            onClick={onExpand}
            aria-label="全屏"
            className="p-1.5 rounded hover:bg-gray-200 text-gray-500 hover:text-gray-700 transition-colors"
            title="全屏预览"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd agenthub/frontend && npx vitest run components/chat/__tests__/PreviewToolbar.test.tsx`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add agenthub/frontend/components/chat/PreviewToolbar.tsx agenthub/frontend/components/chat/__tests__/PreviewToolbar.test.tsx
git commit -m "feat(preview): add PreviewToolbar component"
```

---

## Task 3: 创建 PreviewFrame 组件

**Files:**
- Create: `agenthub/frontend/components/chat/PreviewFrame.tsx`
- Test: `agenthub/frontend/components/chat/__tests__/PreviewFrame.test.tsx`

- [ ] **Step 1: 编写测试**

```typescript
// agenthub/frontend/components/chat/__tests__/PreviewFrame.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { PreviewFrame } from '../PreviewFrame';

describe('PreviewFrame', () => {
  it('渲染 iframe', () => {
    const { container } = render(
      <PreviewFrame htmlCode="<div>Hello</div>" height={400} />
    );
    const iframe = container.querySelector('iframe');
    expect(iframe).toBeInTheDocument();
    expect(iframe?.getAttribute('sandbox')).toContain('allow-scripts');
  });

  it('处理 HTML 代码', () => {
    const { container } = render(
      <PreviewFrame htmlCode="<div>Test</div>" height={300} />
    );
    const iframe = container.querySelector('iframe');
    expect(iframe?.srcdoc).toContain('viewport');
    expect(iframe?.srcdoc).toContain('box-sizing');
  });

  it('设置正确的高度', () => {
    const { container } = render(
      <PreviewFrame htmlCode="<div>Hello</div>" height={500} />
    );
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.style.height).toBe('500px');
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd agenthub/frontend && npx vitest run components/chat/__tests__/PreviewFrame.test.tsx`
Expected: FAIL with "Cannot find module '../PreviewFrame'"

- [ ] **Step 3: 实现 PreviewFrame**

```tsx
// agenthub/frontend/components/chat/PreviewFrame.tsx
"use client";

import { useMemo } from "react";
import { processHtml } from "@/lib/preview";

interface PreviewFrameProps {
  htmlCode: string;
  height?: number;
}

export function PreviewFrame({ htmlCode, height = 400 }: PreviewFrameProps) {
  const processedHtml = useMemo(() => processHtml(htmlCode), [htmlCode]);

  return (
    <div className="relative bg-white" style={{ height }}>
      <iframe
        srcDoc={processedHtml}
        sandbox="allow-scripts allow-forms allow-modals"
        className="w-full h-full border-0"
        title="网页预览"
      />
    </div>
  );
}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd agenthub/frontend && npx vitest run components/chat/__tests__/PreviewFrame.test.tsx`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add agenthub/frontend/components/chat/PreviewFrame.tsx agenthub/frontend/components/chat/__tests__/PreviewFrame.test.tsx
git commit -m "feat(preview): add PreviewFrame component with sandbox"
```

---

## Task 4: 创建 PreviewCard 组件

**Files:**
- Create: `agenthub/frontend/components/chat/PreviewCard.tsx`
- Test: `agenthub/frontend/components/chat/__tests__/PreviewCard.test.tsx`

- [ ] **Step 1: 编写测试**

```typescript
// agenthub/frontend/components/chat/__tests__/PreviewCard.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PreviewCard } from '../PreviewCard';

describe('PreviewCard', () => {
  const mockHtml = '<html><body><div>Hello World</div></body></html>';

  it('渲染预览卡片', () => {
    render(<PreviewCard htmlCode={mockHtml} />);
    expect(screen.getByText('预览')).toBeInTheDocument();
    expect(screen.getByTitle('网页预览')).toBeInTheDocument();
  });

  it('显示自定义标题', () => {
    render(<PreviewCard htmlCode={mockHtml} title="登录页面" />);
    expect(screen.getByText('登录页面')).toBeInTheDocument();
  });

  it('支持折叠', () => {
    render(<PreviewCard htmlCode={mockHtml} />);
    const iframe = screen.getByTitle('网页预览');
    expect(iframe).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText('折叠'));
    expect(screen.queryByTitle('网页预览')).not.toBeInTheDocument();
  });

  it('支持刷新', () => {
    render(<PreviewCard htmlCode={mockHtml} />);
    const refreshBtn = screen.getByLabelText('刷新');
    expect(refreshBtn).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd agenthub/frontend && npx vitest run components/chat/__tests__/PreviewCard.test.tsx`
Expected: FAIL with "Cannot find module '../PreviewCard'"

- [ ] **Step 3: 实现 PreviewCard**

```tsx
// agenthub/frontend/components/chat/PreviewCard.tsx
"use client";

import { useState, useCallback } from "react";
import { PreviewToolbar } from "./PreviewToolbar";
import { PreviewFrame } from "./PreviewFrame";

interface PreviewCardProps {
  htmlCode: string;
  title?: string;
  height?: number;
  onExpand?: () => void;
}

export function PreviewCard({
  htmlCode,
  title = "预览",
  height = 400,
  onExpand,
}: PreviewCardProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleRefresh = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(htmlCode).catch(() => {
      // Fallback: 创建临时 textarea
      const textarea = document.createElement("textarea");
      textarea.value = htmlCode;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
    });
  }, [htmlCode]);

  return (
    <div className="rounded-lg border border-gray-200 overflow-hidden shadow-sm">
      <PreviewToolbar
        title={title}
        isCollapsed={isCollapsed}
        onCollapse={() => setIsCollapsed(!isCollapsed)}
        onRefresh={handleRefresh}
        onCopy={handleCopy}
        onExpand={onExpand}
      />
      {!isCollapsed && (
        <PreviewFrame key={refreshKey} htmlCode={htmlCode} height={height} />
      )}
    </div>
  );
}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd agenthub/frontend && npx vitest run components/chat/__tests__/PreviewCard.test.tsx`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add agenthub/frontend/components/chat/PreviewCard.tsx agenthub/frontend/components/chat/__tests__/PreviewCard.test.tsx
git commit -m "feat(preview): add PreviewCard component"
```

---

## Task 5: 集成到 MessageBubble

**Files:**
- Modify: `agenthub/frontend/components/chat/MessageBubble.tsx`

- [ ] **Step 1: 修改 MessageBubble**

在 `MessageBubble.tsx` 中添加预览功能：

```tsx
// agenthub/frontend/components/chat/MessageBubble.tsx
"use client";

import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import remarkGfm from "remark-gfm";
import { ClarificationCard } from "@/components/chat/ClarificationCard";
import { DiffViewer } from "@/components/chat/DiffViewer";
import { PreviewCard } from "@/components/chat/PreviewCard";
import { TaskPanel } from "@/components/chat/TaskPanel";
import { extractHtmlFromMarkdown, extractTitle } from "@/lib/preview";
import { useTaskStore } from "@/lib/stores/taskStore";
import type { Message } from "@/lib/types";

interface MessageBubbleProps {
  message: Message;
  isStreaming: boolean;
  onCopySuccess?: () => void;
}

export function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.type === "user";

  if (message.messageType === "task_panel") {
    const tasks = useTaskStore.getState().tasks;
    return (
      <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
        <div
          className={`max-w-[70%] rounded-2xl px-4 py-2 ${
            isUser
              ? "bg-primary text-white"
              : "bg-white text-gray-800 border border-gray-200"
          }`}
        >
          <TaskPanel tasks={tasks} />
        </div>
      </div>
    );
  }

  if (message.messageType === "clarification") {
    return (
      <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
        <div
          className={`max-w-[70%] rounded-2xl px-4 py-2 ${
            isUser
              ? "bg-primary text-white"
              : "bg-white text-gray-800 border border-gray-200"
          }`}
        >
          <ClarificationCard
            question={message.content}
            options={(message.metadata?.options as string[]) ?? []}
            onSelect={(option) => {
              window.dispatchEvent(
                new CustomEvent("clarification-select", {
                  detail: { option, messageId: message.id },
                }),
              );
            }}
          />
        </div>
      </div>
    );
  }

  if (message.messageType === "diff") {
    const meta = message.metadata ?? {};
    return (
      <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
        <div
          className={`max-w-[70%] rounded-2xl px-4 py-2 ${
            isUser
              ? "bg-primary text-white"
              : "bg-white text-gray-800 border border-gray-200"
          }`}
        >
          <DiffViewer
            filePath={(meta.file_path as string) ?? ""}
            oldContent={(meta.old_content as string) ?? ""}
            newContent={(meta.new_content as string) ?? ""}
          />
        </div>
      </div>
    );
  }

  // 检测是否包含可预览的 HTML
  const htmlCode = !isUser ? extractHtmlFromMarkdown(message.content) : null;

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[70%] rounded-2xl px-4 py-2 ${
          isUser
            ? "bg-primary text-white"
            : "bg-white text-gray-800 border border-gray-200"
        }`}
      >
        {!isUser && (
          <div className="text-xs font-medium text-gray-500 mb-1">
            {message.sender_name || message.sender}
          </div>
        )}
        <div className="prose prose-sm max-w-none">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeSanitize]}
          >
            {message.content}
          </ReactMarkdown>
        </div>
        {htmlCode && (
          <div className="mt-3">
            <PreviewCard
              htmlCode={htmlCode}
              title={extractTitle(message.content)}
              height={300}
            />
          </div>
        )}
        {isStreaming && (
          <span className="inline-block w-2 h-4 bg-current ml-1 animate-pulse" />
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 运行现有测试确认无破坏**

Run: `cd agenthub/frontend && npx vitest run`
Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/components/chat/MessageBubble.tsx
git commit -m "feat(preview): integrate PreviewCard into MessageBubble"
```

---

## Task 6: 更新 Agent Prompt

**Files:**
- Modify: `agenthub/backend/services/session.py`

- [ ] **Step 1: 添加预览规则到 Agent Prompt**

在 `session.py` 中为 Developer Agent 添加预览规则：

```python
# agenthub/backend/services/session.py

AGENT_CONFIGS: Dict[str, Dict[str, str]] = {
    # ... 其他 Agent ...
    "developer": {
        "name": "开发者",
        "role": "developer",
        "system_prompt": """你是一位资深全栈开发者。根据架构师的设计方案，编写高质量的代码实现。遵循 SOLID 原则，编写清晰、可维护的代码。输出代码时使用 markdown 代码块，标明文件路径和语言。

## 网页预览规则

当用户要求预览网页或生成前端代码时，必须遵循：

1. **自包含原则**：代码必须在 iframe 中独立运行
   - 所有依赖通过 CDN 引入（React、Vue、TailwindCSS 等）
   - 示例：<script src="https://cdn.tailwindcss.com"></script>

2. **模拟数据**：API 调用必须模拟
   - 使用 mock 函数模拟后端响应
   - 提供测试数据和提示信息

3. **标准格式**：使用 markdown 代码块
   ```html
   <!DOCTYPE html>
   <html>
   <!-- 完整代码 -->
   </html>
   ```

4. **用户体验**：
   - 页面必须有基本样式
   - 交互必须有反馈（loading、error、success）
   - 提供操作提示（如"测试账号: admin / 123456"）"""
    },
    # ... 其他 Agent ...
}
```

- [ ] **Step 2: 运行后端测试确认无破坏**

Run: `cd agenthub/backend && pytest`
Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
git add agenthub/backend/services/session.py
git commit -m "feat(preview): add preview rules to developer agent prompt"
```

---

## Task 7: 集成测试

**Files:**
- Test: 手动测试

- [ ] **Step 1: 启动后端**

```bash
cd agenthub/backend
python main.py
```

- [ ] **Step 2: 启动前端**

```bash
cd agenthub/frontend
npm run dev
```

- [ ] **Step 3: 测试预览功能**

1. 打开浏览器访问前端
2. 发送消息：`@developer 写一个简单的登录页面`
3. 确认 Agent 回复中包含 HTML 代码
4. 确认预览卡片正确显示
5. 测试折叠/展开功能
6. 测试刷新功能
7. 测试复制功能

- [ ] **Step 4: 测试边界情况**

1. 发送不含 HTML 的消息，确认不显示预览
2. 发送不完整的 HTML，确认能正确处理
3. 测试包含外部 CDN 的 HTML，确认能正确加载

- [ ] **Step 5: 最终提交**

```bash
git add -A
git commit -m "feat(preview): complete preview card feature"
```

---

## 验收检查清单

- [ ] Agent 生成的 HTML 代码能在聊天界面中正确预览
- [ ] 预览支持基本的用户交互（点击、输入、提交）
- [ ] 预览支持全屏、刷新、复制操作
- [ ] 安全限制有效，无法访问主页面
- [ ] 响应式布局正常
- [ ] 所有测试通过
- [ ] 无 TypeScript 错误

---

**Author:** Claude Code
**Last Updated:** 2026-05-31
