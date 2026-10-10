"""Real deep profile extraction service for LinkedIn."""

from __future__ import annotations

import asyncio
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
            # Wait for client-side redirection from /in/me/ to actual username
            for _ in range(10):
                if "/in/me" not in page.url.lower():
                    break
                await asyncio.sleep(1)

            state = await self.session.detect_session_state(page)
            if state != SessionState.AUTHENTICATED:
                raise ExtractionError(f"Cannot fetch profile; session state is {state.value}")

            url = page.url
            identifier = (
                url.split("/in/")[1].split("/")[0].split("?")[0]
                if "/in/" in url and "/in/me" not in url
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
            # Allow client-side rendering / hydration to settle
            await asyncio.sleep(2)

            state = await self.session.detect_session_state(page)
            if state in (SessionState.LOGIN_REQUIRED, SessionState.AUTHWALL, SessionState.CHECKPOINT):
                raise ExtractionError(f"LinkedIn session challenge encountered: {state.value}")

            # 1. Basic header info - Name
            name_el = await page.query_selector(
                "h1, .text-heading-xlarge, main section:nth-of-type(1) h2, .pv-text-details__left-panel h2"
            )
            full_name = (await name_el.inner_text()).strip() if name_el else ""
            if not full_name or "notification" in full_name.lower():
                sec_headings = await page.query_selector_all("main section h2")
                for sh in sec_headings:
                    txt = (await sh.inner_text()).strip()
                    if txt and "notification" not in txt.lower():
                        full_name = txt
                        break

            # Headline
            headline_el = await page.query_selector(
                ".text-body-medium.break-words, div[data-generated-suggestion-target], .pv-text-details__left-panel div.text-body-medium"
            )
            headline = (await headline_el.inner_text()).strip() if headline_el else ""

            # Location
            loc_el = await page.query_selector(
                "span.text-body-small.inline.t-black--light.break-words, span.text-body-small.inline.t-black--light"
            )
            location = (await loc_el.inner_text()).strip() if loc_el else ""

            # Top section line inspection fallback
            top_sec = await page.query_selector("main section")
            if top_sec:
                top_text = await top_sec.inner_text()
                lines = [line.strip() for line in top_text.split("\n") if line.strip()]
                if not full_name and lines:
                    full_name = lines[0]
                if not headline and len(lines) > 2:
                    for line in lines[1:6]:
                        if any(k in line for k in ["|", "•", "Engineer", "Student", "Developer", "Specialist", "Intern"]):
                            headline = line
                            break
                if not location:
                    for line in lines:
                        if any(c in line for c in ["Vietnam", "City", "United", "Area", "Remote"]):
                            location = line
                            break

            # 2. About section
            about = ""
            about_el = await page.query_selector(
                "#about ~ .display-flex .inline-show-more-text, section:has(#about) .inline-show-more-text"
            )
            if about_el:
                about = (await about_el.inner_text()).strip()
            else:
                about_sec = await page.query_selector("section:has-text('About')")
                if about_sec:
                    sec_lines = (await about_sec.inner_text()).split("\n")
                    collect = False
                    about_collected = []
                    for sl in sec_lines:
                        sl_clean = sl.strip()
                        if sl_clean == "About":
                            collect = True
                            continue
                        if collect:
                            if sl_clean in [
                                "Activity", "Analytics", "Suggested for you", "Experience",
                                "Education", "Skills", "Resources", "Interests"
                            ]:
                                break
                            if sl_clean and sl_clean != "… more":
                                about_collected.append(sl_clean)
                    about = "\n".join(about_collected).strip()

            # 3. Experience section
            experiences: list[ExperienceItem] = []
            exp_elements = await page.query_selector_all(
                "#experience ~ .pvs-list__outer-container > ul > li, section:has(#experience) ul > li"
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
                "#education ~ .pvs-list__outer-container > ul > li, section:has(#education) ul > li"
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
            # Fallback for education if listed in top card
            if not education and top_sec:
                top_text = await top_sec.inner_text()
                for edu_line in top_text.split("\n"):
                    l_clean = edu_line.strip()
                    if any(edu_kw in l_clean for edu_kw in ["University", "College", "Institute", "Academy", "Đại học"]):
                        education.append(EducationItem(school=l_clean, degree=None))
                        break

            # 5. Skills section
            skills: list[str] = []
            skill_elements = await page.query_selector_all(
                "#skills ~ .pvs-list__outer-container > ul > li .t-bold span[aria-hidden='true'], section:has(#skills) ul > li .t-bold span[aria-hidden='true']"
            )
            for el in skill_elements:
                s_text = (await el.inner_text()).strip()
                if s_text and s_text not in skills:
                    skills.append(s_text)

            # Core skills from headline, about, and core technologies
            combined_source = f"{headline} {about}"
            known_techs = [
                "Python", "PyTorch", "TensorFlow", "scikit-learn", "LangGraph", "LangChain",
                "FastAPI", "Docker", "OpenCV", "YOLO", "MongoDB", "PostgreSQL",
                "Vector Databases", "RAG", "LLM", "LLM Agents", "Computer Vision",
                "Deep Learning", "Machine Learning", "NLP", "Kubernetes", "Git"
            ]
            for tech in known_techs:
                if tech.lower() in combined_source.lower() and tech not in skills:
                    skills.append(tech)

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
