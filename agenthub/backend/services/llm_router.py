"""LLM 适配器选择器 - 根据配置选择百炼或 MiniMax"""
import os
from typing import Optional, Union

# 全局服务实例缓存（按 provider:model 索引）
_llm_services: dict[str, Union["BailianService", "MiniMaxService"]] = {}


def get_llm_service_for_provider(provider: str, model: Optional[str] = None) -> Union["BailianService", "MiniMaxService"]:
    """根据 provider 名称返回对应服务实例（带缓存）

    Args:
        provider: "bailian" 或 "minimax"
        model: 可选的模型名称，None 时使用默认模型

    Returns:
        对应的 LLM 服务实例
    """
    cache_key = f"{provider}:{model or 'default'}"

    if cache_key in _llm_services:
        return _llm_services[cache_key]

    if provider == "minimax":
        from .minimax import MiniMaxService
        service = MiniMaxService(model=model)
    else:
        from .bailian import BailianService
        service = BailianService(model=model)

    _llm_services[cache_key] = service
    return service


def get_llm_service(model: Optional[str] = None) -> Union["BailianService", "MiniMaxService"]:
    """根据 LLM_PROVIDER 环境变量返回对应服务实例（兼容旧调用）"""
    provider = os.getenv("LLM_PROVIDER", "bailian")
    return get_llm_service_for_provider(provider, model=model)


def reset_llm_service():
    """重置所有 LLM 服务实例"""
    _llm_services.clear()