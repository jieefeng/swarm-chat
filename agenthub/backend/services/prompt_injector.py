"""Prompt 注入器 - 在系统提示词里注入 HTTP callback 指令

让 Agent 通过 HTTP 请求与团队协作，支持：
- 发送消息给团队（post_message）
- 获取对话上下文（thread-context）
- 获取待处理的 @提及（pending-mentions）

参考：Cat Café 项目（zts212653/clowder-ai）
"""
import os
import logging
from typing import Optional

from .invocation_registry import invocation_registry

logger = logging.getLogger(__name__)

# 默认 API URL
DEFAULT_API_URL = "http://localhost:7010"


class PromptInjector:
    """在系统提示词里注入 HTTP callback 指令"""

    def __init__(self, api_url: Optional[str] = None):
        self.api_url = api_url or os.getenv("API_URL", DEFAULT_API_URL)

    def build_callback_instructions(
        self,
        invocation_id: str,
        callback_token: str,
        agent_id: str,
    ) -> str:
        """构建 callback 指令

        Args:
            invocation_id: Invocation ID
            callback_token: Callback Token
            agent_id: Agent ID（用于工作流触发点）

        Returns:
            str: callback 指令文本
        """
        # 根据 agent_id 构建工作流触发点
        workflow_triggers = self._build_workflow_triggers(agent_id)

        return f"""
## 团队协作工具

你可以通过 HTTP 请求与团队其他成员协作。

### 发送消息给团队

```bash
curl -X POST {self.api_url}/api/callbacks/post-message \\
  -H "Content-Type: application/json" \\
  -d '{{
    "invocation_id": "{invocation_id}",
    "callback_token": "{callback_token}",
    "content": "你的消息",
    "target_agent_id": "目标Agent ID（可选，用于@mention）"
  }}'
```

### 获取对话上下文

```bash
curl -X GET "{self.api_url}/api/callbacks/thread-context?invocation_id={invocation_id}&callback_token={callback_token}"
```

### 获取待处理的 @提及

```bash
curl -X GET "{self.api_url}/api/callbacks/pending-mentions?invocation_id={invocation_id}&callback_token={callback_token}"
```

### 使用规则

1. **主动发消息**：当你完成任务或有重要发现时，主动调用 post_message 告知团队
2. **@mention 其他 Agent**：当你需要其他 Agent 协助时，设置 target_agent_id
3. **获取上下文**：当你需要了解对话历史时，调用 thread-context
4. **检查 @提及**：当你被 @mention 时，调用 pending-mentions 获取详情

### 工作流触发点

{workflow_triggers}

### 注意事项

- 凭证有效期为 1 小时，过期后需要重新获取
- 每次调用都会消耗 API 配额，请合理使用
- 如果遇到 401 错误，说明凭证已过期，请停止调用
"""

    def _build_workflow_triggers(self, agent_id: str) -> str:
        """根据 agent_id 构建工作流触发点

        Args:
            agent_id: Agent ID

        Returns:
            str: 工作流触发点文本
        """
        # 通用触发点
        common_triggers = """
- 完成任务后 → 主动告知团队
- 发现问题时 → @相关 Agent
- 需要帮助时 → @有能力的 Agent
"""

        # 根据 Agent 角色添加特定触发点
        agent_triggers = {
            "designer": """
- 完成需求分析 → @developer（开发者）进行技术评估
- 需要澄清需求 → @用户
- 完成设计方案 → @developer（开发者）开始实现
""",
            "developer": """
- 完成代码实现 → @qa（测试）进行测试
- 遇到技术问题 → @designer（设计师）寻求指导
- 需要需求澄清 → @designer（设计师）
""",
            "qa": """
- 完成测试 → @developer（开发者）修复问题
- 发现 bug → @developer（开发者）
- 测试通过 → @orchestrator（协调器）确认完成
""",
            "orchestrator": """
- 任务拆解完成 → 分配给相应 Agent
- 进度更新 → 通知所有相关 Agent
- 发现阻塞 → 协调解决
""",
        }

        triggers = agent_triggers.get(agent_id, "")
        return common_triggers + triggers

    def inject_into_system_prompt(
        self,
        system_prompt: str,
        invocation_id: str,
        callback_token: str,
        agent_id: str,
    ) -> str:
        """将 callback 指令注入到系统提示词

        Args:
            system_prompt: 原始系统提示词
            invocation_id: Invocation ID
            callback_token: Callback Token
            agent_id: Agent ID

        Returns:
            str: 注入后的系统提示词
        """
        instructions = self.build_callback_instructions(invocation_id, callback_token, agent_id)
        return f"{system_prompt}\n\n{instructions}"

    def create_invocation_for_agent(
        self,
        agent_id: str,
        thread_id: str,
    ) -> tuple[str, str]:
        """为 Agent 创建 invocation 凭证

        Args:
            agent_id: Agent ID
            thread_id: 线程 ID

        Returns:
            tuple[str, str]: (invocation_id, callback_token)
        """
        return invocation_registry.create(agent_id, thread_id)


# 全局 prompt injector 实例
prompt_injector = PromptInjector()
