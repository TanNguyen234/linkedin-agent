"""Company lookup service."""
from typing import Dict, Any
from ..browser.manager import BrowserManager

class CompanyService:
    def __init__(self, browser: BrowserManager):
        self.browser = browser

    async def get_company(self, identifier: str) -> Dict[str, Any]:
        url = f"https://www.linkedin.com/company/{identifier}/"
        return {"identifier": identifier, "url": url}
