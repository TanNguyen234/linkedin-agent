"""Unit tests for connection request gates."""

from linkedin_agent_suite.core.security import approvals


def test_connection_approval_lifecycle():
    payload = {"identifier": "alice-smith", "note": "Glad to connect"}
    token = approvals.request_approval("connect", payload)
    assert len(token) > 0
    ok, msg = approvals.consume_approval(token, "connect", payload)
    assert ok is True
