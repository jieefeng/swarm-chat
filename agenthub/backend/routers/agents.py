"""Agent 配置 API 路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

router = APIRouter(prefix="/api/agents", tags=["agents"])


class LLMProviderUpdate(BaseModel):
    """LLM Provider 更新请求"""
    llm_provider: str

    @field_validator("llm_provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        if v not in ("bailian", "anthropic"):
            raise ValueError("llm_provider must be 'bailian' or 'anthropic'")
        return v


@router.get("/llm-config")
async def get_all_llm_config():
    """获取所有 Agent 的 LLM 配置"""
    from agenthub.backend.services.llm_config_db import LLMConfigDB
    db = LLMConfigDB()
    return db.get_all_config()


@router.put("/{agent_id}/llm-config")
async def update_llm_config(agent_id: str, body: LLMProviderUpdate):
    """更新指定 Agent 的 LLM 配置"""
    from agenthub.backend.services.llm_config_db import LLMConfigDB
    from agenthub.backend.services.session import AGENT_CONFIGS

    if agent_id not in AGENT_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    db = LLMConfigDB()
    db.update_provider(agent_id, body.llm_provider)

    return {"agent_id": agent_id, "llm_provider": body.llm_provider}
