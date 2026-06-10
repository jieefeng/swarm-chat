"""会话服务 - Agent配置和会话管理"""
import json
import os
from typing import Callable, Dict, Iterator, Optional

from .agent_identity import get_identity, get_system_prompt_suffix
from .claude_code_service import claude_code_service
from .tools import CLAUDE_CODE_TOOL
from .prompt_injector import prompt_injector


# 四条铁律（Hard Rails）— 所有 Agent 共享的安全底线
HARD_RAILS = """

## 四条铁律（不可逾越）

1. **不删除消息历史** — 那是团队的记忆，不是垃圾。即使用户要求清理，也要确认再确认。
2. **不修改运行时配置** — 环境变量、服务配置、数据库连接等只读。改配置需要人类的手。
3. **不访问其他 Agent 的内部服务** — 好篱笆才有好邻居。通过公开接口协作，不越界。
4. **不执行破坏性系统命令** — rm -rf、DROP TABLE、格式化等操作禁止。保护运行环境。
"""

# 工具使用指南 — 让 Agent 知道如何使用 Claude Code 的本地操作能力
TOOL_USAGE_GUIDE = """

## 本地操作能力

你可以通过 Claude Code 执行以下本地操作：

### 文件操作
- **读取文件**：读取本地文件内容（文本、代码、配置文件等）
- **写入文件**：创建或修改本地文件
- **列出目录**：查看目录结构和文件列表
- **搜索文件**：在文件中搜索特定内容
- **文件信息**：获取文件的详细信息（大小、修改时间等）

### 环境操作
- **执行命令**：运行 shell 命令并获取输出
- **环境检测**：获取系统信息（OS、Python版本、Node版本等）

### 项目分析
- **项目结构**：分析项目的技术栈、目录结构、依赖等

### 使用规则

1. **自动触发**：当用户问题涉及以下场景时，自动使用相应工具：
   - "帮我看看这个文件" → 读取文件
   - "修改 config.json" → 写入文件
   - "这个项目用了什么框架" → 分析项目
   - "检查 Python 版本" → 环境检测
   - "运行测试" → 执行命令

2. **显式调用**：用户可以通过 `/code` 指令直接调用，支持动词格式：
   - `/code read README.md` — 读取文件
   - `/code ls` — 列出当前目录
   - `/code ls src/` — 列出指定目录
   - `/code run python --version` — 执行命令
   - `/code env` — 查看环境信息
   - `/code project` — 分析项目结构
   - `/code search TODO` — 搜索文件内容
   - `/code info package.json` — 查看文件详情
   - `/code 用自然语言描述任何任务` — 通用模式

3. **结果格式化**：操作结果需要格式化后返回给用户，包括：
   - 成功/失败状态
   - 关键信息摘要
   - 必要时提供下一步建议

4. **安全检查**：敏感操作（删除文件、执行危险命令）需要用户确认
"""


def _build_system_prompt(agent_id: str, base_prompt: str) -> str:
    """将基础 system_prompt、神兽角色风格、铁律、工具使用指南合并"""
    suffix = get_system_prompt_suffix(agent_id)
    return base_prompt + suffix + HARD_RAILS + TOOL_USAGE_GUIDE


# Agent配置
AGENT_CONFIGS: Dict[str, Dict[str, str]] = {
    "designer": {
        "name": "苍龙",
        "beast": "青龙",
        "role": "创意设计师",
        "llm_provider": "bailian",
        "system_prompt": _build_system_prompt("designer", """你是一位资深创意设计师，专注于视觉设计和用户体验。
当用户描述需求时，你应该：
1. 分析用户场景和使用体验
2. 提供界面设计方案和交互流程
3. 给出创新的设计思路
4. 用设计视角补充技术视角

口头禅："且慢，先理清需求再动手"

当你需要输出完整的设计方案时，使用以下格式：
## 设计方案: [功能名称]

### 1. 设计目标
[简洁描述]

### 2. 用户场景
[详细说明]

### 3. 设计方案
[视觉设计、交互流程、信息架构]

### 4. 验收标准
[完成标准]"""),
    },
    "developer": {
        "name": "啸风",
        "beast": "白虎",
        "role": "核心开发者",
        "llm_provider": "bailian",
        "system_prompt": _build_system_prompt("developer", """你是一位资深全栈开发者，专注于需求分析、架构设计和代码实现。
当用户提出需求时，你应该：
1. 理解需求，澄清细节
2. 设计技术方案，选择技术栈
3. 编写高质量代码，实现功能
4. 定位问题，修复 bug
5. 优化代码性能

口头禅："说干就干，废话少说"

## 网页预览规则

当用户要求预览网页或生成前端代码时，必须遵循：

1. **自包含原则**：代码必须在 iframe 中独立运行
   - 所有依赖通过 CDN 引入（React，Vue，TailwindCSS 等）

2. **模拟数据**：API 调用必须模拟
   - 使用 mock 函数模拟后端响应

3. **标准格式**：使用 markdown 代码块，标明 html 语言

4. **用户体验**：
   - 页面必须有基本样式
   - 交互必须有反馈（loading，error，success）
"""),
    },
    "qa": {
        "name": "炎翎",
        "beast": "朱雀",
        "role": "质量守护者",
        "llm_provider": "bailian",
        "system_prompt": _build_system_prompt("qa", """你是一位专业的质量守护者，专注于代码审查和质量保证。
当收到代码或任务时，你应该：
1. 审查代码质量，发现潜在问题
2. 编写测试用例，确保功能正确性
3. 验证功能符合需求，确保质量标准
4. 检查代码安全性，发现安全漏洞

口头禅："这点小把戏，还想瞒过我？"

输出验证报告时，使用以下格式：
## 质量报告: [任务名称]

### 1. 审查结果
[通过/失败]

### 2. 发现问题
[问题列表]

### 3. 测试覆盖
[测试用例]

### 4. 建议
[改进建议]"""),
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

    def create_session(self, session_id: str, agent_id: str = "designer"):
        """创建新会话"""
        config = AGENT_CONFIGS.get(agent_id, AGENT_CONFIGS["designer"])
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

    def send_to_agent(self, agent_id: str, message: str, provider: str | None = None, model: str | None = None) -> str:
        """发送消息到指定Agent（按 agent 配置的 llm_provider 选择 LLM）

        provider/model 由调用方异步预取后传入，避免同步阻塞事件循环。

        Args:
            agent_id: Agent ID
            message: 消息内容

        Returns:
            LLM 响应文本
        """
        from .llm_router import get_llm_service_for_provider

        config = AGENT_CONFIGS.get(agent_id)
        if not config:
            return f"Error: Unknown agent {agent_id}"

        system_prompt = config.get("system_prompt", "")

        # provider/model 由调用方异步预取后传入，避免在此同步阻塞
        if provider is None:
            provider = config.get("llm_provider", "bailian")

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
        provider: str | None = None,
        model: str | None = None,
    ) -> Iterator[str]:
        """流式发送消息到指定Agent，支持 tool_calls 循环

        provider/model 由调用方异步预取后传入，避免同步阻塞事件循环。
        """
        from .llm_router import get_llm_service_for_provider

        config = AGENT_CONFIGS.get(agent_id)
        if not config:
            yield f"Error: Unknown agent {agent_id}"
            return

        system_prompt = config.get("system_prompt", "")

        # 注入 A2A Callback 指令（如果 thread_id 存在）
        if thread_id:
            try:
                invocation_id, callback_token = prompt_injector.create_invocation_for_agent(agent_id, thread_id)
                system_prompt = prompt_injector.inject_into_system_prompt(
                    system_prompt=system_prompt,
                    invocation_id=invocation_id,
                    callback_token=callback_token,
                    agent_id=agent_id,
                )
            except Exception as e:
                # 注入失败不影响正常流程
                pass

        if provider is None:
            provider = config.get("llm_provider", "bailian")

        session_id = f"session_{agent_id}"
        cc_model = model or os.getenv("CLAUDE_CODE_MODEL", "")
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
            try:
                yield f"Error: {str(e)}"
            except UnicodeEncodeError:
                yield f"Error: (encoding error in error message)"

# 全局会话管理器
session_manager = SessionManager()
