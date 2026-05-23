"""LLM 适配器选择器 - 根据配置选择百炼或 Anthropic"""
import os
from typing import Union

# 全局服务实例缓存
_llm_service: Union["BailianService", "ClaudeService", None] = None


def get_llm_service() -> Union["BailianService", "ClaudeService"]:
    """根据 LLM_PROVIDER 环境变量返回对应服务实例

    Returns:
        BailianService 或 ClaudeService 实例

    Note:
        LLM_PROVIDER=bailian（默认） -> BailianService
        LLM_PROVIDER=anthropic          -> ClaudeService
    """
    global _llm_service

    if _llm_service is not None:
        return _llm_service

    provider = os.getenv("LLM_PROVIDER", "bailian")

    if provider == "anthropic":
        from .claude import ClaudeService
        _llm_service = ClaudeService()
    else:
        from .bailian import BailianService
        _llm_service = BailianService()

    return _llm_service


def reset_llm_service():
    """重置 LLM 服务实例（用于测试或配置切换后重新加载）"""
    global _llm_service
    _llm_service = None