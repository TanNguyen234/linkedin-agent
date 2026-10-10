"""Unit tests for connection request gates and target validation."""

from linkedin_agent_suite.core.security import approvals
from linkedin_agent_suite.linkedin.connections.service import (
    validate_linkedin_profile_target,
)


def test_target_url_validation():
    # Valid vanity username
    assert (
        validate_linkedin_profile_target("alice-smith")
        == "https://www.linkedin.com/in/alice-smith/"
    )

    # Valid profile URL
    assert (
        validate_linkedin_profile_target("https://www.linkedin.com/in/alice-smith")
        == "https://www.linkedin.com/in/alice-smith/"
    )

    # Malicious external URLs rejected
    assert validate_linkedin_profile_target("http://evil.com/in/alice") is None
    assert validate_linkedin_profile_target("https://phishing.com/in/alice") is None
    assert validate_linkedin_profile_target("") is None


def test_connection_approval_lifecycle():
    payload = {
        "identifier": "https://www.linkedin.com/in/alice-smith/",
        "note": "Glad to connect",
    }
    token = approvals.request_approval("connect", payload)
    assert len(token) > 0
    ok, _msg = approvals.consume_approval(token, "connect", payload)
    assert ok is True

    # Replay rejected
    ok2, _err2 = approvals.consume_approval(token, "connect", payload)
    assert ok2 is False
