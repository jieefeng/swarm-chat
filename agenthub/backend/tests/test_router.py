"""MessageRouter 单元测试 (UT-R001 ~ UT-R010)"""
import pytest
import sys
import os

# 添加父目录到路径以导入router模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.router import MessageRouter


class TestMessageRouter:
    """MessageRouter测试类"""

    @pytest.fixture
    def router(self):
        """创建MessageRouter实例"""
        return MessageRouter()

    # UT-R001: 解析@pm指令 -> target="pm", content="你好"
    def test_parse_pm_directive(self, router):
        """UT-R001: 解析@pm指令，目标为pm，内容正确提取"""
        result = router.parse("@pm 你好")
        assert result["target"] == "pm"
        assert result["content"] == "你好"
        assert result["is_broadcast"] is False
        assert result["is_termination"] is False

    # UT-R002: 解析@architect指令 -> target="architect", content="请分析"
    def test_parse_architect_directive(self, router):
        """UT-R002: 解析@architect指令，目标为architect，内容正确提取"""
        result = router.parse("@architect 请分析")
        assert result["target"] == "architect"
        assert result["content"] == "请分析"
        assert result["is_broadcast"] is False
        assert result["is_termination"] is False

    # UT-R003: 解析无@广播消息 -> target=["pm","architect"], is_broadcast=True
    def test_parse_broadcast_message(self, router):
        """UT-R003: 无@前缀的消息视为广播，发送给所有Agent"""
        result = router.parse("这是一条广播消息")
        assert result["target"] == ["pm", "architect"]
        assert result["content"] == "这是一条广播消息"
        assert result["is_broadcast"] is True
        assert result["is_termination"] is False

    # UT-R004: 解析无效@指令 -> target=None, 原样返回
    def test_parse_invalid_directive(self, router):
        """UT-R004: 无效的@指令（如不存在的Agent）返回None，内容原样保留"""
        result = router.parse("@unknownagent 内容")
        assert result["target"] is None
        assert result["content"] == "@unknownagent 内容"
        assert result["is_broadcast"] is False

    # UT-R005: 解析纯@无内容 -> target=None
    def test_parse_empty_at_directive(self, router):
        """UT-R005: @后无内容（无空格）返回target=None"""
        result = router.parse("@pm")
        assert result["target"] is None
        assert result["content"] == "@pm"

    # UT-R006: 解析@后无空格 -> target=None
    def test_parse_no_space_after_at(self, router):
        """UT-R006: @后直接跟内容无空格，返回target=None"""
        result = router.parse("@pm你好")
        assert result["target"] is None
        assert result["content"] == "@pm你好"

    # UT-R007: 检测终止关键词"结束讨论" -> is_termination=True
    def test_termination_keyword_end_discussion(self, router):
        """UT-R007: 消息包含"结束讨论"时is_termination为True"""
        result = router.parse("让我们结束讨论吧")
        assert result["is_termination"] is True
        assert "结束讨论" in result["content"]

    # UT-R008: 检测终止关键词"确认方案" -> is_termination=True
    def test_termination_keyword_confirm(self, router):
        """UT-R008: 消息包含"确认方案"时is_termination为True"""
        result = router.parse("现在确认方案")
        assert result["is_termination"] is True
        assert "确认方案" in result["content"]

    # UT-R009: 无终止关键词 -> is_termination=False
    def test_no_termination_keyword(self, router):
        """UT-R009: 普通消息不包含终止关键词，is_termination为False"""
        result = router.parse("@pm 正常消息内容")
        assert result["is_termination"] is False
        assert result["target"] == "pm"

    # UT-R010: 多个终止关键词取第一个
    def test_multiple_termination_keywords_first_wins(self, router):
        """UT-R010: 消息包含多个终止关键词时，只识别第一个"""
        result = router.parse("@pm 结束讨论然后重新讨论")
        assert result["is_termination"] is True
        # 内容仍然完整保留
        assert "结束讨论" in result["content"]

    def test_route_method_returns_tuple(self, router):
        """测试route方法返回正确的元组"""
        target, content, is_broadcast, is_termination = router.route("@pm 你好")
        assert target == "pm"
        assert content == "你好"
        assert is_broadcast is False
        assert is_termination is False

    def test_last_parse_result_saved(self, router):
        """测试最后解析结果被保存"""
        router.parse("@architect 分析需求")
        assert router.last_parse_result is not None
        assert router.last_parse_result["target"] == "architect"