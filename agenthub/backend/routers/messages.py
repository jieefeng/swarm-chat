"""消息路由 - 提供消息历史和Agent列表API"""
import logging
import uuid
import asyncio
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from agenthub.backend.services.session import AGENT_CONFIGS, session_manager
from agenthub.backend.services.agent_identity import get_identity, get_bond_context
from agenthub.backend.services.claude_code_service import claude_code_service
import os
from agenthub.backend.services.memory_manager import (
    memory_manager,
    redis_memory_manager,
)

logger = logging.getLogger(__name__)

# 并发限制：最多同时处理的 LLM 调用数
MAX_CONCURRENT_LLM_CALLS = int(os.getenv("MAX_CONCURRENT_LLM_CALLS", "5"))
_llm_semaphore = asyncio.Semaphore(MAX_CONCURRENT_LLM_CALLS)

# SSE 队列最大容量，防止 OOM
SSE_QUEUE_MAXSIZE = int(os.getenv("SSE_QUEUE_MAXSIZE", "1000"))

# 根据 STORAGE_BACKEND 选择存储实例
# redis_memory_manager 由 create_memory_manager() 根据环境变量创建：
# - STORAGE_BACKEND=redis → RedisMemoryManager
# - STORAGE_BACKEND=sqlite（默认） → sqlite_manager 单例
# - Redis 连接失败 → 回退到 sqlite_manager
memory = redis_memory_manager
from agenthub.backend.services.sse_manager import sse_manager
from agenthub.backend.services.router import MessageRouter
from agenthub.backend.services.clarification_parser import (
    parse_clarification_from_response,
)
from agenthub.backend.services.database import get_db


async def _persist_message(
    role: str,
    content: str,
    agent_id: str,
    sender_name: str,
    user_id: str,
    thread_id: str,
) -> dict:
    """保存消息到 memory。当 memory 不是 SQLite 单例时，额外写入 SQLite。"""
    from agenthub.backend.services.database import sqlite_manager as _sqlite_singleton

    msg = await memory.add_message(
        role=role,
        content=content,
        agent_id=agent_id,
        sender_name=sender_name,
        user_id=user_id,
        thread_id=thread_id,
    )

    # 当 memory 是 SQLite 单例时（STORAGE_BACKEND=sqlite），跳过重复写入
    if memory is _sqlite_singleton:
        return msg

    # Redis 或内存模式：额外持久化到 SQLite
    try:
        db = await get_db()
        await db.add_message(
            thread_id=thread_id,
            role=role,
            content=content,
            agent_id=agent_id,
            sender_name=sender_name,
        )
        logger.info("Message persisted to SQLite: thread_id=%s, role=%s", thread_id, role)
    except Exception as e:
        logger.error("SQLite persist error: %s", e)
    return msg


router = APIRouter(prefix="/api", tags=["messages"])

# 初始化消息路由器
message_router = MessageRouter()


class SendMessageRequest(BaseModel):
    content: str
    sender: str = "user"
    sender_name: str = "用户"
    agent_id: Optional[str] = None
    user_id: str = "default"
    thread_id: str = "default"


class MessageRequest(BaseModel):
    role: str
    content: str
    agent_id: Optional[str] = None


class MessageResponse(BaseModel):
    role: str
    content: str
    agent_id: Optional[str] = None
    timestamp: str


class AgentInfo(BaseModel):
    id: str
    name: str
    role: str


@router.get("/agents")
async def get_agents():
    """获取Agent列表（含五行神兽身份信息）"""
    agents = []
    for agent_id, config in AGENT_CONFIGS.items():
        agent = {
            "id": agent_id,
            "name": config["name"],
            "role": config["role"],
        }
        # 合并神兽身份信息
        identity = get_identity(agent_id)
        if identity:
            agent.update({
                "beast": identity.get("beast"),
                "nickname": identity.get("nickname"),
                "element": identity.get("element"),
                "avatar": identity.get("avatar"),
                "color": identity.get("color"),
                "personality": identity.get("personality"),
                "catchphrase": identity.get("catchphrase"),
                "strengths": identity.get("strengths"),
                "caution": identity.get("caution"),
                "bonds": identity.get("bonds"),
                "speechStyle": identity.get("speech_style"),
            })
        agents.append(agent)
    return {"agents": agents}


@router.get("/messages")
async def get_messages(limit: int = Query(50, ge=1, le=200), thread_id: str = Query("default")):
    """获取消息历史（按线程隔离）"""
    try:
        # 优先从 SQLite 读取持久化消息
        db = await get_db()
        messages = await db.get_messages(thread_id=thread_id, limit=limit)
        try:
            print(f"[MESSAGES] Loaded {len(messages)} messages from SQLite for thread_id={thread_id}")
        except UnicodeEncodeError:
            print(f"[MESSAGES] Loaded {len(messages)} messages from SQLite (encoding error in log)")
        return {"messages": messages}
    except Exception as e:
        try:
            print(f"[MESSAGES] SQLite load error: {e}")
        except UnicodeEncodeError:
            print(f"[MESSAGES] SQLite load error: (encoding error in error message)")
        # 回退到内存存储
        messages = await memory.get_messages(limit=limit, thread_id=thread_id)
        try:
            print(f"[MESSAGES] Loaded {len(messages)} messages from memory for thread_id={thread_id}")
        except UnicodeEncodeError:
            print(f"[MESSAGES] Loaded {len(messages)} messages from memory (encoding error in log)")
        return {"messages": messages}


@router.post("/messages")
async def send_message(req: SendMessageRequest):
    """发送消息并路由到相应Agent

    1. 解析@指令，确定目标Agent
    2. 推送用户消息到SSE
    3. 检测终止关键词
    4. 并行发送消息给目标Agent
    5. 推送Agent响应到SSE
    """
    # 检查是否是 /help 指令
    if req.content.strip().startswith("/help"):
        help_content = """## 📖 AgentHub 使用指南

### 🐉 五行神兽团队

| 神兽 | 名字 | 角色 | 专长 |
|------|------|------|------|
| 青龙 | 苍龙 | 产品经理 | 需求分析、用户体验、功能优先级 |
| 玄武 | 玄冥 | 架构师 | 技术方案、架构设计、技术选型 |
| 白虎 | 啸风 | 开发者 | 全栈开发、代码实现、调试修复 |
| 朱雀 | 炎翎 | 测试工程师 | 代码审查、测试用例、质量保证 |
| 麒麟 | 瑞麟 | 协调器 | 任务拆解、团队协调、进度管理 |

### 💬 基本操作

- **直接输入** — 消息发送给当前选中的 agent
- **@某人** — 定向发送给指定 agent（如 `@苍龙 帮我分析需求`）
- **@all** — 广播给所有 agent

### ⚡ 斜杠命令

| 命令 | 说明 |
|------|------|
| `/help` | 显示此帮助信息 |
| `/code` | 本地代码操作（见下方） |

### 💻 /code 命令

`/code` 命令可以执行本地代码操作：

```
/code read <文件路径>    — 读取文件
/code ls [目录]         — 列出目录
/code run <命令>        — 执行 shell 命令
/code env               — 查看环境信息
/code project [目录]    — 分析项目结构
/code search <关键词>   — 搜索文件内容
/code info <文件路径>   — 查看文件详情
```

也可以用自然语言：
```
/code 读取 README.md 的前 20 行
/code 检查 Python 版本
/code 执行 pytest 运行测试
```

### 🎯 使用技巧

1. **需求分析** → @苍龙（产品经理）
2. **技术方案** → @玄冥（架构师）
3. **写代码** → @啸风（开发者）
4. **代码审查** → @炎翎（测试）
5. **复杂任务** → @瑞麟（协调器）自动拆解"""

        help_msg = await _persist_message(
            role="system",
            content=help_content,
            agent_id="system",
            sender_name="系统",
            user_id=req.user_id,
            thread_id=req.thread_id,
        )
        await sse_manager.broadcast("message", help_msg)
        return {"status": "ok", "is_help_command": True, "success": True}

    # 检查是否是 /code 指令
    if req.content.strip().startswith("/code"):
        code_raw = req.content.strip()[5:].strip()  # 去掉 "/code" 前缀

        # 解析动词格式：/code <verb> [args]
        # 支持的动词：read, ls, run, env, project, search, info
        # 无动词时当作自然语言 prompt
        CODE_VERBS = {
            "read": "read_file",
            "write": "write_file",
            "ls": "list_dir",
            "dir": "list_dir",
            "run": "run_command",
            "exec": "run_command",
            "env": "get_env_info",
            "project": "analyze_project",
            "search": "search_in_files",
            "grep": "search_in_files",
            "info": "get_file_info",
        }

        verb = None
        args = ""
        if code_raw:
            parts = code_raw.split(None, 1)
            candidate = parts[0].lower()
            if candidate in CODE_VERBS:
                verb = candidate
                args = parts[1] if len(parts) > 1 else ""

        # 无参数时显示帮助
        if not code_raw:
            help_msg = await _persist_message(
                role="system",
                content="""📖 `/code` 指令用法：

**动词格式（推荐）：**
- `/code read <文件路径>` — 读取文件
- `/code ls [目录]` — 列出目录
- `/code run <命令>` — 执行命令
- `/code env` — 查看环境信息
- `/code project [目录]` — 分析项目
- `/code search <关键词>` — 搜索文件
- `/code info <文件路径>` — 文件详情

**自然语言（通用）：**
- `/code 读取 README.md 的前 20 行`
- `/code 检查 Python 版本`
- `/code 执行 pytest 运行测试`""",
                agent_id="system",
                sender_name="系统",
                user_id=req.user_id,
                thread_id=req.thread_id,
            )
            await sse_manager.broadcast("message", help_msg)
            return {"status": "ok", "is_code_command": True, "success": True}

        if code_raw:
            # 添加用户消息到memory + SQLite
            user_msg = await _persist_message(
                role=req.sender,
                content=req.content,
                agent_id=req.sender,
                sender_name=req.sender_name,
                user_id=req.user_id,
                thread_id=req.thread_id,
            )

            # 执行 Claude Code 命令
            try:
                # 检查 Claude Code 是否可用
                if not claude_code_service.is_available():
                    error_msg = await _persist_message(
                        role="system",
                        content="❌ Claude Code CLI 未安装。请运行 `npm install -g @anthropic-ai/claude-code` 安装。",
                        agent_id="system",
                        sender_name="系统",
                        user_id=req.user_id,
                        thread_id=req.thread_id,
                    )
                    await sse_manager.broadcast("message", error_msg)
                    return {"status": "error", "message": "Claude Code CLI 未安装"}

                # 根据动词调用对应方法
                if verb == "read":
                    result = claude_code_service.read_file(args)
                elif verb == "write":
                    result = claude_code_service.execute(f"写入文件：{args}")
                elif verb in ("ls", "dir"):
                    result = claude_code_service.list_dir(args or ".")
                elif verb in ("run", "exec"):
                    result = claude_code_service.run_command(args)
                elif verb == "env":
                    result = claude_code_service.get_env_info()
                elif verb == "project":
                    result = claude_code_service.analyze_project(args or ".")
                elif verb in ("search", "grep"):
                    result = claude_code_service.search_in_files(args)
                elif verb == "info":
                    result = claude_code_service.get_file_info(args)
                else:
                    # 无动词或未识别的动词，当作自然语言 prompt
                    result = claude_code_service.execute(code_raw)

                if result.success:
                    # 格式化成功响应
                    response_content = f"```\n{result.output}\n```"
                    if result.duration_ms > 0:
                        response_content += f"\n\n⏱️ 执行时间: {result.duration_ms}ms"
                else:
                    # 格式化错误响应
                    response_content = f"❌ 执行失败\n\n错误信息: {result.error}"
                    if result.output:
                        response_content += f"\n\n输出:\n```\n{result.output}\n```"

                # 保存并广播响应
                agent_msg = await _persist_message(
                    role="claude-code",
                    content=response_content,
                    agent_id="claude-code",
                    sender_name="Claude Code",
                    user_id=req.user_id,
                    thread_id=req.thread_id,
                )
                await sse_manager.broadcast("message", agent_msg)

                return {
                    "status": "ok",
                    "message_id": user_msg.get("id", ""),
                    "is_code_command": True,
                    "success": result.success,
                }

            except Exception as e:
                error_msg = await _persist_message(
                    role="system",
                    content=f"❌ 执行 /code 命令时出错: {str(e)}",
                    agent_id="system",
                    sender_name="系统",
                    user_id=req.user_id,
                    thread_id=req.thread_id,
                )
                await sse_manager.broadcast("message", error_msg)
                return {"status": "error", "message": str(e)}

    route_result = message_router.parse(req.content)

    # 添加用户消息到memory + SQLite
    user_msg = await _persist_message(
        role=req.sender,
        content=req.content,
        agent_id=req.sender,
        sender_name=req.sender_name,
        user_id=req.user_id,
        thread_id=req.thread_id,
    )

    # Note: 不广播用户消息，因为前端已通过乐观更新显示
    # 其他客户端可通过 GET /api/messages 获取历史消息

    # 检查终止信号
    if route_result["is_termination"]:
        await sse_manager.broadcast("termination", {
            "keyword": route_result["content"],
            "message_id": user_msg.get("id", "")
        }, thread_id=req.thread_id)
        return {
            "success": True,
            "message_id": user_msg.get("id", ""),
            "is_termination": True
        }

    # 获取目标Agent列表 (name可能需要转换为id)
    targets = route_result["target"]

    # 前端明确指定了Agent时，优先使用前端指定
    if req.agent_id:
        targets = [req.agent_id]
    elif not targets:
        targets = list(AGENT_CONFIGS.keys())
    elif isinstance(targets, str):
        # 单个name转换为id
        from agenthub.backend.services.router import MessageRouter
        targets = [MessageRouter._NAME_TO_ID.get(targets, targets)]
    else:
        # 多个name转换为id
        from agenthub.backend.services.router import MessageRouter
        targets = [MessageRouter._NAME_TO_ID.get(name, name) for name in targets]

    # 并行发送消息给Agent（流式输出）
    async def send_to_single_agent(agent_id: str) -> dict:
        """流式发送消息给单个Agent，逐个广播文本片段"""
        config = AGENT_CONFIGS.get(agent_id)
        if not config:
            return None

        agent_name = config.get("name", agent_id)
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        full_response = ""
        seq = 0

        # 获取信号量，限制并发 LLM 调用
        async with _llm_semaphore:
            try:
                context = await memory.get_context_for_agent(agent_id, user_id=req.user_id, thread_id=req.thread_id)
                agent_message = f"上下文参考:\n{context}\n\n用户消息: {route_result['content']}" if context else route_result['content']

                # 注入羁绊上下文（当有多个 agent 协作时）
                if isinstance(targets, list) and len(targets) > 1:
                    bond_context = get_bond_context(agent_id, targets)
                    if bond_context:
                        agent_message = f"{agent_message}\n\n{bond_context}"

                # 异步预取 LLM provider/model，避免在 sync 线程中阻塞事件循环
                from agenthub.backend.services.database import get_db
                from agenthub.backend.services.llm_config_db import LLMConfigDB
                _db = await get_db()
                _llm_cfg = LLMConfigDB(_db._db)
                _provider = await _llm_cfg.get_provider(agent_id)
                _model = await _llm_cfg.get_model(agent_id)

                # 获取完整聊天历史，传给 Claude Code
                full_history = await memory.get_messages(user_id=req.user_id, thread_id=req.thread_id)
                history_parts = []
                for msg in full_history:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    history_parts.append(f"[{role}]: {content}")
                history_text = "\n".join(history_parts)

                # 流式调用 LLM，使用线程安全的队列桥接同步生成器与异步循环
                # 设 maxsize 防止队列无限增长导致 OOM
                queue: asyncio.Queue = asyncio.Queue(maxsize=SSE_QUEUE_MAXSIZE)

                def _produce():
                    try:
                        for chunk in session_manager.send_to_agent_stream(
                            agent_id,
                            agent_message,
                            context=history_text,
                            thread_id=req.thread_id,
                            provider=_provider,
                            model=_model,
                            on_tool_start=lambda aid, cmd, thread_id=None: queue.put_nowait(
                                ("_tool_start", aid, cmd, thread_id)
                            ),
                            on_tool_progress=lambda aid, out, thread_id=None: queue.put_nowait(
                                ("_tool_progress", aid, out, thread_id)
                            ),
                            on_tool_result=lambda aid, content, success, thread_id=None: queue.put_nowait(
                                ("_tool_result", aid, content, success, thread_id)
                            ),
                        ):
                            queue.put_nowait(chunk)
                    except Exception as e:
                        queue.put_nowait(e)
                    finally:
                        queue.put_nowait(None)  # 哨兵值，表示生成器结束

                loop = asyncio.get_event_loop()
                loop.run_in_executor(None, _produce)

                # LLM 调用超时配置（默认 120 秒）
                LLM_STREAM_TIMEOUT = int(os.getenv("LLM_STREAM_TIMEOUT", "120"))

                while True:
                    try:
                        item = await asyncio.wait_for(queue.get(), timeout=LLM_STREAM_TIMEOUT)
                    except asyncio.TimeoutError:
                        # 超时：LLM 长时间无响应，终止并报错
                        error_msg = f"LLM 响应超时（{LLM_STREAM_TIMEOUT}秒）"
                        print(f"[MESSAGES] {error_msg} for agent {agent_id}")
                        raise TimeoutError(error_msg)

                    if item is None:
                        break
                    if isinstance(item, Exception):
                        raise item
                    if isinstance(item, tuple):
                        event_type = item[0]
                        if event_type == "_tool_start":
                            _, aid, cmd, tid = item
                            await sse_manager.broadcast_tool_start(aid, cmd, message_id, thread_id=tid)
                        elif event_type == "_tool_progress":
                            _, aid, out, tid = item
                            await sse_manager.broadcast_tool_progress(aid, out, message_id, thread_id=tid)
                        elif event_type == "_tool_result":
                            _, aid, content, success, tid = item
                            await sse_manager.broadcast_tool_result(aid, content, success, message_id, thread_id=tid)
                        continue
                    full_response += item
                    await sse_manager.broadcast_stream_chunk(message_id, item, seq, thread_id=req.thread_id)
                    seq += 1

                # 检查 LLM 输出是否含 clarification 段(LLM 模拟调用工具时会在文本中输出结构)
                # 提取并广播 clarification_request,同时从 full_response 中移除该段,避免重复显示
                clarification = parse_clarification_from_response(full_response)
                if clarification:
                    await sse_manager.broadcast_clarification_request(
                        message_id=message_id,
                        question=clarification.question,
                        options=clarification.options,
                        thread_id=req.thread_id,
                    )
                    full_response = clarification.cleaned_text

                # 流式完成，存储完整消息并广播
                agent_msg = await _persist_message(
                    role=agent_id,
                    content=full_response,
                    agent_id=agent_id,
                    sender_name=agent_name,
                    user_id=req.user_id,
                    thread_id=req.thread_id,
                )
                # 用实际的 message_id 更新
                agent_msg["id"] = message_id
                await sse_manager.broadcast("message", agent_msg, thread_id=req.thread_id)
                return agent_msg

            except Exception as e:
                error_msg = await _persist_message(
                    role=agent_id,
                    content=f"Error: {str(e)}",
                    agent_id=agent_id,
                    sender_name=agent_name,
                    user_id=req.user_id,
                    thread_id=req.thread_id,
                )
                await sse_manager.broadcast("message", error_msg, thread_id=req.thread_id)
                return error_msg

    # 使用asyncio.gather并行处理所有Agent
    await asyncio.gather(*[send_to_single_agent(agent_id) for agent_id in targets])

    return {
        "success": True,
        "message_id": user_msg.get("id", ""),
        "is_broadcast": route_result["is_broadcast"]
    }