# AgentHub Agent 定义

本目录包含 AgentHub 项目中 4 个核心 Agent 的定义和配置。

## 目录结构

```
muiltAgent/
├── .claude/
│   └── settings.json          # Agent 定义（subagents 配置）
├── docs/superpowers/specs/
│   ├── 2026-05-24-agenthub-pm-agent-design.md
│   ├── 2026-05-24-agenthub-architect-agent-design.md
│   ├── 2026-05-24-agenthub-developer-agent-design.md
│   └── 2026-05-24-agenthub-qa-agent-design.md
└── README.md                  # 本文件
```

## Agent 列表

| Agent ID | 角色 | Team Role | 核心职责 |
|----------|------|-----------|----------|
| `agenthub-pm` | 产品经理 | **Team Lead** | 需求分析、用户故事、优先级排序 |
| `agenthub-architect` | 技术架构师 | **Teammate** | 技术可行性、架构设计、代码 Diff |
| `agenthub-developer` | 全栈开发者 | **Teammate** | 代码实现、调试修复、一键部署 |
| `agenthub-qa` | 测试架构师 | **Teammate** | 测试策略、缺陷管理、质量报告 |

## 使用方式

### 方式 1：在 Claude Code 中直接引用

```bash
# 在 Claude Code 会话中启用 Agent Teams
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# 告诉 Claude 创建团队并使用 subagent 定义
Create an agent team to analyze requirements for [产品名称].
Spawn teammates using agenthub-pm, agenthub-architect, and agenthub-qa agent types.
```

### 方式 2：通过 settings.json 加载

Agent 定义已集成到 `.claude/settings.json`，Claude Code 启动时会自动加载。

```json
{
  "subagents": {
    "agenthub-pm": {
      "description": "Product Manager Agent for AgentHub - Team Lead",
      "model": "opus",
      "prompt": "..."
    }
  }
}
```

## Agent Teams 协作流程

```
用户输入需求
       │
       ▼
┌──────────────────────────────────────┐
│     PM Agent（Team Lead）            │
│  - 创建 Task List                    │
│  - 分配任务给 teammates              │
│  - 综合结果                          │
└──────────────────┬───────────────────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │Architect│ │Developer│ │   QA     │
   │ Teammate│ │ Teammate│ │Teammate  │
   └─────────┘ └─────────┘ └─────────┘
        │          │          │
        └──────────┼──────────┘
                   ▼
        Mailbox 互相通信
```

## 核心机制

### Shared Task List
- 任务状态：`pending → in-progress → completed`
- 任务依赖：被阻止的任务需等待前置任务完成

### Mailbox
- teammates 之间直接通信
- 无需通过 Team Lead 中转

### 显示模式
- **In-process**：Shift+Down 切换 teammates
- **Split panes**：需要 tmux，每个 teammate 独立窗格

## 相关文档

- [Claude Code Agent Teams 官方文档](https://code.claude.com/docs/en/agent-teams)
- [PM Agent 详细定义](./docs/superpowers/specs/2026-05-24-agenthub-pm-agent-design.md)
- [Architect Agent 详细定义](./docs/superpowers/specs/2026-05-24-agenthub-architect-agent-design.md)
- [Developer Agent 详细定义](./docs/superpowers/specs/2026-05-24-agenthub-developer-agent-design.md)
- [QA Agent 详细定义](./docs/superpowers/specs/2026-05-24-agenthub-qa-agent-design.md)