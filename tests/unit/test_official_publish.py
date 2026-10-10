"""Comprehensive unit and contract tests for official LinkedIn publisher and pipeline."""

import httpx
import pytest

from linkedin_agent_suite.core.config import Settings
from linkedin_agent_suite.core.errors import AuthenticationError, ConfigurationError
from linkedin_agent_suite.core.storage.database import LocalDatabase
from linkedin_agent_suite.intelligence.content.publishing.official import (
    OfficialLinkedInPublisher,
)
from linkedin_agent_suite.intelligence.content.service import ContentService


def test_missing_token_blocked():
    with pytest.raises(AuthenticationError):
        OfficialLinkedInPublisher(access_token="", enable_posting=True)


def test_disabled_posting_blocked():
    with pytest.raises(ConfigurationError):
        OfficialLinkedInPublisher(access_token="valid_token", enable_posting=False)


def test_invalid_author_urn_format():
    settings = Settings(
        ENABLE_OFFICIAL_POSTING=True,
        LINKEDIN_ACCESS_TOKEN="mock_token",
        LINKEDIN_AUTHOR_URN="invalid_urn_string",
    )
    publisher = OfficialLinkedInPublisher(settings=settings)
    res = publisher.publish_text_post("Hello world")
    assert res.status == "BLOCKED"
    assert res.error_code == "IDENTITY_UNRESOLVED"
    assert "Invalid author URN format" in (res.error_message or "")


def test_valid_author_urn_configured():
    settings = Settings(
        ENABLE_OFFICIAL_POSTING=True,
        LINKEDIN_ACCESS_TOKEN="mock_token",
        LINKEDIN_AUTHOR_URN="urn:li:person:1234567890abcdef",
    )
    publisher = OfficialLinkedInPublisher(settings=settings)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/posts":
            return httpx.Response(201, headers={"x-restli-id": "urn:li:share:998877"})
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res = publisher.publish_text_post("Testing valid URN", client=client)
    assert res.status == "PUBLISHED"
    assert res.post_urn == "urn:li:share:998877"
    assert res.is_confirmed is True


def test_author_resolution_via_v2_me():
    settings = Settings(
        ENABLE_OFFICIAL_POSTING=True,
        LINKEDIN_ACCESS_TOKEN="mock_token",
    )
    publisher = OfficialLinkedInPublisher(settings=settings)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v2/me":
            return httpx.Response(200, json={"id": "member_xyz123"})
        if request.url.path == "/rest/posts":
            return httpx.Response(201, headers={"x-restli-id": "urn:li:share:post_me_123"})
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res = publisher.publish_text_post("Resolving author", client=client)
    assert res.status == "PUBLISHED"
    assert res.post_urn == "urn:li:share:post_me_123"


def test_oidc_userinfo_pairwise_rejected():
    settings = Settings(
        ENABLE_OFFICIAL_POSTING=True,
        LINKEDIN_ACCESS_TOKEN="mock_token",
    )
    publisher = OfficialLinkedInPublisher(settings=settings)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v2/me":
            return httpx.Response(403, text="Scope not granted")
        if request.url.path == "/v2/userinfo":
            return httpx.Response(200, json={"sub": "pairwise_sub_string"})
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res = publisher.publish_text_post("Testing pairwise rejection", client=client)
    assert res.status == "BLOCKED"
    assert res.error_code == "IDENTITY_UNRESOLVED"
    assert "pairwise" in (res.error_message or "").lower()


def test_publish_missing_post_urn_returns_unconfirmed():
    settings = Settings(
        ENABLE_OFFICIAL_POSTING=True,
        LINKEDIN_ACCESS_TOKEN="mock_token",
        LINKEDIN_AUTHOR_URN="urn:li:person:1234567890abcdef",
    )
    publisher = OfficialLinkedInPublisher(settings=settings)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/posts":
            return httpx.Response(201, headers={})  # Missing x-restli-id
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res = publisher.publish_text_post("Testing missing URN", client=client)
    assert res.status == "UNCONFIRMED"
    assert res.error_code == "MISSING_POST_URN"
    assert res.is_confirmed is False


def test_publish_api_version_expired_426():
    settings = Settings(
        ENABLE_OFFICIAL_POSTING=True,
        LINKEDIN_ACCESS_TOKEN="mock_token",
        LINKEDIN_AUTHOR_URN="urn:li:person:1234567890abcdef",
        LINKEDIN_API_VERSION="202401",
    )
    publisher = OfficialLinkedInPublisher(settings=settings)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/posts":
            return httpx.Response(426, text="API version 202401 is deprecated and unsupported")
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res = publisher.publish_text_post("Testing 426", client=client)
    assert res.status == "FAILED"
    assert res.http_status == 426
    assert res.error_code == "API_VERSION_EXPIRED"


def test_publish_auth_failed_401():
    settings = Settings(
        ENABLE_OFFICIAL_POSTING=True,
        LINKEDIN_ACCESS_TOKEN="expired_token",
        LINKEDIN_AUTHOR_URN="urn:li:person:1234567890abcdef",
    )
    publisher = OfficialLinkedInPublisher(settings=settings)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/posts":
            return httpx.Response(401, text="Unauthorized: Token expired")
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res = publisher.publish_text_post("Testing 401", client=client)
    assert res.status == "FAILED"
    assert res.http_status == 401
    assert res.error_code == "AUTH_FAILED"


def test_publish_rate_limit_429():
    settings = Settings(
        ENABLE_OFFICIAL_POSTING=True,
        LINKEDIN_ACCESS_TOKEN="mock_token",
        LINKEDIN_AUTHOR_URN="urn:li:person:1234567890abcdef",
    )
    publisher = OfficialLinkedInPublisher(settings=settings)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/posts":
            return httpx.Response(429, text="Rate limit exceeded")
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res = publisher.publish_text_post("Testing 429", client=client)
    assert res.status == "FAILED"
    assert res.http_status == 429
    assert res.error_code == "RATE_LIMITED"


def test_publish_server_error_500():
    settings = Settings(
        ENABLE_OFFICIAL_POSTING=True,
        LINKEDIN_ACCESS_TOKEN="mock_token",
        LINKEDIN_AUTHOR_URN="urn:li:person:1234567890abcdef",
    )
    publisher = OfficialLinkedInPublisher(settings=settings)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/posts":
            return httpx.Response(500, text="Internal LinkedIn Error")
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res = publisher.publish_text_post("Testing 500", client=client)
    assert res.status == "FAILED"
    assert res.http_status == 500
    assert res.error_code == "SERVER_ERROR"


def test_publish_timeout_returns_unconfirmed():
    settings = Settings(
        ENABLE_OFFICIAL_POSTING=True,
        LINKEDIN_ACCESS_TOKEN="mock_token",
        LINKEDIN_AUTHOR_URN="urn:li:person:1234567890abcdef",
    )
    publisher = OfficialLinkedInPublisher(settings=settings)

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Timeout waiting for LinkedIn response")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    res = publisher.publish_text_post("Testing timeout", client=client)
    assert res.status == "UNCONFIRMED"
    assert res.error_code == "TIMEOUT"
    assert res.is_confirmed is False


def test_content_service_end_to_end_publish_flow(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    db = LocalDatabase(db_file)
    settings = Settings(
        ENABLE_OFFICIAL_POSTING=True,
        LINKEDIN_ACCESS_TOKEN="test_token",
        LINKEDIN_AUTHOR_URN="urn:li:person:1234567890abcdef",
    )
    service = ContentService(db=db, settings=settings)

    # 1. Generate draft
    draft = service.generate_draft("Autonomous AI in Production", ["Fact 1", "Fact 2"])
    assert draft.status == "DRAFT"

    # 2. Preview draft and get approval token
    preview = service.preview_draft(draft.id)
    assert preview["status"] == "READY_FOR_APPROVAL"
    token = preview["approval_token"]

    # 3. Publish draft with mock client
    def mock_publish(self, text, client=None, idempotency_key=None):
        from linkedin_agent_suite.core.models import PublishResult
        return PublishResult(
            status="PUBLISHED",
            post_urn="urn:li:share:published_12345",
            http_status=201,
            is_confirmed=True,
        )

    monkeypatch.setattr(OfficialLinkedInPublisher, "publish_text_post", mock_publish)

    pub_res = service.publish_draft(draft.id, token)
    assert pub_res["status"] == "PUBLISHED"
    assert pub_res["post_urn"] == "urn:li:share:published_12345"

    # Verify SQLite persistence
    persisted = db.get_post_draft(draft.id)
    assert persisted is not None
    assert persisted["status"] == "PUBLISHED"
    assert persisted["post_urn"] == "urn:li:share:published_12345"

    # 4. Duplicate publish attempt must be blocked
    token_dup = service.preview_draft(draft.id)["approval_token"]
    dup_res = service.publish_draft(draft.id, token_dup)
    assert dup_res["status"] == "BLOCKED"
    assert "already published" in dup_res["message"]
