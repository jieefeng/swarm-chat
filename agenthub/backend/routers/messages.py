"""消息路由 - 提供消息历史和Agent列表API"""
import uuid
import asyncio
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from agenthub.backend.services.session import AGENT_CONFIGS, session_manager
from agenthub.backend.services.memory_manager import memory_manager
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
    agent_id: Optional[str] = None  # 前端指定的Agent ID


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
    """获取Agent列表"""
    agents = [
        {"id": agent_id, "name": config["name"], "role": config["role"]}
        for agent_id, config in AGENT_CONFIGS.items()
    ]
    return {"agents": agents}


@router.get("/messages")
async def get_messages(limit: int = Query(50, ge=1, le=200)):
    """获取消息历史"""
    messages = memory_manager.get_messages(limit=limit)
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
    user_msg = memory_manager.add_message(
        role=req.sender,
        content=req.content,
        agent_id=req.sender,
        sender_name=req.sender_name
    )
    print(f"[MESSAGES] User message added: {user_msg.get('id')}")

    # 推送用户消息到SSE
    print(f"[MESSAGES] Broadcasting user message...")
    await sse_manager.broadcast("message", user_msg)
    print(f"[MESSAGES] User message broadcast complete")

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
                    "sender_name": "协调器",
                    "content": output.analysis,
                    "timestamp": "",
                    "type": "agent",
                })
        except Exception as e:
            print(f"[MESSAGES] Orchestrator error: {e}")
            error_msg = memory_manager.add_message(
                role="orchestrator",
                content=f"协调器处理失败: {str(e)}",
                agent_id="orchestrator",
                sender_name="协调器"
            )
            await sse_manager.broadcast("message", error_msg)
        return {"status": "ok", "message_id": user_msg.get("id", "")}

    # 并行发送消息给Agent
    async def send_to_single_agent(agent_id: str) -> dict:
        """发送消息给单个Agent"""
        config = AGENT_CONFIGS.get(agent_id)
        if not config:
            return None

        try:
            context = memory_manager.get_context_for_agent(agent_id)
            agent_message = f"上下文参考:\n{context}\n\n用户消息: {route_result['content']}" if context else route_result['content']

            # 在线程池中执行同步的 LLM 调用，避免阻塞事件循环
            response = await asyncio.to_thread(session_manager.send_to_agent, agent_id, agent_message)

            config = AGENT_CONFIGS.get(agent_id, {})
            agent_name = config.get("name", agent_id)

            agent_msg = memory_manager.add_message(
                role=agent_id,
                content=response,
                agent_id=agent_id,
                sender_name=agent_name
            )

            await sse_manager.broadcast("message", agent_msg)
            return agent_msg

        except Exception as e:
            config = AGENT_CONFIGS.get(agent_id, {})
            agent_name = config.get("name", agent_id)
            error_msg = memory_manager.add_message(
                role=agent_id,
                content=f"Error: {str(e)}",
                agent_id=agent_id,
                sender_name=agent_name
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