"""Real LinkedIn People search service."""

from __future__ import annotations

import logging
import urllib.parse
from typing import Any

from ..browser.manager import BrowserManager
from ..session.manager import SessionManager, SessionState

logger = logging.getLogger(__name__)


class PeopleService:
    def __init__(self, browser: BrowserManager):
        self.browser = browser
        self.session = SessionManager(browser)

    async def search_people(
        self, query: str, filters: dict[str, Any] | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Search people on LinkedIn and extract actual normalized results."""
        context = await self.browser.get_context()
        page = await context.new_page()
        try:
            q_enc = urllib.parse.quote(query)
            url = f"https://www.linkedin.com/search/results/people/?keywords={q_enc}"
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)

            state = await self.session.detect_session_state(page)
            if state in (SessionState.CHECKPOINT, SessionState.ACCOUNT_RESTRICTED):
                return []

            try:
                await page.wait_for_selector(
                    ".reusable-search__result-container, .search-results-container",
                    timeout=12000,
                )
            except Exception:
                return []

            cards = await page.query_selector_all(".reusable-search__result-container")
            results: list[dict[str, Any]] = []

            for card in cards[:limit]:
                name_el = await card.query_selector(
                    "span[aria-hidden='true'], .entity-result__title-text a"
                )
                name = (await name_el.inner_text()).strip() if name_el else ""
                if not name or "LinkedIn Member" in name:
                    continue

                link_el = await card.query_selector("a.app-aware-link[href*='/in/']")
                href = await link_el.get_attribute("href") if link_el else ""
                href_str = str(href or "")
                identifier = (
                    href_str.split("/in/")[1].split("/")[0].split("?")[0]
                    if "/in/" in href_str
                    else ""
                )

                headline_el = await card.query_selector(
                    ".entity-result__primary-subtitle"
                )
                headline = (
                    (await headline_el.inner_text()).strip() if headline_el else ""
                )

                loc_el = await card.query_selector(".entity-result__secondary-subtitle")
                loc = (await loc_el.inner_text()).strip() if loc_el else ""

                degree_el = await card.query_selector(
                    ".entity-result__badge-text, span:has-text('degree')"
                )
                degree = (await degree_el.inner_text()).strip() if degree_el else ""

                results.append(
                    {
                        "name": name,
                        "identifier": identifier,
                        "profile_url": f"https://www.linkedin.com/in/{identifier}/"
                        if identifier
                        else href,
                        "headline": headline,
                        "location": loc,
                        "connection_degree": degree,
                    }
                )
            return results
        finally:
            await page.close()
