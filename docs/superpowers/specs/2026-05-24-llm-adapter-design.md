# LLM 适配层设计 - 百炼/Anthropic 可切换

**日期：** 2026-05-24
**版本：** v1.0

---

## 1. 背景

当前 AgentHub MVP 使用 Anthropic Claude API，需要扩展为同时支持阿里云百炼平台。百炼兼容 OpenAI 接口规范，通过配置切换即可。

## 2. 设计目标

- 新增 `bailian.py` 百炼适配器，与 `claude.py` 接口一致
- 新增 `llm_router.py` 根据环境变量选择适配器
- 默认使用百炼，可通过环境变量切换到 Anthropic
- SessionManager 等已有代码**无需改动**

## 3. 技术方案

### 3.1 百炼 API 规格

| 配置项 | 值 |
|--------|-----|
| base_url | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| model | `qwen3.6-plus-2026-04-02` |
| API Key | `DASHSCOPE_API_KEY` |
| SDK | OpenAI Python SDK（与 Anthropic 相同） |

### 3.2 文件结构

```
agenthub/backend/services/
├── claude.py       # Anthropic 适配器（保留）
├── bailian.py      # 百炼适配器（新增）
└── llm_router.py   # LLM 选择器（新增）
```

### 3.3 bailian.py

```python
class BailianService:
    """百炼 API 服务封装"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = "qwen3.6-plus-2026-04-02"
        self.default_timeout = 60

    async def send_message_with_retry(
        self,
        session_id: str,
        message: str,
        system_prompt: str = "",
        max_retries: int = 3,
        timeout: Optional[int] = None
    ) -> str:
        """异步发送消息，带重试"""

    def send_message(
        self,
        session_id: str,
        message: str,
        system_prompt: str = ""
    ) -> str:
        """同步发送消息"""
```

### 3.4 llm_router.py

```python
def get_llm_service() -> object:
    """根据 LLM_PROVIDER 环境变量返回对应服务"""
    provider = os.getenv("LLM_PROVIDER", "bailian")
    if provider == "anthropic":
        from .claude import ClaudeService
        return ClaudeService()
    from .bailian import BailianService
    return BailianService()
```

### 3.5 配置

| 环境变量 | 值 | 说明 |
|----------|-----|------|
| `LLM_PROVIDER` | `bailian`（默认） | 切换 LLM 提供商 |
| `DASHSCOPE_API_KEY` | - | 百炼 API Key |

切换到 Anthropic：
```bash
LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-xxx
```

## 4. 实现步骤

1. 创建 `bailian.py` - 百炼适配器
2. 创建 `llm_router.py` - LLM 选择器
3. 修改 `session.py` - 改用 `get_llm_service()`
4. 配置文件添加 `.env.example` 说明

## 5. 依赖

```txt
# requirements.txt
openai>=1.0.0
anthropic>=0.25.0
```

---

**Author:** Claude Code
**Last Updated:** 2026-05-24