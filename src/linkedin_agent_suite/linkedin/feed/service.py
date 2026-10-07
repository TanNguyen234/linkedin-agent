"""Real LinkedIn feed and post search service."""

from __future__ import annotations

import logging
import urllib.parse
from typing import Any

from ..browser.manager import BrowserManager
from ..session.manager import SessionManager, SessionState

logger = logging.getLogger(__name__)


class FeedService:
    def __init__(self, browser: BrowserManager):
        self.browser = browser
        self.session = SessionManager(browser)

    async def get_feed(self, limit: int = 10) -> list[dict[str, Any]]:
        """Read and extract real LinkedIn feed items."""
        context = await self.browser.get_context()
        page = await context.new_page()
        try:
            await page.goto(
                "https://www.linkedin.com/feed/",
                wait_until="domcontentloaded",
                timeout=25000,
            )
            state = await self.session.detect_session_state(page)
            if state != SessionState.AUTHENTICATED:
                logger.warning(f"Session not authenticated for feed: {state}")
                return []

            try:
                await page.wait_for_selector(
                    ".feed-shared-update-v2, .feed-shared-update-v2__description",
                    timeout=12000,
                )
            except Exception:
                return []

            updates = await page.query_selector_all(".feed-shared-update-v2")
            feed_items: list[dict[str, Any]] = []

            for upd in updates[:limit]:
                actor_el = await upd.query_selector(
                    ".update-components-actor__name, .feed-shared-actor__name"
                )
                author = (
                    (await actor_el.inner_text()).strip()
                    if actor_el
                    else "LinkedIn Member"
                )

                desc_el = await upd.query_selector(
                    ".update-components-text, .feed-shared-update-v2__description"
                )
                text = (await desc_el.inner_text()).strip() if desc_el else ""

                link_el = await upd.query_selector(
                    "a[href*='urn:li:activity'], a.app-aware-link[href*='/feed/update/']"
                )
                href = await link_el.get_attribute("href") if link_el else ""

                time_el = await upd.query_selector(
                    ".update-components-actor__sub-description, time"
                )
                posted = (await time_el.inner_text()).strip() if time_el else ""

                if text:
                    feed_items.append(
                        {
                            "author": author,
                            "text": text,
                            "url": href,
                            "timestamp": posted,
                        }
                    )
            return feed_items
        finally:
            await page.close()

    async def search_posts(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search posts by keyword on LinkedIn."""
        context = await self.browser.get_context()
        page = await context.new_page()
        try:
            q_enc = urllib.parse.quote(query)
            url = f"https://www.linkedin.com/search/results/content/?keywords={q_enc}"
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)

            state = await self.session.detect_session_state(page)
            if state != SessionState.AUTHENTICATED:
                return []

            try:
                await page.wait_for_selector(
                    ".feed-shared-update-v2, .search-results-container", timeout=12000
                )
            except Exception:
                return []

            updates = await page.query_selector_all(".feed-shared-update-v2")
            items: list[dict[str, Any]] = []
            for upd in updates[:limit]:
                actor_el = await upd.query_selector(".update-components-actor__name")
                desc_el = await upd.query_selector(".update-components-text")
                link_el = await upd.query_selector("a[href*='urn:li:activity']")
                if desc_el:
                    items.append(
                        {
                            "author": (await actor_el.inner_text()).strip()
                            if actor_el
                            else "Member",
                            "text": (await desc_el.inner_text()).strip(),
                            "url": await link_el.get_attribute("href")
                            if link_el
                            else "",
                        }
                    )
            return items
        finally:
            await page.close()
