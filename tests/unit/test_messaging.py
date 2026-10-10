"""Unit tests for messaging validation and approval security gates."""

from linkedin_agent_suite.core.security import approvals
from linkedin_agent_suite.linkedin.messaging.service import validate_linkedin_recipient


def test_recipient_url_validation():
    # Valid vanity username
    assert validate_linkedin_recipient("john-doe-123") == "https://www.linkedin.com/in/john-doe-123/"

    # Valid canonical LinkedIn profile URL
    assert validate_linkedin_recipient("https://www.linkedin.com/in/john-doe-123") == "https://www.linkedin.com/in/john-doe-123/"
    assert validate_linkedin_recipient("https://linkedin.com/in/john-doe-123/") == "https://www.linkedin.com/in/john-doe-123/"

    # Valid thread URL
    assert validate_linkedin_recipient("https://www.linkedin.com/messaging/thread/thread-998877") == "https://www.linkedin.com/messaging/thread/thread-998877/"

    # Untrusted / Malicious URLs must be rejected
    assert validate_linkedin_recipient("http://malicious-site.com/in/john") is None
    assert validate_linkedin_recipient("https://attacker.com/in/john") is None
    assert validate_linkedin_recipient("javascript:alert(1)") is None
    assert validate_linkedin_recipient("") is None


def test_approval_mismatch_and_consumption():
    payload = {"recipient": "https://www.linkedin.com/in/test-user/", "message": "Hello world"}
    token = approvals.request_approval("send_message", payload)

    # Action mismatch rejected
    ok, err = approvals.consume_approval(token, "connect", payload)
    assert ok is False
    assert "mismatch" in err.lower()

    # Payload mismatch rejected
    tampered_payload = {"recipient": "https://www.linkedin.com/in/test-user/", "message": "Hacked message"}
    ok, err = approvals.consume_approval(token, "send_message", tampered_payload)
    assert ok is False
    assert "mismatch" in err.lower()

    # Valid consumption succeeds
    ok, _msg = approvals.consume_approval(token, "send_message", payload)
    assert ok is True

    # Replay rejected
    ok2, _err2 = approvals.consume_approval(token, "send_message", payload)
    assert ok2 is False
