"""Unit tests for cryptographically bound HMAC approvals."""

from linkedin_agent_suite.core.security import approvals


def test_approval_token_lifecycle():
    payload = {"action": "send_message", "recipient": "john_doe"}
    token = approvals.request_approval("send_message", payload)
    assert len(token) == 24

    # Valid consumption
    ok, msg = approvals.consume_approval(token, "send_message", payload)
    assert ok is True

    # Replay consumption fails
    ok2, msg2 = approvals.consume_approval(token, "send_message", payload)
    assert ok2 is False


def test_approval_tamper_detection():
    payload1 = {"action": "send_message", "recipient": "john_doe"}
    payload2 = {"action": "send_message", "recipient": "jane_doe"}
    token = approvals.request_approval("send_message", payload1)

    # Attempting to use token for modified payload must fail
    ok, msg = approvals.consume_approval(token, "send_message", payload2)
    assert ok is False
    assert "mismatch" in msg
