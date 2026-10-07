"""People search service."""
from typing import List, Dict
from ..browser.manager import BrowserManager

class PeopleService:
    def __init__(self, browser: BrowserManager):
        self.browser = browser

    async def search_people(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        page = await self.browser.get_page()
        url = f"https://www.linkedin.com/search/results/people/?keywords={query}"
        await page.goto(url, wait_until="domcontentloaded")
        return [{"query": query, "url": url}]
