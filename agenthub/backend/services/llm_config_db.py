"""LLM 配置数据库模块 - 管理 Agent 的 LLM Provider 配置

使用注入的 aiosqlite.Connection，复用 database.py 的单例连接，
避免每次调用创建 3 个同步连接阻塞事件循环。
"""
import aiosqlite
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class LLMConfigDB:
    """LLM 配置数据库封装（异步，连接注入）"""

    def __init__(self, db: aiosqlite.Connection):
        self._db = db

    async def ensure_schema(self) -> None:
        """初始化表结构 + 填充默认值。在 get_db() 首次调用时执行。"""
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS agent_llm_config (
                agent_id TEXT PRIMARY KEY,
                llm_provider TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 迁移：添加 model 列（如果不存在）
        cursor = await self._db.execute("PRAGMA table_info(agent_llm_config)")
        columns = [row[1] for row in await cursor.fetchall()]
        if "model" not in columns:
            await self._db.execute("ALTER TABLE agent_llm_config ADD COLUMN model TEXT")

        # 表为空时填入默认配置
        cursor = await self._db.execute("SELECT COUNT(*) FROM agent_llm_config")
        row = await cursor.fetchone()
        if row[0] == 0:
            from .session import AGENT_CONFIGS
            for agent_id, config in AGENT_CONFIGS.items():
                provider = config.get("llm_provider", "bailian")
                await self._db.execute(
                    "INSERT INTO agent_llm_config (agent_id, llm_provider) VALUES (?, ?)",
                    (agent_id, provider),
                )

        await self._db.commit()

    async def get_provider(self, agent_id: str) -> Optional[str]:
        """获取指定 Agent 的 LLM Provider"""
        cursor = await self._db.execute(
            "SELECT llm_provider FROM agent_llm_config WHERE agent_id = ?",
            (agent_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else None

    async def get_model(self, agent_id: str) -> Optional[str]:
        """获取指定 Agent 的模型配置"""
        cursor = await self._db.execute(
            "SELECT model FROM agent_llm_config WHERE agent_id = ?",
            (agent_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else None

    async def update_model(self, agent_id: str, model: str) -> bool:
        """更新指定 Agent 的模型配置"""
        cursor = await self._db.execute(
            "UPDATE agent_llm_config SET model = ?, updated_at = CURRENT_TIMESTAMP WHERE agent_id = ?",
            (model, agent_id),
        )
        await self._db.commit()
        return cursor.rowcount > 0

    async def get_all_config(self) -> Dict[str, Dict[str, str]]:
        """获取所有 Agent 的 LLM 配置"""
        cursor = await self._db.execute("SELECT agent_id, llm_provider, model FROM agent_llm_config")
        result = {}
        for row in await cursor.fetchall():
            result[row[0]] = {"llm_provider": row[1], "model": row[2]}
        return result

    async def update_provider(self, agent_id: str, llm_provider: str) -> bool:
        """更新指定 Agent 的 LLM Provider"""
        cursor = await self._db.execute(
            "UPDATE agent_llm_config SET llm_provider = ?, updated_at = CURRENT_TIMESTAMP WHERE agent_id = ?",
            (llm_provider, agent_id),
        )
        await self._db.commit()
        return cursor.rowcount > 0
