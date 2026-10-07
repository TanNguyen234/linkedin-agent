"""LinkedIn jobs extraction service."""
from typing import List
from ...core.models import Job
from ..browser.manager import BrowserManager

class JobService:
    def __init__(self, browser: BrowserManager):
        self.browser = browser

    async def search_jobs(self, keywords: str, location: str = "Remote") -> List[Job]:
        url = f"https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}"
        return [Job(id="li-job-1", title=keywords, company="Featured Company", url=url, source="linkedin")]
