# 网页预览功能设计规范

**日期：** 2026-05-31
**版本：** v1.0
**状态：** 设计定稿

---

## 1. 背景与目标

### 1.1 设计背景

AgentHub 已实现基础 IM 聊天功能和 Orchestrator 协调器，但缺乏比赛要求的"网页预览"功能。用户在与 Agent 协作时，无法直接在聊天界面中预览 Agent 生成的网页代码效果，需要复制代码到外部工具才能查看。

### 1.2 设计目标

- 在聊天界面中直接预览 Agent 生成的网页代码
- 支持自包含的 HTML/CSS/JS 代码渲染
- 提供良好的用户体验（全屏、刷新、复制）
- 确保安全性（sandbox 限制）

### 1.3 约束条件

- 纯前端实现，无需后端改动
- 复用现有 SSE 通道
- 代码必须在 iframe 中独立运行
- 所有依赖通过 CDN 引入

---

## 2. 整体架构

### 2.1 架构概览

```
用户请求预览 → Agent 生成自包含 HTML → 前端提取代码 → PreviewCard 渲染 → iframe 沙箱展示
```

### 2.2 核心组件

| 组件 | 职责 | 文件路径 |
|------|------|----------|
| PreviewCard | 预览卡片主组件 | frontend/components/chat/PreviewCard.tsx |
| PreviewFrame | iframe 沙箱 | frontend/components/chat/PreviewFrame.tsx |
| PreviewToolbar | 工具栏 | frontend/components/chat/PreviewToolbar.tsx |
| preview.ts | HTML 提取和处理工具 | frontend/lib/preview.ts |

---

## 3. 组件设计

### 3.1 PreviewCard 组件

```tsx
interface PreviewCardProps {
  htmlCode: string;           // HTML 代码字符串
  title?: string;             // 预览标题
  height?: number;            // 预览高度（默认 400px）
  onExpand?: () => void;      // 全屏回调
}
```

**功能：**
- 渲染预览卡片容器
- 管理折叠/展开状态
- 提供工具栏操作

### 3.2 PreviewFrame 组件

```tsx
interface PreviewFrameProps {
  htmlCode: string;
  height: number;
}
```

**功能：**
- 渲染 iframe 沙箱
- 处理 HTML 注入（viewport、基础样式）
- 管理加载状态和错误处理

### 3.3 PreviewToolbar 组件

**功能：**
- 显示预览标题
- 提供全屏/刷新/复制按钮
- 折叠/展开控制

### 3.4 HTML 处理工具

```tsx
// 从 markdown 中提取 HTML
export function extractHtmlFromMarkdown(content: string): string | null

// 处理 HTML：注入 viewport、基础样式
export function processHtml(htmlCode: string): string
```

---

## 4. 安全设计

### 4.1 sandbox 属性

```tsx
sandbox="allow-scripts allow-forms allow-modals"
```

| 属性 | 说明 | 风险 |
|------|------|------|
| allow-scripts | 允许执行 JS | 低 |
| allow-forms | 允许表单提交 | 低 |
| allow-modals | 允许 alert/confirm | 低 |
| allow-same-origin | 禁止 | 防止访问主页面 |
| allow-popups | 禁止 | 防止弹窗 |
| allow-top-navigation | 禁止 | 防止跳转 |

### 4.2 HTML 处理

- 注入 meta viewport（响应式）
- 注入基础 CSS 重置（防止溢出）
- 确保有基本的 HTML 结构

---

## 5. 集成设计

### 5.1 消息气泡集成

```tsx
// MessageBubble.tsx
export function MessageBubble({ message }: MessageBubbleProps) {
  const htmlCode = extractHtmlFromMarkdown(message.content);

  return (
    <div className="message-bubble">
      <Markdown content={message.content} />
      {htmlCode && (
        <PreviewCard htmlCode={htmlCode} title={extractTitle(message.content)} />
      )}
    </div>
  );
}
```

### 5.2 Agent Prompt 设计

在 Agent 的 system_prompt 中加入预览指令：

```
## 网页预览规则

当用户要求预览网页或生成前端代码时，必须遵循：

1. **自包含原则**：代码必须在 iframe 中独立运行
   - 所有依赖通过 CDN 引入
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
   - 交互必须有反馈
   - 提供操作提示
```

---

## 6. 实现计划

### 6.1 优先级

| 阶段 | 功能 | 时间 |
|------|------|------|
| P0 | PreviewCard + PreviewFrame 基础组件 | 2h |
| P0 | HTML 提取和处理 | 1h |
| P0 | 集成到 MessageBubble | 1h |
| P1 | 工具栏（全屏/刷新/复制） | 1h |
| P1 | Agent Prompt 优化 | 0.5h |
| P2 | 全屏模式 | 1h |
| P2 | 多预览标签页 | 2h |

### 6.2 文件变更清单

**新增文件：**
- frontend/components/chat/PreviewCard.tsx
- frontend/components/chat/PreviewFrame.tsx
- frontend/components/chat/PreviewToolbar.tsx
- frontend/lib/preview.ts

**修改文件：**
- frontend/components/chat/MessageBubble.tsx
- backend/services/session.py（Agent Prompt）

---

## 7. 技术决策

| 问题 | 决策 |
|------|------|
| 实现方式 | 纯前端 iframe，无需后端改动 |
| 安全策略 | sandbox 限制，禁止 allow-same-origin |
| 依赖管理 | Agent 生成自包含代码，CDN 引入 |
| 数据模拟 | Agent 使用 mock 函数 |
| 样式处理 | 注入基础 CSS 重置 |

---

## 8. 验收标准

- [ ] Agent 生成的 HTML 代码能在聊天界面中正确预览
- [ ] 预览支持基本的用户交互（点击、输入、提交）
- [ ] 预览支持全屏、刷新、复制操作
- [ ] 安全限制有效，无法访问主页面
- [ ] 响应式布局正常

---

**Author:** Claude Code
**Last Updated:** 2026-05-31
