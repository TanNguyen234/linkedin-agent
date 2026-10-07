"""Official LinkedIn REST API publishing gateway with verified identity resolution."""
from __future__ import annotations

from typing import Any

import httpx

from ....core.config import Settings
from ....core.errors import AuthenticationError, ConfigurationError


class OfficialLinkedInPublisher:
    def __init__(self, settings: Settings | None = None, access_token: str | None = None, enable_posting: bool = False, api_version: str = "202401"):
        if settings is None:
            s = Settings()
            if access_token:
                s.linkedin_access_token = access_token
            s.linkedin_api_version = api_version
            self.settings = s
        else:
            self.settings = settings
        if not enable_posting:
            raise ConfigurationError("Official LinkedIn posting is disabled by default.")
        if not self.settings.linkedin_access_token:
            raise AuthenticationError("Official LinkedIn publishing requires LINKEDIN_ACCESS_TOKEN.")

    def get_api_headers(self) -> dict[str, str]:
        version = self.settings.linkedin_api_version
        return {
            "Authorization": f"Bearer {self.settings.linkedin_access_token}",
            "LinkedIn-Version": version,
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

    def resolve_author_urn(self) -> str:
        """Resolve verified author URN from API or explicit config. Never guess."""
        if self.settings.linkedin_author_urn:
            return self.settings.linkedin_author_urn

        # Call /v2/userinfo (OpenID Connect)
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get("https://api.linkedin.com/v2/userinfo", headers={
                    "Authorization": f"Bearer {self.settings.linkedin_access_token}"
                })
                if resp.status_code == 200:
                    data = resp.json()
                    sub = data.get("sub")
                    if sub and isinstance(sub, str) and sub.strip():
                        return f"urn:li:person:{sub.strip()}"
        except Exception:
            pass

        # Fallback to /v2/me (legacy member API)
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get("https://api.linkedin.com/v2/me", headers={
                    "Authorization": f"Bearer {self.settings.linkedin_access_token}"
                })
                if resp.status_code == 200:
                    data = resp.json()
                    person_id = data.get("id")
                    if person_id and isinstance(person_id, str) and person_id.strip():
                        return f"urn:li:person:{person_id.strip()}"
        except Exception:
            pass

        raise AuthenticationError(
            "Cannot resolve member identity for author URN. Grant 'openid profile' or provide LINKEDIN_AUTHOR_URN explicitly."
        )

    def publish_text_post(self, text: str) -> dict[str, Any]:
        """Publish a text post via LinkedIn REST Posts API."""
        author_urn = self.resolve_author_urn()
        headers = self.get_api_headers()

        payload = {
            "author": author_urn,
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": []
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post("https://api.linkedin.com/rest/posts", headers=headers, json=payload)
                if resp.status_code == 201:
                    post_urn = resp.headers.get("x-restli-id", "")
                    return {"status": "PUBLISHED", "post_urn": post_urn}
                elif resp.status_code in (401, 403):
                    raise AuthenticationError(f"LinkedIn API Auth Failed ({resp.status_code}): {resp.text}")
                elif resp.status_code == 426:
                    raise ConfigurationError(f"Stale LinkedIn API Version ({self.settings.linkedin_api_version}): {resp.text}")
                else:
                    return {"status": "FAILED", "code": resp.status_code, "error": resp.text}
        except httpx.HTTPError as e:
            return {"status": "FAILED", "error": str(e)}
