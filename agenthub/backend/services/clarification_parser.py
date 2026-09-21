"""Clarification 解析器 - 从 LLM 文本输出中提取澄清请求

LLM 模拟调用工具时会在回复文本中输出结构化澄清段。
支持两种格式：

1. fenced code block 标记:
   ```clarification
   {"question": "...", "options": ["...", "..."]}
   ```

2. 行内标记:
   [CLARIFICATION]
   {"question": "...", "options": [...]}
   [/CLARIFICATION]

解析成功返回 ClarificationResult；不含澄清段时返回 None。
"""
import json
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

# ```clarification ... ``` 代码块
_FENCED_RE = re.compile(
    r"```clarification\s*\n(.*?)```", re.DOTALL | re.IGNORECASE
)
# [CLARIFICATION] ... [/CLARIFICATION] 行内标记
_TAGGED_RE = re.compile(
    r"\[CLARIFICATION\]\s*(.*?)\s*\[/CLARIFICATION\]", re.DOTALL | re.IGNORECASE
)


@dataclass
class ClarificationResult:
    """解析结果。cleaned_text 为移除澄清段后的正文。"""

    question: str
    options: List[str] = field(default_factory=list)
    cleaned_text: str = ""


def _parse_payload(raw: str) -> Optional[ClarificationResult]:
    """解析 JSON payload 为 ClarificationResult（不设置 cleaned_text）。"""
    try:
        data = json.loads(raw.strip())
    except json.JSONDecodeError:
        logger.warning("Clarification payload is not valid JSON: %.80s", raw)
        return None

    if not isinstance(data, dict):
        return None

    question = data.get("question")
    if not isinstance(question, str) or not question.strip():
        return None

    options = data.get("options", [])
    if not isinstance(options, list):
        options = []
    options = [str(o) for o in options if o]

    return ClarificationResult(question=question.strip(), options=options)


def parse_clarification_from_response(text: str) -> Optional[ClarificationResult]:
    """从 LLM 完整回复中提取澄清请求。

    Args:
        text: LLM 的完整回复文本。

    Returns:
        ClarificationResult（含 question/options/cleaned_text），
        未找到有效澄清段时返回 None。
    """
    if not text:
        return None

    for pattern in (_FENCED_RE, _TAGGED_RE):
        match = pattern.search(text)
        if match:
            result = _parse_payload(match.group(1))
            if result:
                result.cleaned_text = text[: match.start()] + text[match.end():]
                # 去掉澄清段后正文可能残留多余空行
                result.cleaned_text = result.cleaned_text.strip()
                return result
            # 找到标记但解析失败：继续尝试下一种格式
    return None
