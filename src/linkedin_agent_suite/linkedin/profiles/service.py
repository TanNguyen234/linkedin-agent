"""Real deep profile extraction service for LinkedIn."""

from __future__ import annotations

import logging
from typing import Any

from ...core.models import EducationItem, ExperienceItem, Profile
from ..browser.manager import BrowserManager
from ..session.manager import SessionManager

logger = logging.getLogger(__name__)


class ProfileService:
    def __init__(self, browser: BrowserManager):
        self.browser = browser
        self.session = SessionManager(browser)

    async def get_my_profile(self) -> Profile:
        """Fetch authenticated user's own profile."""
        context = await self.browser.get_context()
        page = await context.new_page()
        try:
            await page.goto(
                "https://www.linkedin.com/in/me/",
                wait_until="domcontentloaded",
                timeout=25000,
            )
            url = page.url
            identifier = (
                url.split("/in/")[1].split("/")[0].split("?")[0]
                if "/in/" in url
                else "me"
            )
            return await self.get_profile(identifier, page=page)
        finally:
            await page.close()

    async def get_profile(self, identifier: str, page: Any | None = None) -> Profile:
        """Fetch deep profile information from LinkedIn page."""
        should_close = False
        if page is None:
            context = await self.browser.get_context()
            page = await context.new_page()
            should_close = True
            url = (
                f"https://www.linkedin.com/in/{identifier}/"
                if not identifier.startswith("http")
                else identifier
            )
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)

        try:
            # 1. Basic header info
            name_el = await page.query_selector("h1, .text-heading-xlarge")
            full_name = (
                (await name_el.inner_text()).strip() if name_el else "LinkedIn Member"
            )

            headline_el = await page.query_selector(".text-body-medium.break-words")
            headline = (await headline_el.inner_text()).strip() if headline_el else ""

            loc_el = await page.query_selector(
                ".text-body-small.inline.t-black--light.break-words"
            )
            location = (await loc_el.inner_text()).strip() if loc_el else ""

            # 2. About section
            about_el = await page.query_selector(
                "#about ~ div .inline-show-more-text, section:has(#about) .display-flex"
            )
            about = (await about_el.inner_text()).strip() if about_el else ""

            # 3. Experience section
            exp_items: list[ExperienceItem] = []
            exp_elements = await page.query_selector_all(
                "section:has(#experience) li.artdeco-list__item"
            )
            for el in exp_elements:
                title_el = await el.query_selector(
                    ".mr1.t-bold span[aria-hidden='true']"
                )
                comp_el = await el.query_selector(
                    ".t-14.t-normal span[aria-hidden='true']"
                )
                time_el = await el.query_selector(
                    ".t-14.t-normal.t-black--light span[aria-hidden='true']"
                )
                desc_el = await el.query_selector(".inline-show-more-text")
                if title_el or comp_el:
                    exp_items.append(
                        ExperienceItem(
                            title=(await title_el.inner_text()).strip()
                            if title_el
                            else "",
                            company=(await comp_el.inner_text()).strip()
                            if comp_el
                            else "",
                            duration=(await time_el.inner_text()).strip()
                            if time_el
                            else None,
                            description=(await desc_el.inner_text()).strip()
                            if desc_el
                            else "",
                        )
                    )

            # 4. Education section
            edu_items: list[EducationItem] = []
            edu_elements = await page.query_selector_all(
                "section:has(#education) li.artdeco-list__item"
            )
            for el in edu_elements:
                school_el = await el.query_selector(
                    ".mr1.t-bold span[aria-hidden='true']"
                )
                deg_el = await el.query_selector(
                    ".t-14.t-normal span[aria-hidden='true']"
                )
                if school_el:
                    edu_items.append(
                        EducationItem(
                            school=(await school_el.inner_text()).strip(),
                            degree=(await deg_el.inner_text()).strip()
                            if deg_el
                            else None,
                        )
                    )

            # 5. Skills section
            skills: list[str] = []
            skill_elements = await page.query_selector_all(
                "section:has(#skills) li.artdeco-list__item, section:has(#skills) .hoverable-link-text"
            )
            for el in skill_elements:
                s_name = (await el.inner_text()).strip()
                if s_name and len(s_name) < 50 and s_name not in skills:
                    skills.append(s_name)

            return Profile(
                username=identifier,
                full_name=full_name,
                headline=headline,
                location=location,
                about=about,
                experience=exp_items,
                education=edu_items,
                skills=skills,
                profile_url=f"https://www.linkedin.com/in/{identifier}/",
            )
        finally:
            if should_close:
                await page.close()
