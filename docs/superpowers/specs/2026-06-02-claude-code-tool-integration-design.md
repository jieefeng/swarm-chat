# AgentHub Agent 工具执行能力设计

## 1. 背景与目标

### 1.1 问题

当前 AgentHub 的 Agent 系统是**纯文本 LLM 对话**——用户发消息，Agent 通过百炼/MiniMax 生成文字回复。Agent 无法：
- 读写项目文件
- 执行命令（运行测试、构建项目）
- 搜索代码库
- 使用用户配置的 Claude Code 生态（skills、MCP servers、rules）

### 1.2 目标

让 AgentHub 的 Agent 具备**工具执行能力**，能够调用用户本地的 Claude Code CLI 来完成开发任务，同时复用用户已有的 Claude Code 配置（skills、MCP、rules 等）。

### 1.3 成功标准

- Agent 能自动判断何时需要工具，并通过原生 tool_calls 调用 Claude Code
- 用户在 Agent 执行工具时能看到实时反馈（不是"假死"）
- 所有 Agent 统一拥有全量工具权限
- Agent 执行工具后能基于结果生成有意义的回复

## 2. 架构设计

### 2.1 整体架构

```
用户消息
  ↓
消息路由 (router.py) → @agent_name 解析
  ↓
SessionManager.send_to_agent_stream()
  ↓
LLM 调用（百炼/MiniMax）+ tools 参数
  ↓
LLM 响应
  ├─ content 有值，无 tool_calls → 直接流式返回
  └─ tool_calls 有值 → 工具执行流程
       ↓
       解析 tool_call → ClaudeCodeService
       ↓
       发送 SSE tool_start 事件 → 前端显示加载状态
       ↓
       claude CLI subprocess 执行
       ↓ stdout 逐行 → SSE tool_progress 事件
       ↓
       执行完毕 → SSE tool_result 事件
       ↓
       将 tool result 作为 tool message 发回 LLM
       ↓
       LLM 基于工具结果生成最终回复
       ↓
       流式返回给前端
```

### 2.2 核心组件

#### 2.2.1 ClaudeCodeService（新增）

**文件：** `agenthub/backend/services/claude_code_service.py`

**职责：**
- 封装 Claude Code CLI 的 subprocess 调用
- 支持流式输出（逐行读取 stdout）
- 超时控制
- 自动检测 CLI 是否安装
- 错误处理

**接口：**
```python
class ClaudeCodeService:
    def __init__(self, timeout: int = 300, max_turns: int = 10):
        self.timeout = timeout
        self.max_turns = max_turns

    def is_available(self) -> bool:
        """检测 Claude Code CLI 是否安装"""

    def execute(self, prompt: str, model: str = "", on_progress: Callable[[str], None] = None) -> ClaudeCodeResult:
        """
        执行 Claude Code CLI

        Args:
            prompt: 任务描述
            model: 指定模型（优先使用 Agent 配置，为空则用 CLI 默认）
            on_progress: 进度回调（stdout 逐行输出）

        Returns:
            ClaudeCodeResult(success, output, error, duration_ms)
        """

    async def execute_async(self, prompt: str, on_progress: Callable[[str], None] = None) -> ClaudeCodeResult:
        """异步版本，在事件循环中执行"""

@dataclass
class ClaudeCodeResult:
    success: bool
    output: str
    error: str = ""
    duration_ms: int = 0
```

**CLI 调用方式：**
```bash
claude -p "任务描述" --output-format stream-json --max-turns 10
```

- `--output-format stream-json`：流式 JSON 输出，便于逐行解析
- `--max-turns`：限制 Claude Code 内部轮数，防止无限循环
- `--model`：可选，指定模型
- `--allowedTools`：可选，限制工具范围（当前统一全量，不传此参数）

#### 2.2.2 Tool 定义（修改 LLM 调用）

**文件：** `agenthub/backend/services/llm_router.py` 或新增 `agenthub/backend/services/tools.py`

```python
CLAUDE_CODE_TOOL = {
    "type": "function",
    "function": {
        "name": "claude_code",
        "description": (
            "调用 Claude Code CLI 执行开发任务。可用于："
            "读取/写入/编辑文件、搜索代码、执行命令（如运行测试、构建项目）、"
            "分析项目结构等。适用于需要访问文件系统或执行操作的场景。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "要 Claude Code 执行的具体任务描述，应清晰明确"
                }
            },
            "required": ["prompt"]
        }
    }
}
```

#### 2.2.3 SessionManager 改造（修改）

**文件：** `agenthub/backend/services/session.py`

**改动点：**
- `send_to_agent_stream()` 增加工具调用循环
- 支持多轮 tool_calls（LLM 可能连续调用多个工具）
- 通过回调函数发送 SSE 事件
- `thread_id` 参数透传，用于 SSE 事件路由（与 A2A Threads 对齐）
- Claude Code 的 `--model` 参数优先使用 Agent 配置的模型（与 Model Selection 对齐）

```python
def send_to_agent_stream(
    self,
    agent_id: str,
    message: str,
    message_history: list[dict] = None,
    thread_id: str | None = None,  # 新增：线程 ID，用于 SSE 路由
    on_tool_start: Callable[[str, str], None] = None,
    on_tool_progress: Callable[[str, str], None] = None,
    on_tool_result: Callable[[str, str, bool], None] = None,
) -> Iterator[str]:
    """流式发送消息，支持 tool_calls 循环"""
```

**核心逻辑：**
```python
from .claude_code_service import claude_code_service
from .llm_config_db import LLMConfigDB

db = LLMConfigDB()

# Claude Code 的模型优先使用 Agent 配置，回退到环境变量
cc_model = db.get_model(agent_id) or os.getenv("CLAUDE_CODE_MODEL", "")

# 1. 第一次 LLM 调用（带 tools，仅当 Claude Code 可用时）
tools = [CLAUDE_CODE_TOOL] if claude_code_service.is_available() else None
response = llm.send_message_stream(
    messages=messages,
    tools=tools,
    tool_choice="auto" if tools else None
)

# 2. 如果有 tool_calls，执行工具
if response.tool_calls:
    for tool_call in response.tool_calls:
        prompt = tool_call.function.arguments["prompt"]

        # 发送 tool_start 事件（带 thread_id）
        on_tool_start(agent_id, prompt, thread_id=thread_id)

        # 执行 Claude Code（使用 Agent 配置的模型）
        result = claude_code_service.execute(
            prompt,
            model=cc_model,
            on_progress=lambda output: on_tool_progress(
                agent_id, output, thread_id=thread_id
            )
        )

        # 发送 tool_result 事件（带 thread_id）
        on_tool_result(agent_id, result.output, result.success, thread_id=thread_id)

        # 将 tool result 添加到 messages
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result.output
        })

    # 3. 带 tool results 再次调用 LLM
    final_response = llm.send_message_stream(messages=messages)
    yield from final_response
```

#### 2.2.4 SSE 事件扩展（修改）

**文件：** `agenthub/backend/services/sse_manager.py`

新增事件类型（所有事件必须携带 `thread_id`，与 A2A Threads 的 SSE 过滤机制对齐）：

```python
async def broadcast_tool_start(self, agent_id: str, command: str,
                                message_id: str, thread_id: str | None = None):
    """广播工具开始执行事件"""
    await self.broadcast({
        "type": "tool_start",
        "agent_id": agent_id,
        "command": command,
        "message_id": message_id,
    }, thread_id=thread_id)

async def broadcast_tool_progress(self, agent_id: str, output: str,
                                   message_id: str, thread_id: str | None = None):
    """广播工具执行进度"""
    await self.broadcast({
        "type": "tool_progress",
        "agent_id": agent_id,
        "output": output,
        "message_id": message_id,
    }, thread_id=thread_id)

async def broadcast_tool_result(self, agent_id: str, content: str, success: bool,
                                 message_id: str, thread_id: str | None = None):
    """广播工具执行结果"""
    await self.broadcast({
        "type": "tool_result",
        "agent_id": agent_id,
        "content": content,
        "success": success,
        "message_id": message_id,
    }, thread_id=thread_id)
```

### 2.3 前端改动

#### 2.3.1 SSE 事件处理（修改）

**文件：** `agenthub/frontend/lib/hooks/useChatStream.ts`

增加对新事件类型的处理：

```typescript
case "tool_start":
  addToolExecution({
    id: data.message_id,
    command: data.command,
    status: "running",
  });
  break;

case "tool_progress":
  updateToolExecutionOutput(data.message_id, data.output);
  break;

case "tool_result":
  updateToolExecutionResult(data.message_id, data.content, data.success);
  break;
```

#### 2.3.2 消息展示（修改）

**文件：** `agenthub/frontend/components/chat/MessageBubble.tsx`

增加工具执行状态的展示组件：

```tsx
{toolExecutions.map(tool => (
  <ToolExecutionCard
    key={tool.id}
    command={tool.command}
    status={tool.status}
    output={tool.output}
  />
))}
```

**ToolExecutionCard 组件：**
- `running` 状态：显示加载动画 + 命令描述
- `success` 状态：显示可折叠的工具输出
- `error` 状态：显示错误信息

#### 2.3.3 Store 扩展（修改）

**文件：** `agenthub/frontend/lib/stores/messageStore.ts`

```typescript
interface ToolExecution {
  id: string;
  command: string;
  status: "running" | "success" | "error";
  output?: string;
}

interface MessageState {
  // ... 现有字段
  toolExecutions: Map<string, ToolExecution[]>;
  addToolExecution: (msgId: string, tool: ToolExecution) => void;
  updateToolExecution: (msgId: string, toolId: string, update: Partial<ToolExecution>) => void;
}
```

## 3. LLM 交互协议

### 3.1 工具调用流程

```
# 第一轮：用户消息 + 工具定义
→ {
    messages: [
      {role: "system", content: "你是资深开发者..."},
      {role: "user", content: "帮我看看 src/main.py 的内容"}
    ],
    tools: [CLAUDE_CODE_TOOL],
    tool_choice: "auto"
  }

# LLM 响应：决定调用工具
← {
    choices: [{
      message: {
        role: "assistant",
        content: null,
        tool_calls: [{
          id: "call_abc123",
          type: "function",
          function: {
            name: "claude_code",
            arguments: '{"prompt": "读取 src/main.py 的完整内容"}'
          }
        }]
      }
    }]
  }

# 第二轮：工具结果回传
→ {
    messages: [
      {role: "system", content: "..."},
      {role: "user", content: "帮我看看 src/main.py 的内容"},
      {role: "assistant", tool_calls: [...]},
      {role: "tool", tool_call_id: "call_abc123", content: "文件内容..."}
    ],
    tools: [CLAUDE_CODE_TOOL],
    tool_choice: "auto"
  }

# LLM 最终回复
← {
    choices: [{
      message: {
        role: "assistant",
        content: "src/main.py 的内容如下：\n\n```python\n...\n```\n\n这是一个 FastAPI 入口文件..."
      }
    }]
  }
```

### 3.2 多工具调用

LLM 可能在一次响应中返回多个 tool_calls：

```json
{
  "tool_calls": [
    {"id": "call_1", "function": {"name": "claude_code", "arguments": "{\"prompt\": \"读取 src/main.py\"}"}},
    {"id": "call_2", "function": {"name": "claude_code", "arguments": "{\"prompt\": \"读取 src/config.py\"}"}}
  ]
}
```

**处理方式：** 串行执行（避免并发 subprocess 资源竞争），每个工具执行期间发送独立的 tool_start/tool_progress/tool_result 事件。

### 3.3 工具调用深度限制

为防止无限循环（LLM 反复调用工具），设置最大工具调用轮数：
- 默认：3 轮（即 LLM 最多连续调用 3 次工具）
- 可通过环境变量 `CLAUDE_CODE_MAX_ROUNDS` 配置

## 4. 配置项

### 4.1 环境变量

```bash
# Claude Code 工具配置
CLAUDE_CODE_ENABLED=true          # 是否启用 Claude Code 工具（默认 true）
CLAUDE_CODE_TIMEOUT=300           # 超时时间秒（默认 300）
CLAUDE_CODE_MODEL=""              # 全局默认模型（Agent 配置优先于此值）
CLAUDE_CODE_MAX_TURNS=10          # Claude Code 内部最大轮数（默认 10）
CLAUDE_CODE_MAX_ROUNDS=3          # Agent 与工具交互的最大轮数（默认 3）
```

**模型优先级（从高到低）：**
1. Agent 数据库配置（`agent_llm_config.model`）— 通过 Model Selection 模块设置
2. 环境变量 `CLAUDE_CODE_MODEL` — 全局回退值
3. Claude Code CLI 默认模型

### 4.2 Agent 配置

在 `AGENT_CONFIGS` 中增加 `tools_enabled` 字段：

```python
AGENT_CONFIGS = {
    "pm": {
        "name": "苍龙",
        "tools_enabled": True,
        # ... 其他配置
    },
}
```

## 5. 错误处理

| 场景 | 检测方式 | 处理 |
|------|---------|------|
| Claude Code CLI 未安装 | `claude --version` 返回非 0 | 返回友好错误提示，附安装链接 |
| 执行超时 | subprocess 超过 timeout | 终止进程，返回超时错误 |
| 执行失败 | subprocess 返回非 0 | 返回 stderr 内容 |
| LLM 不支持 tool_calls | 响应中无 tool_calls 字段 | 降级为纯文本回复，提示用户 |
| 工具调用无限循环 | 超过 MAX_ROUNDS | 强制停止，返回已执行结果 |
| JSON 解析失败 | arguments 非法 JSON | 跳过该 tool_call，记录日志 |

### 5.1 CLI 未安装时的降级

```python
def send_to_agent_stream(self, agent_id, message, ...):
    tools = [CLAUDE_CODE_TOOL] if claude_code_service.is_available() else None

    response = llm.send_message_stream(
        messages=messages,
        tools=tools,  # None 时不传 tools 参数
        tool_choice="auto" if tools else None
    )
```

## 6. 测试计划

### 6.1 单元测试

- `test_claude_code_service.py`：CLI 检测、执行、超时、错误处理
- `test_tool_calls.py`：tool_call 解析、结果回传、多轮循环

### 6.2 集成测试

- 端到端：用户消息 → Agent 决定调用工具 → 执行 → 返回结果
- 降级测试：CLI 未安装时的纯文本回复

### 6.3 前端测试

- SSE 事件处理：tool_start、tool_progress、tool_result
- ToolExecutionCard 组件渲染

## 7. 安全考虑

### 7.1 工具权限

当前设计：**所有 Agent 统一全量工具权限**。这意味着 Agent 可以：
- 读写项目中的任何文件
- 执行任意命令
- 访问用户的 Claude Code 配置

**风险缓解：**
- Claude Code CLI 本身有安全机制（权限确认、沙箱）
- 四条铁律（HARD_RAILS）仍然生效
- 未来可按 Agent 角色限制 `--allowedTools`

### 7.2 输入验证

- `prompt` 参数必须为非空字符串
- 长度限制：最大 10000 字符
- 过滤危险命令模式（如 `rm -rf /`）—— 依赖 Claude Code 自身安全机制

## 8. 依赖

### 8.1 系统依赖

- Claude Code CLI 已安装（`npm install -g @anthropic-ai/claude-code` 或等效方式）
- Node.js 运行时（Claude Code CLI 依赖）

### 8.2 Python 依赖

无新增依赖，使用标准库 `subprocess`、`asyncio`。

### 8.3 前端依赖

无新增依赖。

## 9. 里程碑

### Phase 1：后端核心
- 实现 `ClaudeCodeService`（`claude_code_service.py`）
- 修改 `SessionManager` 支持 tool_calls 循环 + `thread_id` 透传
- 扩展 SSE 事件类型（带 `thread_id`）
- 集成 Agent 模型配置（`db.get_model()` → `--model` 参数）
- 单元测试

### Phase 2：前端集成
- 处理新 SSE 事件（tool_start/tool_progress/tool_result）
- 实现 `ToolExecutionCard` 组件
- 更新 `messageStore` 增加 `ToolExecution` 状态

### Phase 3：优化与稳定
- 错误处理完善
- 超时和重试机制
- 性能优化（subprocess 复用）
- 文档更新

## 10. 已有基础设施

以下组件已在项目中实现，本模块直接复用，无需额外前置依赖。

### 10.1 SSE 线程过滤（已实现）

`sse_manager.broadcast(event_type, data, thread_id=...)` 已支持按 `thread_id` 过滤投递。本模块的工具事件直接传入 `thread_id` 即可。

### 10.2 Agent 模型配置（已实现）

`llm_config_db.get_model(agent_id)` 和 `update_model()` 已实现。Claude Code 的 `--model` 参数直接调用 `db.get_model()` 获取。

### 10.3 消息路由的 thread_id（已实现）

`SendMessageRequest.thread_id` 已存在（默认 "default"），`messages.py` 中的 `send_to_single_agent()` 已将 `thread_id` 透传给 `memory.add_message()` 和 `sse_manager.broadcast()`。

## 11. 开放问题

- [ ] Claude Code CLI 是否支持通过 API token 直接调用（不依赖本地登录）？
- [ ] 百炼 API 的 tool_calls 响应格式是否与 OpenAI 完全兼容？需要实测验证
- [ ] 是否需要支持 Claude Code 的 `--resume` 参数（续接之前的会话）？
- [ ] 前端是否需要展示 Claude Code 的中间执行步骤（如文件读取、命令执行的详细过程）？
- [x] 工具事件的 `thread_id` 透传 → SSE 已支持，直接传入即可
- [x] Claude Code 模型与 Agent 模型配置对齐 → `llm_config_db.get_model()` 已实现
