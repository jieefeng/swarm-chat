"""A2A 路由引擎 - Worklist 模式

实现 Agent-to-Agent 路由，支持：
- Worklist 模式（while 循环 + 动态数组）
- 深度限制（默认 15 轮）
- 共享 AbortController（用户可随时 Stop）
- isFinal 语义（全部完成后才解锁输入框）

参考：Cat Café 项目（zts212653/clowder-ai）
"""
import asyncio
import os
import logging
from typing import AsyncIterator, Dict, List, Optional

from .invocation_registry import invocation_registry as _invocation_registry
from .prompt_injector import prompt_injector as _prompt_injector

# 模块级属性（方便测试 mock 覆盖）
invocation_registry = _invocation_registry
prompt_injector = _prompt_injector

logger = logging.getLogger(__name__)

# 默认最大深度
DEFAULT_MAX_DEPTH = 15


class A2ARouter:
    """A2A 路由引擎 - Worklist 模式"""

    def __init__(self):
        self.max_depth = int(os.getenv("MAX_A2A_DEPTH", str(DEFAULT_MAX_DEPTH)))
        # 每个 thread 的 worklist（供 callback 追加）
        self.thread_worklists: Dict[str, List[str]] = {}
        # 每个 thread 的取消信号
        self.thread_signals: Dict[str, asyncio.Event] = {}
        # 每个 thread 的当前执行状态
        self.thread_states: Dict[str, dict] = {}

    async def route_execution(
        self,
        initial_agents: List[str],
        message: str,
        thread_id: str,
        user_id: str,
        on_agent_start: Optional[callable] = None,
        on_agent_chunk: Optional[callable] = None,
        on_agent_done: Optional[callable] = None,
        on_a2a_complete: Optional[callable] = None,
        on_a2a_cancelled: Optional[callable] = None,
    ) -> AsyncIterator[dict]:
        """执行 A2A 路由，流式返回消息

        Args:
            initial_agents: 初始 Agent 列表
            message: 用户消息
            thread_id: 线程 ID
            user_id: 用户 ID
            on_agent_start: Agent 开始执行回调
            on_agent_chunk: Agent 输出 chunk 回调
            on_agent_done: Agent 完成回调
            on_a2a_complete: A2A 链完成回调
            on_a2a_cancelled: A2A 链取消回调

        Yields:
            dict: 消息事件
        """
        worklist = list(initial_agents)
        a2a_count = 0

        # 创建取消信号
        signal = asyncio.Event()
        self.thread_signals[thread_id] = signal
        self.thread_worklists[thread_id] = worklist

        # 初始化状态
        self.thread_states[thread_id] = {
            "is_running": True,
            "current_agent": "",
            "depth": 0,
            "max_depth": self.max_depth,
        }

        try:
            i = 0
            while i < len(worklist) and a2a_count < self.max_depth:
                # 检查取消信号
                if signal.is_set():
                    logger.info(f"A2A 链被取消: thread_id={thread_id}")
                    if on_a2a_cancelled:
                        await on_a2a_cancelled(thread_id, "用户取消")
                    yield {"type": "a2a_cancelled", "thread_id": thread_id, "reason": "用户取消"}
                    break

                agent_id = worklist[i]

                # 更新状态
                self.thread_states[thread_id].update({
                    "current_agent": agent_id,
                    "depth": a2a_count + 1,
                })

                # 通知 Agent 开始执行
                if on_agent_start:
                    await on_agent_start(agent_id, a2a_count + 1, thread_id)
                yield {"type": "a2a_start", "agent_id": agent_id, "depth": a2a_count + 1}

                # 执行 Agent，流式返回
                full_response = ""
                async for chunk in self._invoke_agent(agent_id, message, thread_id, user_id):
                    # 再次检查取消信号
                    if signal.is_set():
                        logger.info(f"A2A 链在 Agent 执行中被取消: agent_id={agent_id}")
                        if on_a2a_cancelled:
                            await on_a2a_cancelled(thread_id, "用户取消")
                        yield {"type": "a2a_cancelled", "thread_id": thread_id, "reason": "用户取消"}
                        return

                    if isinstance(chunk, str):
                        full_response += chunk
                        if on_agent_chunk:
                            await on_agent_chunk(agent_id, chunk, thread_id)
                        yield {"type": "a2a_chunk", "agent_id": agent_id, "content": chunk}
                    elif isinstance(chunk, dict):
                        # 工具调用结果
                        yield chunk

                # 通知 Agent 完成
                if on_agent_done:
                    await on_agent_done(agent_id, full_response, thread_id)
                yield {"type": "a2a_done", "agent_id": agent_id, "response": full_response}

                # 检查是否有 @mention（通过工具调用）
                mentions = self._extract_mentions_from_tools(full_response)
                if mentions and a2a_count < self.max_depth:
                    for mention in mentions:
                        if mention not in worklist:  # 去重
                            worklist.append(mention)
                            a2a_count += 1
                            logger.info(f"A2A 追加 Agent: {mention}, depth={a2a_count}")

                i += 1

            # 全部完成
            if on_a2a_complete:
                await on_a2a_complete(thread_id)
            yield {"type": "a2a_complete", "is_final": True, "thread_id": thread_id}

        except Exception as e:
            logger.error(f"A2A 路由执行错误: {e}")
            yield {"type": "a2a_error", "error": str(e), "thread_id": thread_id}

        finally:
            # 清理状态
            self.thread_worklists.pop(thread_id, None)
            self.thread_signals.pop(thread_id, None)
            self.thread_states.pop(thread_id, None)

    def _extract_mentions_from_tools(self, response: str) -> List[str]:
        """从 Agent 的工具调用中提取 @mention

        解析 Agent 调用 post_message 工具的参数，提取 target_agent_id

        Args:
            response: Agent 的完整响应文本

        Returns:
            List[str]: 被 mention 的 Agent ID 列表
        """
        import re

        mentions = []

        # 查找 post_message 工具调用
        # 格式: {"invocation_id": "...", "callback_token": "...", "content": "...", "target_agent_id": "..."}
        pattern = r'"target_agent_id"\s*:\s*"([^"]+)"'
        matches = re.findall(pattern, response)

        for match in matches:
            if match and match not in mentions:
                mentions.append(match)

        return mentions

    def enqueue_a2a_targets(self, thread_id: str, targets: List[str]):
        """供 callback 追加 Agent 到 worklist

        Args:
            thread_id: 线程 ID
            targets: 要追加的 Agent ID 列表
        """
        worklist = self.thread_worklists.get(thread_id)
        if worklist:
            for target in targets:
                if target not in worklist:  # 去重
                    worklist.append(target)
                    logger.info(f"Callback 追加 Agent: {target}, thread_id={thread_id}")

    def cancel_thread(self, thread_id: str):
        """取消指定线程的 A2A 链

        Args:
            thread_id: 线程 ID
        """
        signal = self.thread_signals.get(thread_id)
        if signal:
            signal.set()
            logger.info(f"取消 A2A 链: thread_id={thread_id}")

    def get_thread_state(self, thread_id: str) -> Optional[dict]:
        """获取线程的 A2A 执行状态

        Args:
            thread_id: 线程 ID

        Returns:
            Optional[dict]: 状态信息，如果线程不存在返回 None
        """
        return self.thread_states.get(thread_id)

    def is_running(self, thread_id: str) -> bool:
        """检查线程是否有 A2A 链在执行

        Args:
            thread_id: 线程 ID

        Returns:
            bool: 是否在执行
        """
        state = self.thread_states.get(thread_id)
        return state is not None and state.get("is_running", False)

    async def _invoke_agent(
        self,
        agent_id: str,
        message: str,
        thread_id: str,
        user_id: str,
    ) -> AsyncIterator:
        """调用单个 Agent

        Args:
            agent_id: Agent ID
            message: 消息内容
            thread_id: 线程 ID
            user_id: 用户 ID

        Yields:
            Agent 的输出（str 或 dict）
        """
        from .session import session_manager, AGENT_CONFIGS
        from .llm_router import get_llm_service_for_provider
        from .memory_manager import memory_manager, redis_memory_manager

        # 根据 STORAGE_BACKEND 选择存储实例
        # redis_memory_manager 在默认 sqlite 模式下实际就是 sqlite_manager 单例
        memory = redis_memory_manager

        config = AGENT_CONFIGS.get(agent_id)
        if not config:
            yield f"Error: Unknown agent {agent_id}"
            return

        system_prompt = config.get("system_prompt", "")
        provider = config.get("llm_provider", "bailian")

        # 获取上下文
        context = await memory.get_context_for_agent(agent_id, user_id=user_id, thread_id=thread_id)
        agent_message = f"上下文参考:\n{context}\n\n用户消息: {message}" if context else message

        # 创建 invocation 凭证（每个 agent 一次）
        inv_id, cb_token = invocation_registry.create(agent_id, thread_id)

        # 注入 callback 指令到 system_prompt
        system_prompt = prompt_injector.inject_into_system_prompt(
            system_prompt, inv_id, cb_token, agent_id
        )

        try:
            llm = get_llm_service_for_provider(provider)

            # 流式调用 LLM
            for chunk in llm.send_message_stream(
                session_id=f"session_{agent_id}_{thread_id}",
                message=agent_message,
                system_prompt=system_prompt,
            ):
                if isinstance(chunk, str):
                    yield chunk
                elif hasattr(chunk, "choices") and chunk.choices:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content

        except Exception as e:
            logger.error(f"Agent 调用失败: agent_id={agent_id}, error={e}")
            yield f"Error: {str(e)}"


# 全局 A2A 路由器实例
a2a_router = A2ARouter()
