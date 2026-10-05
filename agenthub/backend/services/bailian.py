"""阿里云百炼服务（模拟实现） - 已移除真实 API 调用

原实现通过 OpenAI SDK 调用百炼端点（使用 DASHSCOPE_API_KEY），
现全部替换为本地模拟回复，不发起网络请求，不读取任何 API Key。
"""
from .mock_llm import MockLLMService


class BailianService(MockLLMService):
    """百炼服务模拟实现 - 接口与原真实服务一致"""

    DEFAULT_MODEL = "qwen3.7-max-preview"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        super().__init__(api_key=api_key, model=model, provider="bailian")


# 全局百炼服务实例（模拟）
bailian_service = BailianService()
