"""Strict official LinkedIn REST API client with zero mock fallbacks."""
import httpx
from typing import Tuple
from ....core.errors import AuthenticationError, ConfigurationError

class OfficialLinkedInPublisher:
    def __init__(self, access_token: str, enable_posting: bool, api_version: str = "202506"):
        if not access_token:
            raise AuthenticationError("Missing LINKEDIN_ACCESS_TOKEN. Cannot publish via official API.")
        if not enable_posting:
            raise ConfigurationError("ENABLE_OFFICIAL_POSTING is False. Set to True to permit publishing.")
            
        self.access_token = access_token
        self.enable_posting = enable_posting
        self.api_version = api_version
        self.base_url = "https://api.linkedin.com"

    def publish_text_post(self, text: str, visibility: str = "PUBLIC") -> Tuple[bool, str]:
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": self.api_version
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                user_res = client.get(f"{self.base_url}/v2/userinfo", headers=headers)
                if user_res.status_code != 200:
                    return False, f"Userinfo failed ({user_res.status_code}): {user_res.text}"
                sub = user_res.json().get("sub")
                if not sub:
                    return False, "Failed to resolve member ID from userinfo"

                payload = {
                    "author": f"urn:li:person:{sub}",
                    "commentary": text,
                    "visibility": visibility,
                    "distribution": {
                        "feedDistribution": "MAIN_FEED",
                        "targetEntities": [],
                        "thirdPartyDistributionChannels": []
                    },
                    "lifecycleState": "PUBLISHED",
                    "isReshareDisabledByAuthor": False
                }
                post_res = client.post(f"{self.base_url}/rest/posts", headers=headers, json=payload)
                if post_res.status_code in (200, 201):
                    urn = post_res.headers.get("x-restli-id", "unknown-urn")
                    return True, urn
                return False, f"Post creation failed ({post_res.status_code}): {post_res.text}"
        except Exception as e:
            return False, f"Network/HTTP exception: {e}"
