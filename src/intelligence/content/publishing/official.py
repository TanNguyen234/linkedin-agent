"""Official LinkedIn REST API v2 publisher."""
import os
import httpx
from typing import Dict, Any, Tuple
from src.core.errors.exceptions import AuthenticationError

class OfficialLinkedInPublisher:
    def __init__(self, access_token: str):
        if not access_token:
            raise AuthenticationError("Missing LINKEDIN_ACCESS_TOKEN for official publisher.")
        self.access_token = access_token
        self.base_url = "https://api.linkedin.com"

    def publish_text_post(self, text: str, visibility: str = "PUBLIC") -> Tuple[bool, str]:
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": "202506"
        }
        # In live mode calls /v2/userinfo then /rest/posts
        # For mock/offline returns simulated URN
        if self.access_token.startswith("mock_"):
            return True, "urn:li:share:mock-official-12345"
            
        try:
            with httpx.Client(timeout=10.0) as client:
                user_res = client.get(f"{self.base_url}/v2/userinfo", headers=headers)
                if user_res.status_code != 200:
                    return False, f"Userinfo failed: {user_res.status_code}"
                sub = user_res.json().get("sub")
                
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
                return False, f"Post failed: {post_res.status_code} {post_res.text}"
        except Exception as e:
            return False, str(e)
