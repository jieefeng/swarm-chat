"""InvocationRegistry 单元测试（验证已存在实现）"""
import time
import pytest
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
)

from agenthub.backend.services.invocation_registry import InvocationRegistry


class TestInvocationRegistry:
    @pytest.fixture
    def registry(self):
        return InvocationRegistry(ttl=10)

    def test_create_returns_uuid_pair(self, registry):
        inv_id, token = registry.create("designer", "thread-1")
        assert isinstance(inv_id, str) and len(inv_id) == 36
        assert isinstance(token, str) and len(token) == 36
        assert inv_id != token

    def test_create_stores_metadata(self, registry):
        inv_id, _ = registry.create("developer", "thread-2")
        inv = registry.get_invocation(inv_id)
        assert inv is not None
        assert inv["agent_id"] == "developer"
        assert inv["thread_id"] == "thread-2"
        assert inv["ttl"] == 10

    def test_verify_with_correct_credentials(self, registry):
        inv_id, token = registry.create("qa", "thread-3")
        inv = registry.verify(inv_id, token)
        assert inv is not None
        assert inv["agent_id"] == "qa"

    def test_verify_with_wrong_token(self, registry):
        inv_id, _ = registry.create("designer", "thread-4")
        assert registry.verify(inv_id, "wrong-token") is None

    def test_verify_unknown_invocation(self, registry):
        assert registry.verify("nonexistent-id", "any-token") is None

    def test_verify_expired_invocation_returns_none_and_removes(self, registry):
        inv_id, token = registry.create("designer", "thread-5")
        registry._invocations[inv_id]["created_at"] = time.time() - 11
        assert registry.verify(inv_id, token) is None
        assert registry.get_invocation(inv_id) is None

    def test_revoke_removes_invocation(self, registry):
        inv_id, _ = registry.create("developer", "thread-6")
        assert registry.revoke(inv_id) is True
        assert registry.get_invocation(inv_id) is None

    def test_revoke_unknown_returns_false(self, registry):
        assert registry.revoke("nonexistent") is False

    def test_cleanup_expired_removes_only_expired(self, registry):
        inv_id_old, _ = registry.create("designer", "thread-7")
        inv_id_new, _ = registry.create("developer", "thread-8")
        registry._invocations[inv_id_old]["created_at"] = time.time() - 100
        registry.cleanup_expired()
        assert registry.get_invocation(inv_id_old) is None
        assert registry.get_invocation(inv_id_new) is not None

    def test_count_tracks_active_invocations(self, registry):
        assert registry.count() == 0
        registry.create("designer", "thread-9")
        registry.create("developer", "thread-10")
        assert registry.count() == 2

    def test_get_all_invocations_returns_copy(self, registry):
        registry.create("designer", "thread-11")
        snapshot = registry.get_all_invocations()
        assert len(snapshot) == 1
        snapshot.clear()
        assert registry.count() == 1
