"""Multi-signal session state manager for LinkedIn."""

from __future__ import annotations

import logging
from enum import Enum

from patchright.async_api import Page

from ..browser.manager import BrowserManager

logger = logging.getLogger(__name__)


class SessionState(str, Enum):
    AUTHENTICATED = "AUTHENTICATED"
    LOGIN_REQUIRED = "LOGIN_REQUIRED"
    AUTHWALL = "AUTHWALL"
    CHECKPOINT = "CHECKPOINT"
    ACCOUNT_RESTRICTED = "ACCOUNT_RESTRICTED"
    UNKNOWN = "UNKNOWN"


class SessionManager:
    def __init__(self, browser: BrowserManager):
        self.browser = browser

    async def detect_session_state(self, page: Page | None = None) -> SessionState:
        """Evaluate page signals to detect robust authenticated status."""
        should_close = False
        if page is None:
            context = await self.browser.get_context()
            page = await context.new_page()
            should_close = True
            try:
                await page.goto(
                    "https://www.linkedin.com/feed/",
                    timeout=20000,
                    wait_until="domcontentloaded",
                )
            except Exception as e:
                logger.warning(f"Failed to navigate during session detection: {e}")

        try:
            url = page.url.lower()

            # 1. Security Checkpoint / CAPTCHA
            if (
                "/checkpoint/challenge" in url
                or "security verification" in (await page.title()).lower()
            ):
                return SessionState.CHECKPOINT
            if await page.query_selector(
                'form[action*="challenge"], #captcha-internal'
            ):
                return SessionState.CHECKPOINT

            # 2. Account Restriction
            if "/checkpoint/lg/account-restricted" in url:
                return SessionState.ACCOUNT_RESTRICTED
            if await page.query_selector('text="Your account has been restricted"'):
                return SessionState.ACCOUNT_RESTRICTED

            # 3. Authwall / Intercept
            if "/authwall" in url or await page.query_selector(
                'input[name="authwall"], .authwall-join-form'
            ):
                return SessionState.AUTHWALL

            # 4. Check for active login form inputs
            has_login_fields = await page.query_selector(
                '#username, #password, input[name="session_key"]'
            )

            # 5. Check cookies for li_at token (gold standard LinkedIn session proof)
            has_li_at = False
            try:
                cookies = await page.context.cookies(["https://www.linkedin.com", "https://linkedin.com"])
                has_li_at = any(
                    c.get("name") == "li_at" and len(c.get("value", "")) > 10
                    for c in cookies
                )
            except Exception as e:
                logger.debug("Failed reading cookies: %s", e)

            # If li_at cookie exists and we are not on an active login error page, we are authenticated
            if has_li_at and not (("/login" in url or "/checkpoint/lg/login-submit" in url) and has_login_fields):
                return SessionState.AUTHENTICATED

            # 6. Authenticated DOM & URL Signals
            has_nav = await page.query_selector(
                '#global-nav, nav[aria-label*="Primary" i], nav[aria-label*="chính" i], .global-nav, header.global-nav'
            )
            has_me = await page.query_selector(
                '.global-nav__me, button[aria-label*="Me" i], button[aria-label*="Tôi" i], .nav-item--profile, img.global-nav__me-photo'
            )
            is_feed_or_home = any(
                p in url for p in ["/feed", "/in/", "/mynetwork", "/jobs", "/messaging", "/notifications"]
            )

            if has_nav or has_me or (is_feed_or_home and not has_login_fields):
                return SessionState.AUTHENTICATED

            # 7. Login Required
            if ("/login" in url or "/checkpoint/lg/login-submit" in url) or has_login_fields:
                return SessionState.LOGIN_REQUIRED

            return SessionState.UNKNOWN
        finally:
            if should_close:
                await page.close()
