"""会话服务 - Agent配置和会话管理"""
import json
import os
from typing import Callable, Dict, Iterator, Optional

from .agent_identity import get_identity, get_system_prompt_suffix
from .claude_code_service import claude_code_service
from .tools import CLAUDE_CODE_TOOL


# 四条铁律（Hard Rails）— 所有 Agent 共享的安全底线
HARD_RAILS = """

## 四条铁律（不可逾越）

1. **不删除消息历史** — 那是团队的记忆，不是垃圾。即使用户要求清理，也要确认再确认。
2. **不修改运行时配置** — 环境变量、服务配置、数据库连接等只读。改配置需要人类的手。
3. **不访问其他 Agent 的内部服务** — 好篱笆才有好邻居。通过公开接口协作，不越界。
4. **不执行破坏性系统命令** — rm -rf、DROP TABLE、格式化等操作禁止。保护运行环境。
"""


def _build_system_prompt(agent_id: str, base_prompt: str) -> str:
    """将基础 system_prompt、神兽角色风格、铁律合并"""
    suffix = get_system_prompt_suffix(agent_id)
    return base_prompt + suffix + HARD_RAILS


# Agent配置
AGENT_CONFIGS: Dict[str, Dict[str, str]] = {
    "pm": {
        "name": "苍龙",
        "beast": "青龙",
        "role": "产品经理（PM）",
        "llm_provider": "bailian",
        "system_prompt": _build_system_prompt("pm", """你是一个资深产品经理，专注于需求分析和用户体验设计。
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
[完成标准]"""),
    },
    "architect": {
        "name": "玄冥",
        "beast": "玄武",
        "role": "系统架构师",
        "llm_provider": "bailian",
        "system_prompt": _build_system_prompt("architect", """你是一个资深系统架构师，专注于技术方案设计和架构决策。
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
[完成标准]"""),
    },
    "developer": {
        "name": "啸风",
        "beast": "白虎",
        "role": "developer",
        "llm_provider": "bailian",
        "system_prompt": _build_system_prompt("developer", """你是一位资深全栈开发者。根据架构师的设计方案，编写高质量的代码实现。遵循 SOLID 原则，编写清晰、可维护的代码。输出代码时使用 markdown 代码块，标明文件路径和语言。

## 网页预览规则

当用户要求预览网页或生成前端代码时，必须遵循：

1. **自包含原则**：代码必须在 iframe 中独立运行
   - 所有依赖通过 CDN 引入（React，Vue，TailwindCSS 等）
   - 示例：通过 CDN 引入所需依赖

2. **模拟数据**：API 调用必须模拟
   - 使用 mock 函数模拟后端响应
   - 提供测试数据和提示信息

3. **标准格式**：使用 markdown 代码块，标明 html 语言

4. **用户体验**：
   - 页面必须有基本样式
   - 交互必须有反馈（loading，error，success）
   - 提供操作提示（如测试账号提示）
"""),
    },
    "qa": {
        "name": "炎翎",
        "beast": "朱雀",
        "role": "qa",
        "llm_provider": "bailian",
        "system_prompt": _build_system_prompt("qa", "你是一位专业的 QA 工程师。审查开发者提交的代码，验证功能正确性、边界情况和代码质量。输出验证报告，标明通过/失败及原因。"),
    },
    "orchestrator": {
        "name": "瑞麟",
        "beast": "麒麟",
        "role": "orchestrator",
        "llm_provider": "bailian",
        "system_prompt": _build_system_prompt("orchestrator", "你是任务协调器。分析用户需求，将其拆解为可执行的任务列表，以 JSON 格式输出。每个任务包含 title, description, assigned_to, depends_on, priority 字段。如果需求不清晰，设置 requires_clarification=true 并提供 clarification_question。"),
    },
}


class SessionManager:
    """管理会话状态"""

    def __init__(self):
        self.sessions: Dict[str, dict] = {}

    def create_session(self, session_id: str, agent_id: str = "pm"):
        """创建新会话"""
        config = AGENT_CONFIGS.get(agent_id, AGENT_CONFIGS["pm"])
        self.sessions[session_id] = {
            "agent_id": agent_id,
            "messages": [],
            "system_prompt": config.get("system_prompt", "")
        }

    def get_session(self, session_id: str) -> Optional[dict]:
        """获取会话"""
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str):
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def send_to_agent(self, agent_id: str, message: str) -> str:
        """发送消息到指定Agent（按 agent 配置的 llm_provider 选择 LLM）

        优先从数据库读取 provider 和 model，回退到 AGENT_CONFIGS 默认值

        Args:
            agent_id: Agent ID
            message: 消息内容

        Returns:
            LLM 响应文本
        """
        from .llm_router import get_llm_service_for_provider
        from .llm_config_db import LLMConfigDB

        config = AGENT_CONFIGS.get(agent_id)
        if not config:
            return f"Error: Unknown agent {agent_id}"

        system_prompt = config.get("system_prompt", "")

        # 从数据库读取 provider 和 model，回退到默认值
        db = LLMConfigDB()
        provider = db.get_provider(agent_id) or config.get("llm_provider", "bailian")
        model = db.get_model(agent_id)  # None 时使用默认模型

        session_id = f"session_{agent_id}"

        try:
            llm = get_llm_service_for_provider(provider, model=model)
            response = llm.send_message(
                session_id=session_id,
                message=message,
                system_prompt=system_prompt
            )
            return response
        except Exception as e:
            return f"Error: {str(e)}"

    def send_to_agent_stream(
        self,
        agent_id: str,
        message: str,
        context: str = "",
        message_history: list[dict] | None = None,
        thread_id: str | None = None,
        on_tool_start: Callable | None = None,
        on_tool_progress: Callable | None = None,
        on_tool_result: Callable | None = None,
    ) -> Iterator[str]:
        """流式发送消息到指定Agent，支持 tool_calls 循环"""
        from .llm_router import get_llm_service_for_provider
        from .llm_config_db import LLMConfigDB

        config = AGENT_CONFIGS.get(agent_id)
        if not config:
            yield f"Error: Unknown agent {agent_id}"
            return

        system_prompt = config.get("system_prompt", "")

        db = LLMConfigDB()
        provider = db.get_provider(agent_id) or config.get("llm_provider", "bailian")
        model = db.get_model(agent_id)

        session_id = f"session_{agent_id}"
        cc_model = db.get_model(agent_id) or os.getenv("CLAUDE_CODE_MODEL", "")
        tools = [CLAUDE_CODE_TOOL] if claude_code_service.is_available() else None
        max_rounds = int(os.getenv("CLAUDE_CODE_MAX_ROUNDS", "3"))

        try:
            llm = get_llm_service_for_provider(provider, model=model)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ]

            for round_num in range(max_rounds + 1):
                accumulated_content = ""
                tool_calls_map: dict[str, dict] = {}

                # 第一轮使用原始消息，后续轮次使用空消息（因为 messages 列表已包含上下文）
                current_message = message if round_num == 0 else ""
                current_system = system_prompt if round_num == 0 else ""

                for chunk in llm.send_message_stream(
                    session_id=session_id,
                    message=current_message,
                    system_prompt=current_system,
                    tools=tools,
                    tool_choice="auto" if tools else None,
                ):
                    if tools and hasattr(chunk, "choices") and chunk.choices:
                        delta = chunk.choices[0].delta
                        if delta.content:
                            accumulated_content += delta.content
                            yield delta.content
                        if delta.tool_calls:
                            for tc in delta.tool_calls:
                                tc_id = tc.id or ""
                                if tc_id not in tool_calls_map:
                                    tool_calls_map[tc_id] = {"name": "", "arguments": ""}
                                if tc.function:
                                    if tc.function.name:
                                        tool_calls_map[tc_id]["name"] = tc.function.name
                                    if tc.function.arguments:
                                        tool_calls_map[tc_id]["arguments"] += tc.function.arguments
                    else:
                        if isinstance(chunk, str):
                            accumulated_content += chunk
                            yield chunk

                if not tool_calls_map:
                    break

                for tc_id, tc_info in tool_calls_map.items():
                    try:
                        prompt = json.loads(tc_info["arguments"]).get("prompt", "")
                    except (json.JSONDecodeError, AttributeError):
                        yield f"\n[错误: 无法解析 tool_call 参数]\n"
                        continue

                    if not prompt:
                        continue

                    # 拼接上下文到 prompt
                    full_prompt = f"{context}\n\n{prompt}" if context else prompt

                    if on_tool_start:
                        on_tool_start(agent_id, full_prompt, thread_id=thread_id)

                    result = claude_code_service.execute(
                        full_prompt,
                        model=cc_model,
                        on_progress=(lambda output: on_tool_progress(agent_id, output, thread_id=thread_id))
                        if on_tool_progress
                        else None,
                    )

                    if on_tool_result:
                        on_tool_result(agent_id, result.output, result.success, thread_id=thread_id)

                    messages.append({
                        "role": "assistant",
                        "tool_calls": [{
                            "id": tc_id,
                            "type": "function",
                            "function": {
                                "name": tc_info["name"],
                                "arguments": tc_info["arguments"],
                            },
                        }],
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "content": result.output if result.success else f"Error: {result.error}",
                    })

                session_id = f"session_{agent_id}_tool_{round_num}"

        except Exception as e:
            yield f"Error: {str(e)}"

# 全局会话管理器
session_manager = SessionManager()
