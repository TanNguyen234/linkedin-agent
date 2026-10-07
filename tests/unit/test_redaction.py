"""Tests ensuring secrets are never logged or leaked."""

from linkedin_agent_suite.core.logging import sanitize_log_message


def test_credential_sanitization():
    raw = "Connecting with li_at=AQEDAA891238912 and Bearer secret_token_xyz"
    sanitized = sanitize_log_message(raw)
    assert "AQEDAA891238912" not in sanitized
    assert "secret_token_xyz" not in sanitized
    assert "[REDACTED]" in sanitized
