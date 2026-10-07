"""Profile reading service."""
from ...core.models import Profile
from ..browser.manager import BrowserManager

class ProfileService:
    def __init__(self, browser: BrowserManager):
        self.browser = browser

    async def get_my_profile(self) -> Profile:
        page = await self.browser.get_page()
        await page.goto("https://www.linkedin.com/in/", wait_until="domcontentloaded")
        name = await page.locator("h1").first.inner_text() if await page.locator("h1").count() else "Member"
        headline = await page.locator(".text-body-medium").first.inner_text() if await page.locator(".text-body-medium").count() else ""
        return Profile(full_name=name.strip(), headline=headline.strip())

    async def get_profile(self, identifier: str) -> Profile:
        page = await self.browser.get_page()
        url = f"https://www.linkedin.com/in/{identifier}/" if not identifier.startswith("http") else identifier
        await page.goto(url, wait_until="domcontentloaded")
        name = await page.locator("h1").first.inner_text() if await page.locator("h1").count() else identifier
        return Profile(full_name=name.strip(), profile_url=url)
