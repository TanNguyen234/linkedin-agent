"""Unit tests for HMAC two-phase approval gates."""
from src.core.security.approvals import request_approval, consume_approval

def test_approval_token_lifecycle():
    payload = {"action": "send_message", "recipient": "john_doe"}
    token = request_approval("send_message", payload)
    assert len(token) == 16
    
    # Valid consumption
    ok, msg = consume_approval(token, "send_message", payload)
    assert ok is True
    
    # Second consumption must fail (single-use)
    ok2, msg2 = consume_approval(token, "send_message", payload)
    assert ok2 is False
