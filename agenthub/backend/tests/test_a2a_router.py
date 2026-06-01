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
