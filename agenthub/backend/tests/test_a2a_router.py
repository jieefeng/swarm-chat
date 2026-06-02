"""A2ARouter 测试"""
import pytest
from agenthub.backend.services.a2a_router import A2ARouter


@pytest.fixture
def router():
    return A2ARouter()


def test_parse_mentions_simple(router):
    """测试简单 @mention 解析"""
    content = "@architect 这个方案可行吗？"
    cleaned, mentions = router.parse_mentions(content)
    assert cleaned == "这个方案可行吗？"
    assert mentions == ["architect"]


def test_parse_mentions_multiple(router):
    """测试多个 @mention 解析"""
    content = "@architect @pm 这个方案可行吗？"
    cleaned, mentions = router.parse_mentions(content)
    assert cleaned == "这个方案可行吗？"
    assert "architect" in mentions
    assert "pm" in mentions


def test_parse_mentions_no_mention(router):
    """测试无 @mention"""
    content = "这个方案可行吗？"
    cleaned, mentions = router.parse_mentions(content)
    assert mentions == []


def test_parse_mentions_unknown(router):
    """测试未知的 @mention"""
    content = "@unknown 这个方案可行吗？"
    cleaned, mentions = router.parse_mentions(content)
    assert mentions == []


def test_parse_mentions_email_not_matched(router):
    """测试邮箱地址中的 @ 不被误识别为 mention"""
    content = "请联系 user@example.com 或 @architect"
    cleaned, mentions = router.parse_mentions(content)
    assert mentions == ["architect"]
    assert "user@example.com" in cleaned


# --- Handoff 检测测试 ---

def test_detect_handoff_simple(router):
    """测试简单的 handoff 检测"""
    content = "方案已完成 [HANDOFF:developer]"
    result = router.detect_handoff(content)
    assert result == ("developer", None)


def test_detect_handoff_with_reason(router):
    """测试带原因的 handoff 检测"""
    content = "方案已完成 [HANDOFF:qa:请审查代码]"
    result = router.detect_handoff(content)
    assert result == ("qa", "请审查代码")


def test_detect_no_handoff(router):
    """测试无 handoff 标记"""
    content = "方案已完成"
    result = router.detect_handoff(content)
    assert result is None


def test_detect_invalid_agent(router):
    """测试无效的 agent ID"""
    content = "[HANDOFF:unknown_agent]"
    result = router.detect_handoff(content)
    assert result is None


def test_detect_handoff_in_middle(router):
    """测试 handoff 标记在中间位置"""
    content = "这是方案 [HANDOFF:developer] 请实现"
    result = router.detect_handoff(content)
    assert result == ("developer", None)
