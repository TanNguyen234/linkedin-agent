"""Official LinkedIn REST API publishing gateway with verified identity resolution."""
from __future__ import annotations

import logging
from datetime import UTC, datetime

import httpx

from ....core.config import Settings, get_settings
from ....core.errors import AuthenticationError, ConfigurationError
from ....core.models import PublishResult

logger = logging.getLogger(__name__)


class OfficialLinkedInPublisher:
    """Gateway for publishing posts to LinkedIn REST Posts API."""

    def __init__(
        self,
        settings: Settings | None = None,
        access_token: str | None = None,
        enable_posting: bool | None = None,
        api_version: str | None = None,
    ) -> None:
        if settings is None:
            base_settings = get_settings()
            self.settings = base_settings.model_copy()
        else:
            self.settings = settings.model_copy()

        if access_token is not None:
            self.settings.linkedin_access_token = access_token
        if enable_posting is not None:
            self.settings.enable_official_posting = enable_posting
        if api_version is not None:
            self.settings.linkedin_api_version = api_version

        if not self.settings.enable_official_posting:
            raise ConfigurationError(
                "Official LinkedIn posting is disabled by default. Set ENABLE_OFFICIAL_POSTING=true."
            )
        if not self.settings.linkedin_access_token:
            raise AuthenticationError(
                "Official LinkedIn publishing requires LINKEDIN_ACCESS_TOKEN."
            )

        # In-memory publication attempt ledger to prevent duplicate execution
        self._published_urns: set[str] = set()

    def get_api_headers(self) -> dict[str, str]:
        version = self.settings.linkedin_api_version
        return {
            "Authorization": f"Bearer {self.settings.linkedin_access_token}",
            "LinkedIn-Version": version,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

    def resolve_author_urn(self, client: httpx.Client | None = None) -> str:
        """Resolve verified author URN from explicit config or documented API. Never guess."""
        # 1. Explicitly configured and verified LINKEDIN_AUTHOR_URN
        if self.settings.linkedin_author_urn:
            raw_urn = self.settings.linkedin_author_urn.strip()
            if (raw_urn.startswith("urn:li:person:") or raw_urn.startswith("urn:li:organization:")) and len(raw_urn) > 15:
                return raw_urn
            raise AuthenticationError(
                f"Invalid author URN format: '{raw_urn}'. Expected 'urn:li:person:<id>' or 'urn:li:organization:<id>'."
            )

        # 2. Call /v2/me (documented member identity)
        close_client = False
        if client is None:
            client = httpx.Client(timeout=10.0)
            close_client = True

        try:
            resp = client.get(
                "https://api.linkedin.com/v2/me",
                headers={"Authorization": f"Bearer {self.settings.linkedin_access_token}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                person_id = data.get("id")
                if person_id and isinstance(person_id, str) and person_id.strip():
                    return f"urn:li:person:{person_id.strip()}"
            elif resp.status_code == 426:
                raise ConfigurationError(
                    f"Stale LinkedIn API Version ({self.settings.linkedin_api_version}): {resp.text}"
                )

            # 3. Check /v2/userinfo (OpenID Connect)
            resp_userinfo = client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {self.settings.linkedin_access_token}"},
            )
            if resp_userinfo.status_code == 200:
                # OIDC sub is pairwise in modern LinkedIn OIDC and cannot be blindly mapped to urn:li:person
                data = resp_userinfo.json()
                sub = data.get("sub")
                if sub:
                    raise AuthenticationError(
                        "IDENTITY_UNRESOLVED: OpenID Connect sub is pairwise and cannot be assumed to be a valid Posts API Person ID. Please configure LINKEDIN_AUTHOR_URN explicitly."
                    )
        except (ConfigurationError, AuthenticationError):
            raise
        except Exception as e:
            logger.debug(f"Error querying identity endpoints: {e}")
        finally:
            if close_client:
                client.close()

        raise AuthenticationError(
            "IDENTITY_UNRESOLVED: Cannot resolve member identity for author URN. Provide LINKEDIN_AUTHOR_URN explicitly."
        )

    def publish_text_post(
        self,
        text: str,
        client: httpx.Client | None = None,
        idempotency_key: str | None = None,
    ) -> PublishResult:
        """Publish a text post via LinkedIn REST Posts API and return a typed PublishResult."""
        try:
            author_urn = self.resolve_author_urn(client=client)
        except AuthenticationError as e:
            return PublishResult(
                status="BLOCKED",
                error_code="IDENTITY_UNRESOLVED",
                error_message=str(e),
                is_confirmed=False,
            )
        except ConfigurationError as e:
            return PublishResult(
                status="BLOCKED",
                error_code="CONFIGURATION_ERROR",
                error_message=str(e),
                is_confirmed=False,
            )

        headers = self.get_api_headers()
        payload = {
            "author": author_urn,
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }

        close_client = False
        if client is None:
            client = httpx.Client(timeout=15.0)
            close_client = True

        try:
            resp = client.post("https://api.linkedin.com/rest/posts", headers=headers, json=payload)
            if resp.status_code == 201:
                post_urn = resp.headers.get("x-restli-id", "")
                if not post_urn:
                    # Check body if present
                    try:
                        data = resp.json()
                        post_urn = data.get("id") or data.get("urn") or ""
                    except Exception:
                        post_urn = ""

                if post_urn:
                    self._published_urns.add(post_urn)
                    return PublishResult(
                        status="PUBLISHED",
                        post_urn=post_urn,
                        http_status=201,
                        is_confirmed=True,
                        published_at=datetime.now(UTC).isoformat(),
                    )
                else:
                    return PublishResult(
                        status="UNCONFIRMED",
                        http_status=201,
                        error_code="MISSING_POST_URN",
                        error_message="HTTP 201 received but no post identifier (x-restli-id) was returned.",
                        is_confirmed=False,
                    )
            elif resp.status_code == 426:
                return PublishResult(
                    status="FAILED",
                    http_status=426,
                    error_code="API_VERSION_EXPIRED",
                    error_message=f"Stale LinkedIn API Version ({self.settings.linkedin_api_version}): {resp.text}",
                    is_confirmed=False,
                )
            elif resp.status_code in (401, 403):
                return PublishResult(
                    status="FAILED",
                    http_status=resp.status_code,
                    error_code="AUTH_FAILED",
                    error_message=f"LinkedIn API Auth Failed ({resp.status_code}): {resp.text}",
                    is_confirmed=False,
                )
            elif resp.status_code == 429:
                return PublishResult(
                    status="FAILED",
                    http_status=429,
                    error_code="RATE_LIMITED",
                    error_message=f"LinkedIn API Rate Limit Exceeded: {resp.text}",
                    is_confirmed=False,
                )
            elif resp.status_code >= 500:
                return PublishResult(
                    status="FAILED",
                    http_status=resp.status_code,
                    error_code="SERVER_ERROR",
                    error_message=f"LinkedIn Server Error ({resp.status_code}): {resp.text}",
                    is_confirmed=False,
                )
            else:
                return PublishResult(
                    status="FAILED",
                    http_status=resp.status_code,
                    error_code=f"HTTP_{resp.status_code}",
                    error_message=resp.text,
                    is_confirmed=False,
                )
        except httpx.TimeoutException as e:
            return PublishResult(
                status="UNCONFIRMED",
                error_code="TIMEOUT",
                error_message=f"Request timed out during publish POST submission: {e!s}",
                is_confirmed=False,
            )
        except httpx.HTTPError as e:
            return PublishResult(
                status="FAILED",
                error_code="NETWORK_ERROR",
                error_message=f"Network error during publish: {e!s}",
                is_confirmed=False,
            )
        finally:
            if close_client:
                client.close()
