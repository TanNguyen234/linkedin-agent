"""LinkedIn live session validation, checkpoint and restriction detection."""
from __future__ import annotations

import logging
from typing import Dict, Any
from patchright.async_api import Page
from ...core.errors import CheckpointChallengeError, AccountRestrictedError
from ..browser.manager import BrowserManager

logger = logging.getLogger(__name__)

AUTH_BLOCKER_PATTERNS = ["/login", "/authwall", "/uas/login"]
CHECKPOINT_PATTERNS = ["/checkpoint", "/challenge", "/consumer-email-challenge"]
RESTRICTION_PATTERNS = ["login-restriction", "account-restricted"]

class SessionManager:
    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager

    async def validate_session(self, page: Page | None = None) -> Dict[str, Any]:
        """Navigate to LinkedIn and verify real authenticated session status."""
        should_close = False
        if page is None:
            page = await self.browser_manager.get_page()
            should_close = True

        try:
            logger.info("Checking LinkedIn session by loading feed...")
            await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=15000)
            current_url = page.url

            # 1. Check for account restriction
            if any(p in current_url for p in RESTRICTION_PATTERNS):
                raise AccountRestrictedError(f"LinkedIn account is restricted: {current_url}")

            # 2. Check for security checkpoint / CAPTCHA
            if any(p in current_url for p in CHECKPOINT_PATTERNS):
                raise CheckpointChallengeError(f"LinkedIn checkpoint/verification challenge presented: {current_url}")

            # 3. Check for login wall
            if any(p in current_url for p in AUTH_BLOCKER_PATTERNS):
                return {
                    "authenticated": False,
                    "url": current_url,
                    "status": "LOGIN_REQUIRED",
                    "details": "Redirected to login/authwall"
                }

            # 4. Check for primary nav elements
            nav_count = await page.locator('nav a[href*="/feed"], nav button:has-text("Home"), .global-nav').count()
            if nav_count > 0 or "/feed" in current_url:
                return {
                    "authenticated": True,
                    "url": current_url,
                    "status": "ACTIVE_AUTHENTICATED",
                    "details": "Authenticated navigation elements found"
                }

            return {
                "authenticated": False,
                "url": current_url,
                "status": "UNKNOWN_STATE",
                "details": "Page loaded without authenticated markers"
            }
        finally:
            if should_close:
                await self.browser_manager.close()
