"""Real LinkedIn Company lookup service."""

from __future__ import annotations

import logging
from typing import Any

from ..browser.manager import BrowserManager
from ..session.manager import SessionManager

logger = logging.getLogger(__name__)


class CompanyService:
    def __init__(self, browser: BrowserManager):
        self.browser = browser
        self.session = SessionManager(browser)

    async def get_company(self, identifier: str) -> dict[str, Any]:
        """Extract real company data from LinkedIn."""
        context = await self.browser.get_context()
        page = await context.new_page()
        try:
            url = (
                f"https://www.linkedin.com/company/{identifier}/"
                if not identifier.startswith("http")
                else identifier
            )
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)

            name_el = await page.query_selector("h1, .org-top-card-summary__title")
            name = (await name_el.inner_text()).strip() if name_el else identifier

            tagline_el = await page.query_selector(
                ".org-top-card-summary__tagline, p.org-top-card-summary__tagline"
            )
            about = (await tagline_el.inner_text()).strip() if tagline_el else ""

            info_items = await page.query_selector_all(
                ".org-top-card-summary-info-list__info-item, .org-page-details__definition-text"
            )
            industry = ""
            employees = ""
            for item in info_items:
                t = (await item.inner_text()).strip()
                if "employees" in t.lower() or "associated members" in t.lower():
                    employees = t
                elif not industry and len(t) < 40 and not any(c.isdigit() for c in t):
                    industry = t

            return {
                "name": name,
                "identifier": identifier,
                "linkedin_url": url,
                "about": about,
                "industry": industry,
                "employee_count": employees,
            }
        finally:
            await page.close()
