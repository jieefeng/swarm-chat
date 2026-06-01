"""LLM 配置数据库模块 - 管理 Agent 的 LLM Provider 配置"""
import sqlite3
from typing import Dict, Optional


class LLMConfigDB:
    """LLM 配置数据库封装"""

    def __init__(self, db_path: str = "agenthub.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """初始化数据库：创建表 + 填充默认值"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_llm_config (
                    agent_id TEXT PRIMARY KEY,
                    llm_provider TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 表为空时填入默认配置
            cursor = conn.execute("SELECT COUNT(*) FROM agent_llm_config")
            if cursor.fetchone()[0] == 0:
                from .session import AGENT_CONFIGS
                for agent_id, config in AGENT_CONFIGS.items():
                    provider = config.get("llm_provider", "bailian")
                    conn.execute(
                        "INSERT INTO agent_llm_config (agent_id, llm_provider) VALUES (?, ?)",
                        (agent_id, provider)
                    )

            conn.commit()
        finally:
            conn.close()

    def get_provider(self, agent_id: str) -> Optional[str]:
        """获取指定 Agent 的 LLM Provider"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "SELECT llm_provider FROM agent_llm_config WHERE agent_id = ?",
                (agent_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def get_all_config(self) -> Dict[str, Dict[str, str]]:
        """获取所有 Agent 的 LLM 配置"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("SELECT agent_id, llm_provider FROM agent_llm_config")
            result = {}
            for row in cursor.fetchall():
                result[row[0]] = {"llm_provider": row[1]}
            return result
        finally:
            conn.close()

    def update_provider(self, agent_id: str, llm_provider: str) -> bool:
        """更新指定 Agent 的 LLM Provider"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute(
                "UPDATE agent_llm_config SET llm_provider = ?, updated_at = CURRENT_TIMESTAMP WHERE agent_id = ?",
                (llm_provider, agent_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
