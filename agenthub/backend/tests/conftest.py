"""测试公共配置：把仓库根目录加入 sys.path。

各测试文件通过 `from agenthub.backend...` 导入被测代码，该包路径
只有以仓库根为起点才能解析；没有这一步，`pytest tests/test_xxx.py`
单文件运行时会 ModuleNotFoundError。
"""
import os
import sys

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
)

# 跳过 mock LLM 的流式打字机延迟（每 chunk 一次阻塞 sleep，会拖慢且卡住事件循环）
os.environ.setdefault("MOCK_LLM_STREAM_DELAY", "0")

import asyncio

import pytest


@pytest.fixture(scope="session", autouse=True)
def _close_shared_sqlite():
    """会话结束后关闭全局 SQLiteManager 单例连接。

    测试里 TestClient 不用 `with`（lifespan 不运行，close_db 不会触发），
    且各测试用 `asyncio.run` 在临时事件循环里调用 init_db。aiosqlite 的
    连接工作线程是非 daemon 线程，连接不关进程就永远退不出去——表现为
    "202 passed" 打印完 pytest 仍然挂死。
    """
    yield
    from agenthub.backend.services.database import sqlite_manager

    if sqlite_manager._db is not None:
        try:
            asyncio.run(sqlite_manager.close())
        except Exception:
            pass
