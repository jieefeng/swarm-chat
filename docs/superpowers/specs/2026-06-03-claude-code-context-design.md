# Claude Code 上下文传递设计

## 1. 背景与目标

### 1.1 问题

当前 Claude Code 工具调用时，`prompt` 只包含 LLM 解析出来的工具参数（如"读取 main.py"），没有包含聊天历史。这导致：

- Claude Code 不知道之前的对话内容
- 无法基于上下文做出更准确的判断
- 每次调用都是"无状态"的

### 1.2 目标

让 Claude Code 每次调用时都能看到：
1. **完整的聊天历史** - 用户和 Agent 之间的所有对话

### 1.3 成功标准

- Claude Code 能看到完整的聊天上下文
- 改动最小化，不影响现有功能
- 保持代码职责清晰

## 2. 设计方案

### 2.1 数据流

```
messages.py:
  context = memory.get_messages(...)  # 完整聊天历史
  ↓
  session_manager.send_to_agent_stream(
      agent_id,
      agent_message,
      context=context,  # 新增参数
      ...
  )
  ↓
session.py:
  # 拼接到 prompt 前面
  full_prompt = f"{context}\n\n{prompt}" if context else prompt
  ↓
  claude_code_service.execute(full_prompt, ...)
  ↓
  claude -p "完整历史 + 工具参数"
```

### 2.2 上下文格式

```text
[user]: 帮我看看 main.py 的内容
[pm]: 好的，我来看看...
[user]: 然后帮我修改第 10 行
```

格式说明：
- 使用 `[role]: content` 格式（与现有 `get_context_for_agent` 一致）
- 包含完整聊天历史（不限制长度）

### 2.3 关键决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 上下文范围 | 完整历史 | 用户选择，不限制长度 |
| 传递方式 | 拼接到 prompt 前面 | 简单直接 |
| 历史格式 | `[role]: content` | 与现有格式一致 |
| 截断策略 | 不限制 | 用户选择，先不处理 |
| Token 统计 | 暂不做 | Claude Code CLI 不返回 token 使用量 |

## 3. 改动详情

### 3.1 messages.py 改动

```python
# 现有代码（第 251-252 行）
context = await memory.get_context_for_agent(agent_id, user_id=req.user_id, thread_id=req.thread_id)
agent_message = f"上下文参考:\n{context}\n\n用户消息: {route_result['content']}" if context else route_result['content']

# 新增：获取完整历史
full_history = await memory.get_messages(user_id=req.user_id, thread_id=req.thread_id)

# 新增：格式化完整历史
history_parts = []
for msg in full_history:
    role = msg.get('role', 'unknown')
    content = msg.get('content', '')
    history_parts.append(f"[{role}]: {content}")
history_text = "\n".join(history_parts)

# 传给 session_manager
for chunk in session_manager.send_to_agent_stream(
    agent_id,
    agent_message,
    context=history_text,  # 新增参数
    thread_id=req.thread_id,
    ...
):
```

### 3.2 session.py 改动

```python
# send_to_agent_stream 方法签名
def send_to_agent_stream(
    self,
    agent_id: str,
    message: str,
    context: str = "",  # 新增参数
    message_history: list[dict] | None = None,
    thread_id: str | None = None,
    on_tool_start: Callable | None = None,
    on_tool_progress: Callable | None = None,
    on_tool_result: Callable | None = None,
) -> Iterator[str]:
    """流式发送消息到指定Agent，支持 tool_calls 循环"""

    # ... 现有代码 ...

    # 工具调用时，拼接上下文
    for tc_id, tc_info in tool_calls_map.items():
        try:
            prompt = json.loads(tc_info["arguments"]).get("prompt", "")
        except (json.JSONDecodeError, AttributeError):
            yield f"\n[错误: 无法解析 tool_call 参数]\n"
            continue

        if not prompt:
            continue

        # 新增：拼接上下文到 prompt
        full_prompt = f"{context}\n\n{prompt}" if context else prompt

        if on_tool_start:
            on_tool_start(agent_id, full_prompt, thread_id=thread_id)

        result = claude_code_service.execute(
            full_prompt,  # 使用拼接后的 prompt
            model=cc_model,
            on_progress=(lambda output: on_tool_progress(agent_id, output, thread_id=thread_id))
            if on_tool_progress
            else None,
        )
```

## 4. 潜在风险与缓解

### 4.1 Prompt 过长

**风险：** 如果聊天历史很长，Claude Code 响应会变慢，token 成本增加。

**缓解：** 用户选择不限制长度。如果后续发现性能问题，可以加截断策略：
```python
# 可选：限制历史长度
max_history_chars = 10000
if len(history_text) > max_history_chars:
    history_text = history_text[-max_history_chars:]
```

### 4.2 重复信息

**风险：** LLM 已经看到上下文，Claude Code 再看一遍，信息重复。

**缓解：** 这是用户的选择，确保 Claude Code 有完整上下文。重复信息不会导致功能问题，只是 token 浪费。

### 4.3 工具结果膨胀

**风险：** 如果工具结果加入聊天历史，下次调用时上下文会包含之前的结果，导致 prompt 膨胀。

**缓解：** 用户选择工具结果不加入聊天历史，保持上下文简洁。

## 5. 测试计划

### 5.1 单元测试

- 测试 `send_to_agent_stream` 的 `context` 参数
- 测试 prompt 拼接逻辑

### 5.2 集成测试

- 启动后端，发送消息，观察 Claude Code 是否能看到上下文
- 多轮对话测试，验证上下文传递

### 5.3 前端测试

- 无前端改动，不需要测试

## 6. 依赖

无新增依赖。

## 7. 里程碑

### Phase 1：后端改动

- [ ] 修改 `messages.py`，获取完整历史
- [ ] 修改 `session.py`，新增 `context` 参数
- [ ] 测试上下文传递

### Phase 2：验证

- [ ] 启动后端，发送消息，观察 Claude Code 响应
- [ ] 确认 Claude Code 能看到完整上下文
