"""会话服务 - Agent配置和会话管理"""
from typing import Dict, Optional


# Agent配置
AGENT_CONFIGS: Dict[str, Dict[str, str]] = {
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
    },
    "developer": {
        "name": "开发者",
        "role": "developer",
        "system_prompt": "你是一位资深全栈开发者。根据架构师的设计方案，编写高质量的代码实现。遵循 SOLID 原则，编写清晰、可维护的代码。输出代码时使用 markdown 代码块，标明文件路径和语言。"
    },
    "qa": {
        "name": "QA工程师",
        "role": "qa",
        "system_prompt": "你是一位专业的 QA 工程师。审查开发者提交的代码，验证功能正确性、边界情况和代码质量。输出验证报告，标明通过/失败及原因。"
    },
    "orchestrator": {
        "name": "协调器",
        "role": "orchestrator",
        "system_prompt": "你是任务协调器。分析用户需求，将其拆解为可执行的任务列表，以 JSON 格式输出。每个任务包含 title, description, assigned_to, depends_on, priority 字段。如果需求不清晰，设置 requires_clarification=true 并提供 clarification_question。"
    }
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
        """发送消息到指定Agent（同步调用Claude API）

        Args:
            agent_id: Agent ID
            message: 消息内容

        Returns:
            Claude响应文本
        """
        from .llm_router import get_llm_service

        config = AGENT_CONFIGS.get(agent_id)
        if not config:
            return f"Error: Unknown agent {agent_id}"

        system_prompt = config.get("system_prompt", "")
        session_id = f"session_{agent_id}"

        try:
            llm = get_llm_service()
            response = llm.send_message(
                session_id=session_id,
                message=message,
                system_prompt=system_prompt
            )
            return response
        except Exception as e:
            return f"Error: {str(e)}"


# 全局会话管理器
session_manager = SessionManager()