"""Real deep profile extraction service for LinkedIn."""

from __future__ import annotations

import logging
from typing import Any

from ...core.errors import ExtractionError
from ...core.models import EducationItem, ExperienceItem, Profile
from ..browser.manager import BrowserManager
from ..session.manager import SessionManager, SessionState

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
            state = await self.session.detect_session_state(page)
            if state != SessionState.AUTHENTICATED:
                raise ExtractionError(f"Cannot fetch profile; session state is {state.value}")

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
        """Fetch deep profile information from LinkedIn page without fabricated fallbacks."""
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
            state = await self.session.detect_session_state(page)
            if state in (SessionState.LOGIN_REQUIRED, SessionState.AUTHWALL, SessionState.CHECKPOINT):
                raise ExtractionError(f"LinkedIn session challenge encountered: {state.value}")

            # 1. Basic header info - Never use fabricated 'LinkedIn Member'
            name_el = await page.query_selector("h1, .text-heading-xlarge")
            full_name = (await name_el.inner_text()).strip() if name_el else ""

            headline_el = await page.query_selector(
                ".text-body-medium.break-words, div[data-generated-suggestion-target]"
            )
            headline = (await headline_el.inner_text()).strip() if headline_el else ""

            loc_el = await page.query_selector(
                "span.text-body-small.inline.t-black--light.break-words"
            )
            location = (await loc_el.inner_text()).strip() if loc_el else ""

            # 2. About section
            about = ""
            about_el = await page.query_selector("#about ~ .display-flex .inline-show-more-text")
            if about_el:
                about = (await about_el.inner_text()).strip()

            # 3. Experience section
            experiences: list[ExperienceItem] = []
            exp_elements = await page.query_selector_all(
                "#experience ~ .pvs-list__outer-container > ul > li"
            )
            for el in exp_elements:
                title_el = await el.query_selector(".t-bold span[aria-hidden='true']")
                company_el = await el.query_selector(".t-normal span[aria-hidden='true']")
                duration_el = await el.query_selector(
                    ".t-black--light span[aria-hidden='true']"
                )
                desc_el = await el.query_selector(".inline-show-more-text")

                exp_title = (await title_el.inner_text()).strip() if title_el else ""
                exp_company = (await company_el.inner_text()).strip() if company_el else ""
                exp_duration = (await duration_el.inner_text()).strip() if duration_el else None
                exp_desc = (await desc_el.inner_text()).strip() if desc_el else ""

                if exp_title or exp_company:
                    experiences.append(
                        ExperienceItem(
                            title=exp_title,
                            company=exp_company,
                            duration=exp_duration,
                            description=exp_desc,
                        )
                    )

            # 4. Education section
            education: list[EducationItem] = []
            edu_elements = await page.query_selector_all(
                "#education ~ .pvs-list__outer-container > ul > li"
            )
            for el in edu_elements:
                school_el = await el.query_selector(".t-bold span[aria-hidden='true']")
                degree_el = await el.query_selector(".t-normal span[aria-hidden='true']")
                school_name = (await school_el.inner_text()).strip() if school_el else ""
                degree_name = (await degree_el.inner_text()).strip() if degree_el else None
                if school_name:
                    education.append(
                        EducationItem(
                            school=school_name,
                            degree=degree_name,
                        )
                    )

            # 5. Skills section
            skills: list[str] = []
            skill_elements = await page.query_selector_all(
                "#skills ~ .pvs-list__outer-container > ul > li .t-bold span[aria-hidden='true']"
            )
            for el in skill_elements:
                s_text = (await el.inner_text()).strip()
                if s_text and s_text not in skills:
                    skills.append(s_text)

            profile = Profile(
                full_name=full_name,
                headline=headline,
                location=location,
                about=about,
                skills=skills,
                experience=experiences,
                education=education,
                profile_url=page.url,
            )
            return profile
        finally:
            if should_close:
                await page.close()
