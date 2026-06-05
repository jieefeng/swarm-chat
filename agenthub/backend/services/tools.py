"""LLM Tool 定义 — 用于 OpenAI 兼容 API 的 tools 参数"""

CLAUDE_CODE_TOOL = {
    "type": "function",
    "function": {
        "name": "claude_code",
        "description": (
            "调用 Claude Code CLI 执行开发任务。可用于："
            "读取/写入/编辑文件、搜索代码、执行命令（如运行测试、构建项目）、"
            "分析项目结构等。适用于需要访问文件系统或执行操作的场景。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "要 Claude Code 执行的具体任务描述，应清晰明确",
                }
            },
            "required": ["prompt"],
        },
    },
}
