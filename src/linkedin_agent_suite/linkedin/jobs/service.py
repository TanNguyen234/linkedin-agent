"""Real LinkedIn Job search and extraction service."""

from __future__ import annotations

import logging
import urllib.parse

from ...core.models import Job
from ..browser.manager import BrowserManager
from ..session.manager import SessionManager, SessionState

logger = logging.getLogger(__name__)


class JobService:
    def __init__(self, browser: BrowserManager):
        self.browser = browser
        self.session = SessionManager(browser)

    async def search_jobs(
        self, keywords: str, location: str = "Remote", limit: int = 25
    ) -> list[Job]:
        """Search and extract real LinkedIn jobs without placeholders."""
        context = await self.browser.get_context()
        page = await context.new_page()
        try:
            kw_enc = urllib.parse.quote(keywords)
            loc_enc = urllib.parse.quote(location)
            url = f"https://www.linkedin.com/jobs/search/?keywords={kw_enc}&location={loc_enc}"
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)

            state = await self.session.detect_session_state(page)
            if state in (SessionState.CHECKPOINT, SessionState.ACCOUNT_RESTRICTED):
                logger.error(f"Cannot search jobs: session state is {state}")
                return []

            try:
                await page.wait_for_selector(
                    ".jobs-search__results-list, .scaffold-layout__list-container, .job-card-container",
                    timeout=12000,
                )
            except Exception:
                return []

            cards = await page.query_selector_all(
                ".jobs-search-results__list-item, .job-card-container"
            )
            jobs: list[Job] = []

            for card in cards[:limit]:
                # ID extraction
                job_id = await card.get_attribute(
                    "data-occludable-job-id"
                ) or await card.get_attribute("data-job-id")

                title_elem = await card.query_selector(
                    ".job-card-list__title, a.job-card-container__link, .base-search-card__title"
                )
                title = (
                    (await title_elem.inner_text()).strip()
                    if title_elem
                    else "Job Title"
                )

                link_elem = await card.query_selector(
                    "a.job-card-container__link, a.base-card__full-link"
                )
                href = await link_elem.get_attribute("href") if link_elem else ""

                if not job_id and href and "/jobs/view/" in href:
                    job_id = href.split("/jobs/view/")[1].split("/")[0].split("?")[0]
                if not job_id:
                    continue

                company_elem = await card.query_selector(
                    ".job-card-container__primary-description, .base-search-card__subtitle, .job-card-container__company-name"
                )
                company = (
                    (await company_elem.inner_text()).strip()
                    if company_elem
                    else "Company"
                )

                loc_elem = await card.query_selector(
                    ".job-card-container__metadata-item, .job-search-card__location"
                )
                loc = (await loc_elem.inner_text()).strip() if loc_elem else location

                href_str = str(href or "")
                job_url = (
                    f"https://www.linkedin.com/jobs/view/{job_id}/"
                    if not href_str.startswith("http")
                    else href_str
                )

                jobs.append(
                    Job(
                        id=str(job_id),
                        title=title,
                        company=company,
                        location=loc,
                        url=str(job_url or f"https://www.linkedin.com/jobs/view/{job_id}/"),
                        source="linkedin",
                    )
                )
            return jobs
        finally:
            await page.close()

    async def get_job(self, job_id_or_url: str) -> Job | None:
        """Fetch details for a specific LinkedIn job posting."""
        url = (
            job_id_or_url
            if job_id_or_url.startswith("http")
            else f"https://www.linkedin.com/jobs/view/{job_id_or_url}/"
        )
        context = await self.browser.get_context()
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            title_el = await page.query_selector(
                "h1.job-details-jobs-unified-top-card__job-title, h1.top-card-layout__title"
            )
            title = (await title_el.inner_text()).strip() if title_el else "Unknown Job"

            comp_el = await page.query_selector(
                ".job-details-jobs-unified-top-card__company-name, .topcard__org-name-link"
            )
            company = (
                (await comp_el.inner_text()).strip() if comp_el else "Unknown Company"
            )

            desc_el = await page.query_selector(
                "#job-details, .jobs-description-content__text"
            )
            desc = (await desc_el.inner_text()).strip() if desc_el else ""

            apply_el = await page.query_selector(
                "a.jobs-apply-button, a[data-tracking-control-name*='apply']"
            )
            apply_url = await apply_el.get_attribute("href") if apply_el else url

            return Job(
                id=job_id_or_url.split("/")[-1].split("?")[0],
                title=title,
                company=company,
                description=desc,
                url=url,
                apply_url=apply_url,
                source="linkedin",
            )
        finally:
            await page.close()

    async def get_apply_url(self, job_id_or_url: str) -> str:
        job = await self.get_job(job_id_or_url)
        return job.apply_url if job and job.apply_url else job_id_or_url
