"""Unit tests for official publisher safety gates."""
import pytest
from linkedin_agent_suite.intelligence.content.publishing.official import OfficialLinkedInPublisher
from linkedin_agent_suite.core.errors import AuthenticationError, ConfigurationError

def test_missing_token_blocked():
    with pytest.raises(AuthenticationError):
        OfficialLinkedInPublisher(access_token="", enable_posting=True)

def test_disabled_posting_blocked():
    with pytest.raises(ConfigurationError):
        OfficialLinkedInPublisher(access_token="valid_token", enable_posting=False)
