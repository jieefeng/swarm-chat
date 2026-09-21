"""数据库单例模块 - 共享 SQLiteManager 实例

所有路由通过 get_db() 获取同一个已初始化的 SQLiteManager，
避免各处自建连接导致路径不一致与冗余实例。
LLM 配置表 (agent_llm_config) 在首次 get_db() 时确保 schema 就绪。
"""
import os
import logging
from pathlib import Path

from agenthub.backend.services.sqlite_manager import SQLiteManager

logger = logging.getLogger(__name__)

# 数据库文件路径：DB_PATH 环境变量优先，默认 backend/data/agenthub.db
_DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "agenthub.db"
DB_PATH = os.getenv("DB_PATH", str(_DEFAULT_DB_PATH))

# 全局单例：与 memory_manager.create_memory_manager() 共用同一实例
sqlite_manager = SQLiteManager(DB_PATH)

_initialized = False


async def get_db() -> SQLiteManager:
    """获取已初始化的 SQLiteManager 单例。

    首次调用时建立连接并确保 LLM 配置表 schema 就绪；
    后续调用直接返回同一实例。
    """
    global _initialized
    if not _initialized:
        # 确保数据目录存在
        os.makedirs(os.path.dirname(str(DB_PATH)), exist_ok=True)
        await sqlite_manager.init_db()

        # LLM 配置表复用同一底层连接
        from agenthub.backend.services.llm_config_db import LLMConfigDB

        await LLMConfigDB(sqlite_manager._db).ensure_schema()
        _initialized = True
        logger.info("Database initialized: %s", DB_PATH)
    return sqlite_manager


async def close_db() -> None:
    """关闭单例连接（应用停机时调用）。"""
    global _initialized
    if _initialized:
        await sqlite_manager.close()
        _initialized = False
        logger.info("Database closed")
