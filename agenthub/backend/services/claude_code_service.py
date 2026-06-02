"""Claude Code CLI 封装 — 通过 subprocess 调用 claude 命令执行开发任务"""
import json
import os
import subprocess
import time
from dataclasses import dataclass
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

    def __init__(self, timeout: int = 300, max_turns: int = 10):
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


# 全局实例
claude_code_service = ClaudeCodeService(
    timeout=int(os.getenv("CLAUDE_CODE_TIMEOUT", "300")),
    max_turns=int(os.getenv("CLAUDE_CODE_MAX_TURNS", "10")),
)
