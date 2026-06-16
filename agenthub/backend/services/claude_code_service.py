"""Claude Code CLI 封装 — 通过 subprocess 调用 claude 命令执行开发任务"""
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional


@dataclass
class ClaudeCodeResult:
    """Claude Code 执行结果"""
    success: bool
    output: str
    error: str = ""
    duration_ms: int = 0


class ClaudeCodeService:
    """封装 Claude Code CLI 的调用"""

    def __init__(self, timeout: int = 120, max_turns: int = 10):
        self.timeout = timeout
        self.max_turns = max_turns

    def is_available(self) -> bool:
        """检测 Claude Code CLI 是否安装"""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def execute(
        self,
        prompt: str,
        model: str = "",
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> ClaudeCodeResult:
        """执行 Claude Code CLI"""
        if not self.is_available():
            return ClaudeCodeResult(
                success=False,
                output="",
                error="Claude Code CLI 未安装。请运行 npm install -g @anthropic-ai/claude-code 安装。",
            )

        cmd = [
            "claude", "-p", prompt,
            "--output-format", "stream-json",
            "--max-turns", str(self.max_turns),
        ]
        if model:
            cmd.extend(["--model", model])

        start_time = time.monotonic()
        output_lines: list[str] = []

        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8",
            )

            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    event_type = event.get("type", "")
                    if event_type == "text":
                        text = event.get("text", "")
                        if text and on_progress:
                            on_progress(text)
                    elif event_type == "result":
                        result_text = event.get("result", "")
                        if result_text:
                            output_lines.append(result_text)
                    elif event_type == "tool_use":
                        tool_name = event.get("tool", {}).get("name", "unknown")
                        if on_progress:
                            on_progress(f"[工具调用: {tool_name}]")
                    elif event_type == "tool_result":
                        tool_output = event.get("output", "")
                        if tool_output:
                            output_lines.append(tool_output)
                except json.JSONDecodeError:
                    output_lines.append(line)
                    if on_progress:
                        on_progress(line)

            proc.wait(timeout=self.timeout)
            duration_ms = int((time.monotonic() - start_time) * 1000)

            if proc.returncode != 0:
                stderr = proc.stderr.read() if proc.stderr else ""
                return ClaudeCodeResult(
                    success=False, output="\n".join(output_lines),
                    error=stderr or f"进程退出码: {proc.returncode}",
                    duration_ms=duration_ms,
                )

            return ClaudeCodeResult(
                success=True, output="\n".join(output_lines),
                duration_ms=duration_ms,
            )

        except subprocess.TimeoutExpired:
            proc.kill()
            duration_ms = int((time.monotonic() - start_time) * 1000)
            return ClaudeCodeResult(
                success=False, output="\n".join(output_lines),
                error=f"执行超时（{self.timeout}秒）", duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            return ClaudeCodeResult(
                success=False, output="\n".join(output_lines),
                error=str(e), duration_ms=duration_ms,
            )

    # ==================== 工具函数封装 ====================

    def read_file(self, path: str, encoding: str = "utf-8") -> ClaudeCodeResult:
        """读取文件内容

        Args:
            path: 文件路径（绝对或相对路径）
            encoding: 文件编码，默认 utf-8

        Returns:
            ClaudeCodeResult，成功时 output 包含文件内容
        """
        prompt = f"读取文件 {path} 的完整内容并原样输出，不要添加任何解释。如果文件不存在，输出错误信息。"
        return self.execute(prompt)

    def write_file(self, path: str, content: str, encoding: str = "utf-8") -> ClaudeCodeResult:
        """写入文件内容

        Args:
            path: 文件路径（绝对或相对路径）
            content: 要写入的内容
            encoding: 文件编码，默认 utf-8

        Returns:
            ClaudeCodeResult，成功时 output 包含写入结果
        """
        # 截断过长内容以避免 prompt 过大
        display_content = content[:5000] + "..." if len(content) > 5000 else content
        prompt = f"""将以下内容写入文件 {path}：

```
{display_content}
```

如果目录不存在，自动创建。写入完成后输出文件路径和字节数。"""
        return self.execute(prompt)

    def list_dir(self, path: str = ".", recursive: bool = False) -> ClaudeCodeResult:
        """列出目录内容

        Args:
            path: 目录路径，默认当前目录
            recursive: 是否递归列出子目录

        Returns:
            ClaudeCodeResult，成功时 output 包含目录列表
        """
        if recursive:
            prompt = f"递归列出目录 {path} 的所有文件和子目录，使用树形结构展示。"
        else:
            prompt = f"列出目录 {path} 下的文件和子目录，显示文件大小和修改时间。"
        return self.execute(prompt)

    def run_command(self, cmd: str, cwd: str = "") -> ClaudeCodeResult:
        """执行 shell 命令

        Args:
            cmd: 要执行的命令
            cwd: 工作目录，默认当前目录

        Returns:
            ClaudeCodeResult，成功时 output 包含命令输出
        """
        cwd_info = f"在目录 {cwd} 下" if cwd else ""
        prompt = f"{cwd_info}执行命令 `{cmd}`，输出命令的 stdout 和 stderr。如果命令失败，输出错误信息和退出码。"
        return self.execute(prompt)

    def get_env_info(self) -> ClaudeCodeResult:
        """获取系统环境信息

        Returns:
            ClaudeCodeResult，成功时 output 包含环境信息
        """
        prompt = """获取当前系统环境信息，包括：
1. 操作系统版本
2. Python 版本
3. Node.js 版本（如果安装）
4. 已安装的主要开发工具（git, docker 等）
5. 环境变量中的关键配置（不包含敏感信息）

以结构化格式输出。"""
        return self.execute(prompt)

    def analyze_project(self, path: str = ".") -> ClaudeCodeResult:
        """分析项目结构

        Args:
            path: 项目根目录路径

        Returns:
            ClaudeCodeResult，成功时 output 包含项目分析结果
        """
        prompt = f"""分析目录 {path} 的项目结构，包括：
1. 项目类型（前端/后端/全栈等）
2. 使用的框架和技术栈
3. 主要目录结构
4. 依赖管理方式（package.json, requirements.txt 等）
5. 配置文件列表
6. 入口文件

以结构化格式输出分析结果。"""
        return self.execute(prompt)

    def search_in_files(self, pattern: str, path: str = ".", file_pattern: str = "") -> ClaudeCodeResult:
        """在文件中搜索内容

        Args:
            pattern: 搜索的正则表达式或文本
            path: 搜索的目录路径
            file_pattern: 文件过滤模式（如 *.py）

        Returns:
            ClaudeCodeResult，成功时 output 包含搜索结果
        """
        file_info = f"只在 {file_pattern} 文件中" if file_pattern else ""
        prompt = f"在目录 {path} 下{file_info}搜索 '{pattern}'，输出匹配的文件名、行号和内容。"
        return self.execute(prompt)

    def get_file_info(self, path: str) -> ClaudeCodeResult:
        """获取文件详细信息

        Args:
            path: 文件路径

        Returns:
            ClaudeCodeResult，成功时 output 包含文件信息
        """
        prompt = f"获取文件 {path} 的详细信息，包括：文件大小、修改时间、权限、文件类型。"
        return self.execute(prompt)


# 全局实例
claude_code_service = ClaudeCodeService(
    timeout=int(os.getenv("CLAUDE_CODE_TIMEOUT", "300")),
    max_turns=int(os.getenv("CLAUDE_CODE_MAX_TURNS", "10")),
)
