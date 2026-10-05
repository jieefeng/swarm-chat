"""存储后端降级测试"""
import pytest
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMemoryFallback:
    """测试 Redis 不可用时的降级行为"""

    def test_redis_fallback_on_connection_error(self):
        """Redis 连接失败时降级到 SQLite"""
        from agenthub.backend.services.sqlite_manager import SQLiteManager
        from agenthub.backend.services.memory_manager import create_memory_manager
        with patch.dict(os.environ, {
            "STORAGE_BACKEND": "redis",
            # 本机必无监听的端口：立即得到 connection refused，不依赖 DNS（invalid-host 解析耗时不稳定）
            "REDIS_URL": "redis://127.0.0.1:1"
        }):
            manager = create_memory_manager()
            # 应该降级为 SQLiteManager
            assert isinstance(manager, SQLiteManager)
