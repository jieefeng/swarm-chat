# AgentHub MVP 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个IM聊天式多Agent协作平台，支持@指令触发、消息广播、SSE实时推送

**Architecture:** 前端Next.js，后端FastAPI，通信HTTP POST + SSE

**Tech Stack:** Next.js 14 + TypeScript + TailwindCSS + shadcn/ui | FastAPI + Python + SSE

---

## 用户故事

## 用户故事：@指令触发Agent

**用户角色**：作为 用户
**使用场景**：我希望在群聊中指定某个Agent进行沟通时
**达成目标**：能够 通过@指令（如@pm、@architect）触发特定Agent响应
**核心价值**：以便 获得特定角色专家的精准回复，避免广播式噪音

**验收标准**：
1. 输入 `@pm 请分析需求` 时，只有PM Agent响应
2. 输入 `@architect 架构设计` 时，只有Architect Agent响应
3. @指令格式为 `@agentID 内容`，正则匹配 `^@(\w+)\s+(.*)$`
4. @指令后跟随的内容作为消息本体发送给目标Agent
5. 未匹配的agentID当作普通消息处理

**优先级**：Must

---

## 用户故事：消息广播

**用户角色**：作为 用户
**使用场景**：我希望向所有Agent同时提问时
**达成目标**：能够 在不使用@指令时，消息自动广播给所有Agent
**核心价值**：以便 高效收集多专家意见，适合需求评审和头脑风暴场景

**验收标准**：
1. 无@指令的消息同时触发所有已配置的Agent
2. 广播模式下所有Agent并行处理，互不阻塞
3. 各Agent响应通过SSE实时推送展示
4. 响应顺序不固定，由处理速度决定
5. 返回结果中 `is_broadcast: true` 标识广播消息

**优先级**：Must

---

## 用户故事：SSE实时推送

**用户角色**：作为 前端界面
**使用场景**：我希望在新消息到达时无需轮询即可实时显示
**达成目标**：能够 通过SSE（Server-Sent Events）接收后端推送的实时消息
**核心价值**：以便 用户体验流畅的即时通讯效果，消息秒级可见

**验收标准**：
1. 前端通过 `GET /api/events` 建立SSE连接
2. 用户发送消息后，立即通过SSE推送用户消息到前端
3. Agent响应完成后，通过SSE推送Agent消息到前端
4. 终止信号通过 `termination` 事件类型推送
5. SSE连接断开时自动重连

**优先级**：Must

---

## 用户故事：终止关键词检测

**用户角色**：作为 系统
**使用场景**：我希望在人机交互中识别终止讨论的信号
**达成目标**：能够 检测消息中的终止关键词（如"结束讨论"、"确认方案"）并触发终止流程
**核心价值**：以便 在讨论达成共识或有明确结论时，优雅地结束当前话题

**验收标准**：
1. 支持的终止关键词列表：`["结束讨论", "开始实现", "确认方案", "重新讨论"]`
2. 检测到终止关键词后，触发 `termination` SSE事件
3. 终止事件包含 `keyword` 和 `message_id` 字段
4. 前端收到终止事件后弹出提示
5. 终止关键词匹配为包含匹配，不需完全一致

**优先级**：Should

---

## 用户故事：消息历史查询

**用户角色**：作为 前端界面
**使用场景**：我希望页面加载时能获取历史消息记录
**达成目标**：能够 通过 `GET /api/messages` 和 `GET /api/agents` 查询历史消息和Agent列表
**核心价值**：以便 用户刷新页面或重新连接时，能恢复完整的对话上下文

**验收标准**：
1. `GET /api/messages` 返回消息列表，按时间戳升序排列
2. `GET /api/messages?limit=N` 支持限制返回消息数量，默认50条
3. `GET /api/agents` 返回已配置的Agent列表（id、name、role）
4. 消息结构包含：`id`, `sender`, `sender_name`, `content`, `timestamp`, `type`
5. Agent结构包含：`id`, `name`, `role`

**优先级**：Should

---

## 文件结构

```
agenthub/
├── backend/
│   ├── main.py                    # FastAPI入口
│   ├── requirements.txt           # Python依赖
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── messages.py            # POST /api/messages, GET /api/messages, GET /api/agents
│   │   └── events.py              # GET /api/events (SSE)
│   └── services/
│       ├── __init__.py
│       ├── router.py              # @指令解析 + 广播
│       ├── session.py             # Agent会话管理
│       ├── memory.py              # 共享上下文
│       └── claude.py              # Claude API适配
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   └── MessageInput.tsx
│   │   └── agents/
│   │       └── AgentList.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   └── types.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── next.config.js
└── README.md
```

---

## Task 1: 后端基础 - FastAPI + SSE

**Files:**
- Create: `agenthub/backend/requirements.txt`
- Create: `agenthub/backend/main.py`
- Create: `agenthub/backend/models/__init__.py`
- Create: `agenthub/backend/models/message.py`

**验收标准：**
- [ ] `requirements.txt` 包含 fastapi、uvicorn、anthropic、pydantic、python-dotenv、sse-starlette
- [ ] `main.py` 包含 FastAPI 初始化和 CORS 中间件配置
- [ ] `main.py` 包含 `/` 和 `/health` 端点
- [ ] `models/message.py` 包含 Message 和 SendMessageRequest 模型定义
- [ ] `models/`, `routers/`, `services/` 目录包含 `__init__.py` 空文件
- [ ] 项目可通过 `python main.py` 启动，监听 0.0.0.0:8000

- [ ] **Step 1: 创建依赖文件**

```txt
# agenthub/backend/requirements.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
anthropic==0.18.0
pydantic==2.5.3
python-dotenv==1.0.0
sse-starlette==1.8.2
```

- [ ] **Step 2: 创建消息模型**

```python
# agenthub/backend/models/message.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Message(BaseModel):
    id: str
    sender: str          # agent ID: "pm", "architect", "user"
    sender_name: str     # 显示名称
    content: str         # 消息内容
    timestamp: int       # Unix时间戳
    type: str            # "user" | "agent"

class SendMessageRequest(BaseModel):
    content: str
    sender: str = "user"
    sender_name: str = "用户"
```

- [ ] **Step 3: 创建主入口**

```python
# agenthub/backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="AgentHub API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
from routers import messages, events
app.include_router(messages.router)
app.include_router(events.router)

@app.get("/")
async def root():
    return {"message": "AgentHub API", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 4: 创建 __init__ 文件**

```python
# agenthub/backend/models/__init__.py
# agenthub/backend/routers/__init__.py
# agenthub/backend/services/__init__.py
# 空文件，标记为Python包
```

- [ ] **Step 5: 提交**

```bash
cd agenthub
git init
git add -A
git commit -m "feat: backend project structure and FastAPI setup"
```

---

## Task 2: Claude Adapter

**Files:**
- Create: `agenthub/backend/services/claude.py`

**验收标准：**
- [ ] `ClaudeAdapter` 类包含 `create_session` 方法，使用 `anthropic.Anthropic` 创建会话
- [ ] `create_session` 返回包含 `session_id` 和 `model` 的字典
- [ ] `send_message` 方法发送消息到指定会话，返回响应文本
- [ ] 使用环境变量 `ANTHROPIC_API_KEY` 配置API Key
- [ ] 默认模型为 `claude-sonnet-4-20250514`
- [ ] 模块导出单例 `claude_adapter` 供其他服务使用

- [ ] **Step 1: 编写Claude适配器**

```python
# agenthub/backend/services/claude.py
import anthropic
import os

class ClaudeAdapter:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = "claude-sonnet-4-20250514"

    def create_session(self, system_prompt: str) -> dict:
        """创建新的Claude会话"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=[]
        )
        return {"session_id": response.id, "model": self.model}

    def send_message(self, session_id: str, message: str, system_prompt: str = "") -> str:
        """发送消息到指定会话"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt if system_prompt else None,
            messages=[{"role": "user", "content": message}]
        )
        return response.content[0].text

claude_adapter = ClaudeAdapter()
```

- [ ] **Step 2: 提交**

```bash
git add backend/services/claude.py
git commit -m "feat: add Claude adapter"
```

---

## Task 3: Agent会话管理

**Files:**
- Create: `agenthub/backend/services/session.py`

**验收标准：**
- [ ] `AGENT_CONFIGS` 包含 `pm` 和 `architect` 两个Agent配置
- [ ] 每个Agent配置包含 `name`、`role`、`system_prompt`
- [ ] `SessionManager` 支持 `get_or_create_session` 方法，缓存会话ID
- [ ] `get_system_prompt` 返回指定Agent的系统提示词
- [ ] `send_to_agent` 封装会话创建和消息发送逻辑
- [ ] 模块导出单例 `session_manager` 供其他服务使用

- [ ] **Step 1: 编写会话管理器**

```python
# agenthub/backend/services/session.py
from typing import Dict, Optional
from .claude import claude_adapter

AGENT_CONFIGS = {
    "pm": {
        "name": "产品经理",
        "role": "产品经理（PM）",
        "system_prompt": """你是一个资深产品经理，专注于需求分析和用户体验设计。
当用户描述需求时，你应该：
1. 澄清需求的背景和目标
2. 分析用户群体和使用场景
3. 给出功能优先级建议
4. 用产品视角补充技术视角

当你需要输出完整的方案时，使用Spec格式：
## Spec: [功能名称]

### 1. 需求概述
[简洁描述]

### 2. 功能描述
[详细说明]

### 3. 技术方案
[架构设计]

### 4. 验收标准
[完成标准]"""
    },
    "architect": {
        "name": "架构师",
        "role": "系统架构师",
        "system_prompt": """你是一个资深系统架构师，专注于技术方案设计和架构决策。
当用户提出需求时，你应该：
1. 分析技术可行性和复杂度
2. 提出具体的技术方案和备选方案
3. 评估方案的优缺点和风险
4. 给出实施建议和时间估算

当你需要输出完整的技术方案时，使用Spec格式：
## Spec: [功能名称]

### 1. 需求概述
[简洁描述]

### 2. 功能描述
[详细说明]

### 3. 技术方案
[架构设计、API设计、数据库设计等]

### 4. 约束条件
[性能要求、兼容性等]

### 5. 验收标准
[完成标准]"""
    }
}

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, str] = {}
        self.system_prompts: Dict[str, str] = {}

    def get_or_create_session(self, agent_id: str) -> str:
        if agent_id not in self.sessions:
            config = AGENT_CONFIGS.get(agent_id)
            if not config:
                raise ValueError(f"Unknown agent: {agent_id}")
            session_info = claude_adapter.create_session(config["system_prompt"])
            self.sessions[agent_id] = session_info["session_id"]
            self.system_prompts[agent_id] = config["system_prompt"]
        return self.sessions[agent_id]

    def get_system_prompt(self, agent_id: str) -> str:
        if agent_id not in self.system_prompts:
            config = AGENT_CONFIGS.get(agent_id)
            if config:
                self.system_prompts[agent_id] = config["system_prompt"]
        return self.system_prompts.get(agent_id, "")

    def send_to_agent(self, agent_id: str, message: str) -> str:
        session_id = self.get_or_create_session(agent_id)
        system_prompt = self.get_system_prompt(agent_id)
        response = claude_adapter.send_message(session_id, message, system_prompt)
        return response

session_manager = SessionManager()
```

- [ ] **Step 2: 提交**

```bash
git add backend/services/session.py
git commit -m "feat: add session manager for agent Claude会话"
```

---

## Task 4: 消息路由器

**Files:**
- Create: `agenthub/backend/services/router.py`

**验收标准：**
- [ ] `parse_at_mention` 方法使用正则 `^@(\w+)\s+(.*)$` 解析@指令
- [ ] @指令解析成功返回 `(agent_id, content)` 元组
- [ ] @指令解析失败返回 `(None, 原始文本)`
- [ ] `get_target_agents` 方法：无@时返回所有Agent列表，有@时返回目标Agent列表
- [ ] `is_termination_signal` 方法检测终止关键词，支持 `["结束讨论", "开始实现", "确认方案", "重新讨论"]`
- [ ] `route_message` 返回包含 `targets`、`content`、`is_broadcast`、`is_termination`、`termination_keyword` 的字典
- [ ] 模块导出单例 `router` 供其他服务使用

- [ ] **Step 1: 编写消息路由器**

```python
# agenthub/backend/services/router.py
import re
from typing import Tuple, List, Optional
from .session import AGENT_CONFIGS

class MessageRouter:
    def __init__(self):
        self.termination_keywords = ["结束讨论", "开始实现", "确认方案", "重新讨论"]

    def parse_at_mention(self, text: str) -> Tuple[Optional[str], str]:
        """解析@mention格式，返回(target, content)"""
        match = re.match(r'^@(\w+)\s+(.*)$', text.strip())
        if match:
            agent_id = match.group(1)
            if agent_id in AGENT_CONFIGS:
                return agent_id, match.group(2)
        return None, text

    def get_target_agents(self, text: str) -> List[str]:
        """获取消息目标，无@返回所有Agent"""
        target, _ = self.parse_at_mention(text)
        if target:
            return [target]
        return list(AGENT_CONFIGS.keys())

    def is_termination_signal(self, text: str) -> Tuple[bool, str]:
        """检查终止关键词"""
        for keyword in self.termination_keywords:
            if keyword in text:
                return True, keyword
        return False, ""

    def route_message(self, text: str) -> dict:
        """路由消息，返回路由结果"""
        target, content = self.parse_at_mention(text)
        is_termination, keyword = self.is_termination_signal(text)
        return {
            "targets": self.get_target_agents(text),
            "content": content,
            "is_broadcast": target is None,
            "is_termination": is_termination,
            "termination_keyword": keyword
        }

router = MessageRouter()
```

- [ ] **Step 2: 提交**

```bash
git add backend/services/router.py
git commit -m "feat: add message router with @mention parsing"
```

---

## Task 5: 共享上下文管理

**Files:**
- Create: `agenthub/backend/services/memory.py`

**验收标准：**
- [ ] `MemoryManager` 类管理消息列表，默认上下文窗口20条
- [ ] `add_message` 方法添加消息，返回包含 `id`、`sender`、`sender_name`、`content`、`timestamp`、`type` 的字典
- [ ] `add_message` 使用 `uuid.uuid4().hex[:8]` 生成8位消息ID
- [ ] `add_message` 超过上下文窗口时，保留最近20条消息
- [ ] `get_messages` 方法支持 `limit` 参数，默认返回最近50条消息
- [ ] `get_context_for_agent` 返回最近10条消息的上下文字符串，格式为 `[{sender_name}]: {content[:200]}`
- [ ] 模块导出单例 `memory_manager` 供其他服务使用

- [ ] **Step 1: 编写内存管理器**

```python
# agenthub/backend/services/memory.py
from typing import List, Dict
from datetime import datetime
import uuid

class MemoryManager:
    def __init__(self):
        self.messages: List[Dict] = []
        self.context_window = 20

    def add_message(self, sender: str, sender_name: str, content: str, msg_type: str = "agent") -> Dict:
        message = {
            "id": f"msg_{uuid.uuid4().hex[:8]}",
            "sender": sender,
            "sender_name": sender_name,
            "content": content,
            "timestamp": int(datetime.now().timestamp()),
            "type": msg_type
        }
        self.messages.append(message)
        if len(self.messages) > self.context_window:
            self.messages = self.messages[-self.context_window:]
        return message

    def get_messages(self, limit: int = 50) -> List[Dict]:
        return self.messages[-limit:]

    def get_context_for_agent(self, agent_id: str) -> str:
        recent = self.get_messages(limit=10)
        context_parts = []
        for msg in recent:
            context_parts.append(f"[{msg['sender_name']}]: {msg['content'][:200]}")
        return "\n".join(context_parts)

    def clear(self):
        self.messages = []

memory_manager = MemoryManager()
```

- [ ] **Step 2: 提交**

```bash
git add backend/services/memory.py
git commit -m "feat: add memory manager for shared context"
```

---

## Task 6: SSE事件管理器

**Files:**
- Create: `agenthub/backend/services/sse_manager.py`

**验收标准：**
- [ ] `SSEEventManager` 类管理订阅者队列集合
- [ ] `subscribe` 方法返回异步生成器，管理队列订阅生命周期
- [ ] `push_message` 方法推送消息事件，事件类型为 `message`
- [ ] `push_termination` 方法推送终止事件，事件类型为 `termination`，包含 `keyword` 和 `message_id`
- [ ] 事件格式符合SSE规范：`event: {type}\ndata: {json}\n\n`
- [ ] 模块导出单例 `sse_manager` 供其他服务使用

- [ ] **Step 1: 编写SSE管理器**

```python
# agenthub/backend/services/sse_manager.py
from typing import AsyncGenerator, Dict, Set
import asyncio
import json

class SSEEventManager:
    def __init__(self):
        self.subscribers: Set[asyncio.Queue] = set()

    async def subscribe(self) -> AsyncGenerator:
        """SSE订阅，返回事件流"""
        queue = asyncio.Queue()
        self.subscribers.add(queue)
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            self.subscribers.remove(queue)

    async def push_message(self, message: dict):
        """推送消息到所有订阅者"""
        event = f"event: message\ndata: {json.dumps(message, ensure_ascii=False)}\n\n"
        for queue in self.subscribers:
            await queue.put(event)

    async def push_termination(self, keyword: str, message_id: str):
        """推送终止信号"""
        data = json.dumps({"keyword": keyword, "message_id": message_id}, ensure_ascii=False)
        event = f"event: termination\ndata: {data}\n\n"
        for queue in self.subscribers:
            await queue.put(event)

sse_manager = SSEEventManager()
```

- [ ] **Step 2: 提交**

```bash
git add backend/services/sse_manager.py
git commit -m "feat: add SSE event manager"
```

---

## Task 7: API路由

**Files:**
- Create: `agenthub/backend/routers/messages.py`
- Create: `agenthub/backend/routers/events.py`

**验收标准：**
- [ ] `POST /api/messages` 端点接收 `SendMessageRequest`，返回发送结果
- [ ] `POST /api/messages` 解析@指令，路由到目标Agent
- [ ] `POST /api/messages` 检测终止关键词，有则返回 `is_termination: true`
- [ ] `POST /api/messages` 返回 `success`、`message_id`、`is_broadcast` 字段
- [ ] `GET /api/messages` 端点返回消息列表查询接口
- [ ] `GET /api/messages` 支持 `limit` 查询参数
- [ ] `GET /api/agents` 端点返回已配置Agent列表
- [ ] `GET /api/events` SSE端点返回事件流
- [ ] `GET /api/events` 使用 `EventSourceResponse` 实现SSE

- [ ] **Step 1: 创建消息路由**

```python
# agenthub/backend/routers/messages.py
from fastapi import APIRouter, HTTPException
from ..models.message import SendMessageRequest
from ..services.router import router
from ..services.session import session_manager, AGENT_CONFIGS
from ..services.memory import memory_manager
from ..services.sse_manager import sse_manager

router_api = APIRouter(prefix="/api")

@router_api.post("/messages")
async def send_message(req: SendMessageRequest):
    """发送消息并路由到相应Agent"""
    route_result = router.route_message(req.content)

    # 添加用户消息
    user_msg = memory_manager.add_message(
        sender=req.sender,
        sender_name=req.sender_name,
        content=req.content,
        msg_type="user"
    )

    # 立即推送用户消息到SSE
    await sse_manager.push_message(user_msg)

    # 检查终止信号
    if route_result["is_termination"]:
        await sse_manager.push_termination(
            route_result["termination_keyword"],
            user_msg["id"]
        )
        return {"success": True, "message_id": user_msg["id"], "is_termination": True}

    # 发送消息给目标Agent
    for agent_id in route_result["targets"]:
        try:
            agent_config = AGENT_CONFIGS.get(agent_id)
            if not agent_config:
                continue

            context = memory_manager.get_context_for_agent(agent_id)
            agent_message = f"上下文参考:\n{context}\n\n用户消息: {route_result['content']}" if context else route_result['content']

            response = session_manager.send_to_agent(agent_id, agent_message)

            agent_msg = memory_manager.add_message(
                sender=agent_id,
                sender_name=agent_config["name"],
                content=response,
                msg_type="agent"
            )

            await sse_manager.push_message(agent_msg)

        except Exception as e:
            error_msg = {
                "id": f"msg_{uuid.uuid4().hex[:8]}",
                "sender": agent_id,
                "sender_name": agent_config["name"],
                "content": f"Error: {str(e)}",
                "timestamp": int(datetime.now().timestamp()),
                "type": "agent"
            }
            await sse_manager.push_message(error_msg)

    return {"success": True, "message_id": user_msg["id"], "is_broadcast": route_result["is_broadcast"]}

@router_api.get("/messages")
async def get_messages(limit: int = 50):
    """获取消息历史"""
    messages = memory_manager.get_messages(limit=limit)
    return {"messages": messages}

@router_api.get("/agents")
async def get_agents():
    """获取Agent列表"""
    agents = [
        {"id": agent_id, **config}
        for agent_id, config in AGENT_CONFIGS.items()
    ]
    return {"agents": agents}
```

- [ ] **Step 2: 创建SSE事件路由**

```python
# agenthub/backend/routers/events.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from ..services.sse_manager import sse_manager
import asyncio
import json

router_events = APIRouter(prefix="/api")

@router_events.get("/events")
async def events():
    """SSE事件流端点"""
    async def event_generator():
        queue = asyncio.Queue()
        sse_manager.subscribers.add(queue)
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            sse_manager.subscribers.discard(queue)

    return EventSourceResponse(event_generator())
```

- [ ] **Step 3: 更新main.py导入**

```python
# agenthub/backend/main.py 添加
from routers import messages, events
app.include_router(messages.router)
app.include_router(events.router)
```

- [ ] **Step 4: 提交**

```bash
git add backend/routers/messages.py backend/routers/events.py backend/main.py
git commit -m "feat: add API routes and SSE endpoint"
```

---

## Task 8: 前端初始化 - Next.js

**Files:**
- Create: `agenthub/frontend/package.json`
- Create: `agenthub/frontend/tsconfig.json`
- Create: `agenthub/frontend/next.config.js`
- Create: `agenthub/frontend/tailwind.config.ts`
- Create: `agenthub/frontend/app/globals.css`
- Create: `agenthub/frontend/app/layout.tsx`

**验收标准：**
- [ ] `package.json` 包含 Next.js 14、React 18、react-markdown 依赖
- [ ] `package.json` 包含 TypeScript、TailwindCSS、PostCSS、autoprefixer 开发依赖
- [ ] `tsconfig.json` 配置 `paths: { "@/*": ["./*"] }` 支持路径别名
- [ ] `next.config.js` 配置 API 代理，将 `/api/*` 转发到 `http://localhost:8000/*`
- [ ] `tailwind.config.ts` 配置 content 路径覆盖 `./app/**/*` 和 `./components/**/*`
- [ ] `globals.css` 包含 `@tailwind base`、`@tailwind components`、`@tailwind utilities`
- [ ] `layout.tsx` 包含 Metadata 配置，标题为 "AgentHub"
- [ ] 项目可通过 `npm install && npm run dev` 启动，监听 localhost:3000

- [ ] **Step 1: 创建package.json**

```json
{
  "name": "agenthub-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "14.2.3",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-markdown": "^9.0.1"
  },
  "devDependencies": {
    "@types/node": "^20.12.7",
    "@types/react": "^18.3.1",
    "@types/react-dom": "^18.3.0",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.3",
    "typescript": "^5.4.5"
  }
}
```

- [ ] **Step 2: 创建tsconfig.json**

```json
{
  "compilerOptions": {
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 3: 创建next.config.js**

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
```

- [ ] **Step 4: 创建tailwind.config.ts**

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
export default config;
```

- [ ] **Step 5: 创建postcss.config.js**

```javascript
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

- [ ] **Step 6: 创建globals.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 7: 创建layout.tsx**

```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgentHub",
  description: "多Agent协作平台",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
```

- [ ] **Step 8: 提交**

```bash
git add frontend/package.json frontend/tsconfig.json frontend/next.config.js
git add frontend/tailwind.config.ts frontend/postcss.config.js
git add frontend/app/globals.css frontend/app/layout.tsx
git commit -m "feat: add Next.js project structure"
```

---

## Task 9: 前端类型定义

**Files:**
- Create: `agenthub/frontend/lib/types.ts`
- Create: `agenthub/frontend/lib/api.ts`

**验收标准：**
- [ ] `types.ts` 导出 `Message` 接口，包含 `id`、`sender`、`sender_name`、`content`、`timestamp`、`type`
- [ ] `types.ts` 导出 `Agent` 接口，包含 `id`、`name`、`role`
- [ ] `types.ts` 导出 `SendMessageResponse` 接口，包含 `success`、`message_id`、`is_broadcast?`、`is_termination?`
- [ ] `api.ts` 的 `sendMessage` 方法 POST 到 `/api/messages`
- [ ] `api.ts` 的 `getMessages` 方法 GET `/api/messages?limit={limit}`
- [ ] `api.ts` 的 `getAgents` 方法 GET `/api/agents`
- [ ] `createSSEConnection` 函数建立 `/api/events` SSE连接
- [ ] SSE 监听 `message` 和 `termination` 两种事件类型

- [ ] **Step 1: 创建类型定义**

```typescript
// agenthub/frontend/lib/types.ts
export interface Message {
  id: string;
  sender: string;
  sender_name: string;
  content: string;
  timestamp: number;
  type: 'user' | 'agent';
}

export interface Agent {
  id: string;
  name: string;
  role: string;
}

export interface SendMessageResponse {
  success: boolean;
  message_id: string;
  is_broadcast?: boolean;
  is_termination?: boolean;
}
```

- [ ] **Step 2: 创建API服务**

```typescript
// agenthub/frontend/lib/api.ts
import { Message, Agent, SendMessageResponse } from './types';

const API_BASE = '/api';

export const api = {
  async sendMessage(content: string): Promise<SendMessageResponse> {
    const res = await fetch(`${API_BASE}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content,
        sender: 'user',
        sender_name: '用户'
      })
    });
    return res.json();
  },

  async getMessages(limit: number = 50): Promise<{ messages: Message[] }> {
    const res = await fetch(`${API_BASE}/messages?limit=${limit}`);
    return res.json();
  },

  async getAgents(): Promise<{ agents: Agent[] }> {
    const res = await fetch(`${API_BASE}/agents`);
    return res.json();
  }
};

export function createSSEConnection(
  onMessage: (message: Message) => void,
  onTermination: (keyword: string) => void
) {
  const eventSource = new EventSource(`${API_BASE}/events`);

  eventSource.addEventListener('message', (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  });

  eventSource.addEventListener('termination', (event) => {
    const data = JSON.parse(event.data);
    onTermination(data.keyword);
  });

  eventSource.onerror = (error) => {
    console.error('SSE error:', error);
  };

  return eventSource;
}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/lib/types.ts frontend/lib/api.ts
git commit -m "feat: add frontend type definitions and API service"
```

---

## Task 10: 前端组件 - MessageBubble

**Files:**
- Create: `agenthub/frontend/components/chat/MessageBubble.tsx`

**验收标准：**
- [ ] `MessageBubble` 组件接收 `Message` 类型 `message` prop
- [ ] 根据 `message.type` 区分用户消息和Agent消息，使用不同样式
- [ ] 使用 `react-markdown` 渲染消息内容
- [ ] 显示发送者名称 `message.sender_name`
- [ ] 显示格式化的时间戳（时:分）
- [ ] PM Agent 使用蓝色主题样式
- [ ] 其他Agent使用绿色主题样式
- [ ] 用户消息使用灰色主题样式，右对齐显示

- [ ] **Step 1: 创建MessageBubble组件**

```tsx
// agenthub/frontend/components/chat/MessageBubble.tsx
'use client';

import ReactMarkdown from 'react-markdown';
import { Message } from '@/lib/types';

interface MessageBubbleProps {
  message: Message;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isAgent = message.type === 'agent';
  const isPM = message.sender === 'pm';

  return (
    <div className={`flex ${isAgent ? 'items-start' : 'items-end'} mb-4`}>
      <div
        className={`max-w-[70%] px-4 py-3 rounded-2xl ${
          isPM
            ? 'bg-blue-100 border border-blue-300 rounded-tl-none'
            : isAgent
            ? 'bg-green-100 border border-green-300 rounded-tl-none'
            : 'bg-gray-100 border border-gray-300 rounded-tr-none'
        }`}
      >
        <div className="text-xs font-semibold text-gray-600 mb-1">
          {message.sender_name}
        </div>
        <div className="text-sm leading-relaxed">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
      </div>
      <div className="text-xs text-gray-400 mt-1 mx-2">
        {new Date(message.timestamp * 1000).toLocaleTimeString('zh-CN', {
          hour: '2-digit',
          minute: '2-digit'
        })}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/components/chat/MessageBubble.tsx
git commit -m "feat: add MessageBubble component"
```

---

## Task 11: 前端组件 - MessageList

**Files:**
- Create: `agenthub/frontend/components/chat/MessageList.tsx`

**验收标准：**
- [ ] `MessageList` 组件接收 `Message[]` 类型 `messages` prop
- [ ] 使用 `useEffect` 监听 `messages` 变化，自动滚动到底部
- [ ] 使用 `useRef` 引用列表容器 DOM 元素
- [ ] 消息为空时显示占位提示文字 "暂无消息，开始对话吧"
- [ ] 使用 `MessageBubble` 组件渲染每条消息
- [ ] 列表容器使用 `overflow-y-auto` 实现垂直滚动

- [ ] **Step 1: 创建MessageList组件**

```tsx
// agenthub/frontend/components/chat/MessageList.tsx
'use client';

import { useEffect, useRef } from 'react';
import { Message } from '@/lib/types';
import { MessageBubble } from './MessageBubble';

interface MessageListProps {
  messages: Message[];
}

export function MessageList({ messages }: MessageListProps) {
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div
      ref={listRef}
      className="flex-1 overflow-y-auto p-4 bg-gray-50"
    >
      {messages.length === 0 ? (
        <div className="text-center text-gray-400 mt-20">
          暂无消息，开始对话吧
        </div>
      ) : (
        messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))
      )}
    </div>
  );
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/components/chat/MessageList.tsx
git commit -m "feat: add MessageList component"
```

---

## Task 12: 前端组件 - MessageInput

**Files:**
- Create: `agenthub/frontend/components/chat/MessageInput.tsx`

**验收标准：**
- [ ] `MessageInput` 组件接收 `onSend` 函数和 `disabled?` 可选 prop
- [ ] 使用受控组件管理输入框状态
- [ ] 表单提交时调用 `onSend` 并清空输入框
- [ ] `disabled` 为 true 时显示占位符 "等待回复..."，输入框禁用
- [ ] 发送按钮在输入为空或 `disabled` 为 true 时禁用显示
- [ ] 按钮使用条件样式：可发送时蓝色激活，不可发送时灰色禁用

- [ ] **Step 1: 创建MessageInput组件**

```tsx
// agenthub/frontend/components/chat/MessageInput.tsx
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

- [ ] **Step 2: 提交**

```bash
git add frontend/components/chat/MessageInput.tsx
git commit -m "feat: add MessageInput component"
```

---

## Task 13: 前端组件 - AgentList

**Files:**
- Create: `agenthub/frontend/components/agents/AgentList.tsx`

**验收标准：**
- [ ] `AgentList` 组件接收 `Agent[]` 类型 `agents` prop
- [ ] 侧边栏宽度 12rem (w-48)，白色背景
- [ ] 标题 "Agent 列表" 使用 `text-sm font-semibold`
- [ ] 每个Agent显示 `name` 和 `role`
- [ ] Agent项之间使用 `border-b border-gray-100` 分隔

- [ ] **Step 1: 创建AgentList组件**

```tsx
// agenthub/frontend/components/agents/AgentList.tsx
'use client';

import { Agent } from '@/lib/types';

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

- [ ] **Step 2: 提交**

```bash
git add frontend/components/agents/AgentList.tsx
git commit -m "feat: add AgentList component"
```

---

## Task 14: 前端主页面

**Files:**
- Create: `agenthub/frontend/app/page.tsx`

**验收标准：**
- [ ] 主页面使用 `'use client'` 指令
- [ ] 使用 `useState` 管理 `messages`、`agents`、`loading` 状态
- [ ] 页面加载时调用 `api.getMessages()` 和 `api.getAgents()` 初始化数据
- [ ] 建立 SSE 连接，监听 `message` 和 `termination` 事件
- [ ] `message` 事件将新消息追加到 `messages` 状态
- [ ] `termination` 事件弹出 alert 显示终止关键词
- [ ] 组件卸载时关闭 SSE 连接
- [ ] `handleSend` 函数调用 `api.sendMessage()` 并设置 loading 状态
- [ ] 布局包含 Header、AgentList 侧边栏、MessageList 和 MessageInput

- [ ] **Step 1: 创建主页面**

```tsx
// agenthub/frontend/app/page.tsx
'use client';

import { useState, useEffect, useCallback } from 'react';
import { AgentList } from '@/components/agents/AgentList';
import { MessageList } from '@/components/chat/MessageList';
import { MessageInput } from '@/components/chat/MessageInput';
import { api, createSSEConnection } from '@/lib/api';
import { Message, Agent } from '@/lib/types';

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // 加载初始数据
    const loadData = async () => {
      try {
        const [msgsRes, agentsRes] = await Promise.all([
          api.getMessages(),
          api.getAgents()
        ]);
        setMessages(msgsRes.messages || []);
        setAgents(agentsRes.agents || []);
      } catch (err) {
        console.error('Failed to load data:', err);
      }
    };
    loadData();

    // 建立SSE连接
    const eventSource = createSSEConnection(
      (message) => {
        setMessages((prev) => [...prev, message]);
      },
      (keyword) => {
        alert(`已识别终止信号: ${keyword}`);
      }
    );

    return () => {
      eventSource.close();
    };
  }, []);

  const handleSend = useCallback(async (content: string) => {
    setLoading(true);
    try {
      await api.sendMessage(content);
    } catch (err) {
      console.error('Failed to send message:', err);
      alert('发送消息失败');
    } finally {
      setLoading(false);
    }
  }, []);

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
          <MessageList messages={messages} />
          <MessageInput onSend={handleSend} disabled={loading} />
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/app/page.tsx
git commit -m "feat: add main page with full UI"
```

---

## Task 15: README文档

**Files:**
- Create: `agenthub/README.md`

**验收标准：**
- [ ] README 包含项目简介 "IM聊天式多Agent协作平台"
- [ ] 包含后端启动说明：`pip install`、`cp .env.example .env`、`python main.py`
- [ ] 包含前端启动说明：`npm install`、`npm run dev`
- [ ] 功能列表包含：@指令触发、广播消息、SSE实时推送、Spec格式输出、终止关键词
- [ ] 技术栈说明前端为 Next.js 14 + TypeScript + TailwindCSS，后端为 FastAPI + Python

- [ ] **Step 1: 创建README**

```markdown
# AgentHub

IM聊天式多Agent协作平台

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # 编辑并填入 ANTHROPIC_API_KEY
python main.py
```

后端运行在 http://localhost:8000

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:3000

## 功能

- [x] @指令触发特定Agent
- [x] 广播消息给所有Agent
- [x] SSE实时推送
- [x] Spec文档格式输出
- [x] 人类触发终止讨论

## 技术栈

- 前端: Next.js 14 + TypeScript + TailwindCSS
- 后端: FastAPI + Python
- 通信: HTTP POST + SSE
```

- [ ] **Step 2: 提交**

```bash
git add README.md
git commit -m "docs: add README"
```

---

## 执行选择

**Plan complete and saved to `docs/superpowers/plans/2026-05-24-agenthub-mvp-plan.md`.**

Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**