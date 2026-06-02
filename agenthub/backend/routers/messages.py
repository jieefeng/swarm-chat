"""消息路由 - 提供消息历史和Agent列表API"""
import uuid
import asyncio
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from agenthub.backend.services.session import AGENT_CONFIGS, session_manager
from agenthub.backend.services.agent_identity import get_identity, get_bond_context
import os
from agenthub.backend.services.memory_manager import (
    memory_manager,
    redis_memory_manager,
)

# 根据 STORAGE_BACKEND 选择存储实例
memory = redis_memory_manager if os.getenv("STORAGE_BACKEND") == "redis" else memory_manager
from agenthub.backend.services.sse_manager import sse_manager
from agenthub.backend.services.router import MessageRouter
from agenthub.backend.services.orchestrator import OrchestratorAgent
from agenthub.backend.routers.tasks import task_manager

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
    messages = await memory.get_messages(limit=limit, thread_id=thread_id)
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
    print(f"[MESSAGES] Received message: {req.content[:100]}")
    route_result = message_router.parse(req.content)

    # 添加用户消息到memory
    user_msg = await memory.add_message(
        role=req.sender,
        content=req.content,
        agent_id=req.sender,
        sender_name=req.sender_name,
        user_id=req.user_id,
        thread_id=req.thread_id,
    )
    print(f"[MESSAGES] User message added: {user_msg.get('id')}")

    # Note: 不广播用户消息，因为前端已通过乐观更新显示
    # 其他客户端可通过 GET /api/messages 获取历史消息

    # 检查终止信号
    if route_result["is_termination"]:
        await sse_manager.broadcast("termination", {
            "keyword": route_result["content"],
            "message_id": user_msg.get("id", "")
        })
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

    # Orchestrator 拆解流程：拦截 @协调器 消息，走任务拆解而非普通 LLM 调用
    if "orchestrator" in targets:
        try:
            orchestrator = OrchestratorAgent()
            output = await orchestrator.decompose(route_result["content"])

            if output.requires_clarification:
                question = output.clarification_question or "请澄清您的需求"
                options = output.uncertain_points[0].options if output.uncertain_points else []
                await sse_manager.broadcast_clarification_request(
                    message_id=str(uuid.uuid4()),
                    question=question,
                    options=options,
                )
            elif output.tasks:
                tasks = task_manager.add_tasks_from_orchestrator(output)
                for task in tasks:
                    await sse_manager.broadcast_task_created(task.id, task.title, task.assigned_to)
                # 后台执行所有任务
                asyncio.create_task(task_manager.run_all())
            else:
                # 降级：将分析结果作为普通消息广播
                await sse_manager.broadcast("message", {
                    "id": str(uuid.uuid4()),
                    "sender": "orchestrator",
                    "sender_name": "瑞麟",
                    "content": output.analysis,
                    "timestamp": "",
                    "type": "agent",
                })
        except Exception as e:
            print(f"[MESSAGES] Orchestrator error: {e}")
            error_msg = await memory.add_message(
                role="orchestrator",
                content=f"协调器处理失败: {str(e)}",
                agent_id="orchestrator",
                sender_name="协调器",
                user_id=req.user_id,
                thread_id=req.thread_id,
            )
            await sse_manager.broadcast("message", error_msg)
        return {"status": "ok", "message_id": user_msg.get("id", "")}

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

        try:
            context = await memory.get_context_for_agent(agent_id, user_id=req.user_id, thread_id=req.thread_id)
            agent_message = f"上下文参考:\n{context}\n\n用户消息: {route_result['content']}" if context else route_result['content']

            # 注入羁绊上下文（当有多个 agent 协作时）
            if isinstance(targets, list) and len(targets) > 1:
                bond_context = get_bond_context(agent_id, targets)
                if bond_context:
                    agent_message = f"{agent_message}\n\n{bond_context}"

            # 流式调用 LLM，使用线程安全的队列桥接同步生成器与异步循环
            print(f"[STREAM] Starting stream for agent={agent_id}, message_id={message_id}")
            queue: asyncio.Queue = asyncio.Queue()

            def _produce():
                try:
                    for chunk in session_manager.send_to_agent_stream(
                        agent_id,
                        agent_message,
                        thread_id=req.thread_id,
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
            print(f"[STREAM] Producer started, consuming from queue")

            while True:
                item = await queue.get()
                if item is None:
                    print(f"[STREAM] Generator exhausted after {seq} chunks")
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
                print(f"[STREAM] Got chunk #{seq}: {repr(item[:50])}")
                await sse_manager.broadcast_stream_chunk(message_id, item, seq)
                seq += 1

            # 流式完成，存储完整消息并广播
            print(f"[STREAM] Stream complete. Total chunks: {seq}, response length: {len(full_response)}")
            agent_msg = await memory.add_message(
                role=agent_id,
                content=full_response,
                agent_id=agent_id,
                sender_name=agent_name,
                user_id=req.user_id,
                thread_id=req.thread_id,
            )
            # 用实际的 message_id 更新
            agent_msg["id"] = message_id
            print(f"[STREAM] Broadcasting final message event, message_id={message_id}")
            await sse_manager.broadcast("message", agent_msg)
            return agent_msg

        except Exception as e:
            error_msg = await memory.add_message(
                role=agent_id,
                content=f"Error: {str(e)}",
                agent_id=agent_id,
                sender_name=agent_name,
                user_id=req.user_id,
                thread_id=req.thread_id,
            )
            await sse_manager.broadcast("message", error_msg)
            return error_msg

    # 使用asyncio.gather并行处理所有Agent
    await asyncio.gather(*[send_to_single_agent(agent_id) for agent_id in targets])

    return {
        "success": True,
        "message_id": user_msg.get("id", ""),
        "is_broadcast": route_result["is_broadcast"]
    }