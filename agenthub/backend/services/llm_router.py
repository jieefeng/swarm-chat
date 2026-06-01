"""LLM 适配器选择器 - 根据配置选择百炼或 Anthropic"""
import os
from typing import Union

# 全局服务实例缓存（按 provider 名称索引）
_llm_services: dict[str, Union["BailianService", "ClaudeService"]] = {}


def get_llm_service_for_provider(provider: str) -> Union["BailianService", "ClaudeService"]:
    """根据 provider 名称返回对应服务实例（带缓存）

    Args:
        provider: "bailian" 或 "anthropic"

    Returns:
        对应的 LLM 服务实例
    """
    if provider in _llm_services:
        return _llm_services[provider]

    if provider == "anthropic":
        from .claude import ClaudeService
        service = ClaudeService()
    else:
        from .bailian import BailianService
        service = BailianService()

    _llm_services[provider] = service
    return service


def get_llm_service() -> Union["BailianService", "ClaudeService"]:
    """根据 LLM_PROVIDER 环境变量返回对应服务实例（兼容旧调用）"""
    provider = os.getenv("LLM_PROVIDER", "bailian")
    return get_llm_service_for_provider(provider)


def reset_llm_service():
    """重置所有 LLM 服务实例"""
    _llm_services.clear()