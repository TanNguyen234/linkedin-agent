"""Unit tests for messaging approval security gates."""

from linkedin_agent_suite.core.security import approvals


def test_approval_mismatch_and_consumption():
    payload = {"recipient": "test-user", "message": "Hello world"}
    token = approvals.request_approval("send_message", payload)

    # Action mismatch rejected
    ok, err = approvals.consume_approval(token, "connect", payload)
    assert ok is False
    assert "mismatch" in err.lower()

    # Payload mismatch rejected
    tampered_payload = {"recipient": "test-user", "message": "Hacked message"}
    ok, err = approvals.consume_approval(token, "send_message", tampered_payload)
    assert ok is False
    assert "mismatch" in err.lower()

    # Valid consumption succeeds
    ok, msg = approvals.consume_approval(token, "send_message", payload)
    assert ok is True

    # Replay rejected
    ok2, err2 = approvals.consume_approval(token, "send_message", payload)
    assert ok2 is False
