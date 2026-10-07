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

            # 4. Login Required
            if "/login" in url or "/checkpoint/lg/login-submit" in url:
                return SessionState.LOGIN_REQUIRED
            if await page.query_selector(
                '#username, #password, input[name="session_key"]'
            ):
                return SessionState.LOGIN_REQUIRED

            # 5. Authenticated Signals
            # Must have global nav or primary navigation AND avatar/profile button, without login fields
            has_nav = await page.query_selector(
                '#global-nav, nav[aria-label="Primary"], .global-nav'
            )
            has_me = await page.query_selector(
                '.global-nav__me, button[aria-label*="Me"], .nav-item--profile'
            )
            if has_nav or (has_me and "/feed" in url):
                return SessionState.AUTHENTICATED

            return SessionState.UNKNOWN
        finally:
            if should_close:
                await page.close()
