"""ClaudeCodeService 单元测试"""
import subprocess
import sys
import os
from unittest.mock import patch, MagicMock
import pytest

# 添加父目录到路径以导入模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agenthub.backend.services.claude_code_service import ClaudeCodeService, ClaudeCodeResult


class TestClaudeCodeService:
    """ClaudeCodeService 测试"""

    def test_is_available_returns_true_when_installed(self):
        service = ClaudeCodeService()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert service.is_available() is True

    def test_is_available_returns_false_when_not_installed(self):
        service = ClaudeCodeService()
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert service.is_available() is False

    def test_is_available_returns_false_on_nonzero(self):
        service = ClaudeCodeService()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            assert service.is_available() is False

    def test_execute_returns_success_result(self):
        service = ClaudeCodeService()
        with patch.object(service, "is_available", return_value=True):
            with patch("subprocess.Popen") as mock_popen:
                mock_proc = MagicMock()
                mock_proc.stdout.__iter__ = MagicMock(return_value=iter([
                    '{"type":"result","result":"文件内容"}\n'
                ]))
                mock_proc.wait.return_value = 0
                mock_proc.returncode = 0
                mock_popen.return_value = mock_proc
                result = service.execute("读取 main.py")
                assert result.success is True
                assert "文件内容" in result.output

    def test_execute_returns_error_when_not_available(self):
        service = ClaudeCodeService()
        with patch.object(service, "is_available", return_value=False):
            result = service.execute("读取 main.py")
            assert result.success is False
            assert "未安装" in result.error

    def test_execute_calls_on_progress(self):
        service = ClaudeCodeService()
        progress_calls = []
        with patch.object(service, "is_available", return_value=True):
            with patch("subprocess.Popen") as mock_popen:
                mock_proc = MagicMock()
                mock_proc.stdout.__iter__ = MagicMock(return_value=iter([
                    '{"type":"text","text":"正在读取..."}\n',
                    '{"type":"result","result":"完成"}\n'
                ]))
                mock_proc.wait.return_value = 0
                mock_proc.returncode = 0
                mock_popen.return_value = mock_proc
                result = service.execute("读取 main.py", on_progress=lambda x: progress_calls.append(x))
                assert len(progress_calls) > 0

    def test_execute_with_model_passes_model_flag(self):
        service = ClaudeCodeService()
        with patch.object(service, "is_available", return_value=True):
            with patch("subprocess.Popen") as mock_popen:
                mock_proc = MagicMock()
                mock_proc.stdout.__iter__ = MagicMock(return_value=iter([
                    '{"type":"result","result":"ok"}\n'
                ]))
                mock_proc.wait.return_value = 0
                mock_proc.returncode = 0
                mock_popen.return_value = mock_proc
                service.execute("test", model="qwen-plus")
                call_args = mock_popen.call_args[0][0]
                assert "--model" in call_args
                assert "qwen-plus" in call_args

    def test_execute_timeout_terminates_process(self):
        service = ClaudeCodeService(timeout=1)
        with patch.object(service, "is_available", return_value=True):
            with patch("subprocess.Popen") as mock_popen:
                mock_proc = MagicMock()
                mock_proc.stdout.__iter__ = MagicMock(return_value=iter([]))
                mock_proc.wait.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=1)
                mock_popen.return_value = mock_proc
                result = service.execute("长时间任务")
                assert result.success is False
                assert "超时" in result.error
                mock_proc.kill.assert_called_once()
