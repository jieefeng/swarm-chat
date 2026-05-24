# @Agent Mention 下拉菜单设计

## 概述

在消息输入框中实现 @mention 自动完成功能，当用户输入 `@` 时显示 Agent 列表供选择。

## 交互行为

| 行为 | 设计 |
|------|------|
| 触发 | 输入 `@` 立即显示下拉菜单 |
| 过滤 | 实时根据输入过滤 Agent 名称 |
| 选中 | 点击/回车插入 `@产品经理 ` 到光标位置 |
| 关闭 | 点击外部或按 ESC 关闭 |
| 空状态 | 显示"无匹配Agent" |

## 界面规格

| 元素 | 设计 |
|------|------|
| 菜单位置 | 输入框下方，紧贴 |
| 菜单宽度 | 与输入框等宽 |
| 列表项高度 | 48px |
| 最大显示数 | 5个（超出滚动） |
| 背景色 | 白色 + 阴影 |
| 选中高亮 | 浅蓝背景 |

## 数据结构

```typescript
interface MentionOption {
  id: string;        // "pm"
  name: string;      // "产品经理"
  role: string;      // "产品经理（PM）"
}
```

## 组件结构

```
MessageInput
  └── div (position-relative)
        ├── input
        └── {isMentioning && <MentionDropdown
              options={filteredAgents}
              onSelect={handleSelect}
            />}
```

## 实现文件

- `agenthub/frontend/components/chat/MentionDropdown.tsx` - 新增下拉菜单组件
- `agenthub/frontend/components/chat/MessageInput.tsx` - 修改添加 mention 逻辑

## 依赖

- 使用 `useRef` 获取 input DOM 元素
- 使用 `useState` 管理下拉菜单状态
- Agent 数据从父组件通过 props 传入