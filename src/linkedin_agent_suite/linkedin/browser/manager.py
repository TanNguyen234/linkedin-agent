"""Patchright Chromium browser manager with persistent session support."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from patchright.async_api import BrowserContext, Page, Playwright, async_playwright

from ...core.errors import BrowserBusyError, BrowserError

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages the Patchright Chromium instance with persistent context."""

    def __init__(
        self,
        user_data_dir: Path | str = "data/browser_profile",
        headless: bool = True,
        slow_mo: int = 50,
        viewport: dict[str, int] | None = None,
        executable_path: str | None = None,
    ):
        self.user_data_dir = Path(user_data_dir)
        self.headless = headless
        self.slow_mo = slow_mo
        self.viewport = viewport or {"width": 1280, "height": 800}
        self.executable_path = executable_path

        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None

    async def get_context(self) -> BrowserContext:
        return await self.start()

    async def start(self) -> BrowserContext:
        """Launch the persistent Chromium context."""
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        if self._context:
            return self._context

        retries = 3
        for attempt in range(retries):
            try:
                self._playwright = await async_playwright().start()
                launch_args = [
                    "--disable-blink-features=AutomationControlled",
                    "--webrtc-ip-handling-policy=disable_non_proxied_udp",
                ]
                options: dict[str, Any] = {
                    "user_data_dir": str(self.user_data_dir),
                    "headless": self.headless,
                    "slow_mo": self.slow_mo,
                    "viewport": self.viewport,
                    "args": launch_args,
                }
                if self.executable_path:
                    options["executable_path"] = self.executable_path

                self._context = await self._playwright.chromium.launch_persistent_context(
                    **options
                )
                logger.info(
                    "Chromium persistent context launched at %s", self.user_data_dir
                )
                return self._context
            except Exception as e:
                if self._playwright:
                    try:
                        await self._playwright.stop()
                    except Exception:
                        pass
                    self._playwright = None

                is_busy = (
                    "Target page, context or browser has been closed" in str(e)
                    or "lock" in str(e).lower()
                    or "processsingleton" in str(e).lower()
                )
                if is_busy and attempt < retries - 1:
                    logger.warning(
                        "Browser profile busy or locked (attempt %d/%d). Retrying in 2s...",
                        attempt + 1,
                        retries,
                    )
                    await asyncio.sleep(2.0)
                    continue

                if is_busy:
                    raise BrowserBusyError(
                        f"Browser profile is currently locked: {e}. "
                        f"Ensure no other Chromium process is accessing '{self.user_data_dir}'."
                    )
                raise BrowserError(f"Failed to start Patchright browser: {e}")
        raise BrowserBusyError(f"Failed to acquire browser profile at '{self.user_data_dir}' after retries.")

    async def get_page(self) -> Page:
        """Get an active page from context, or create a new one."""
        ctx = await self.start()
        pages = ctx.pages
        if pages:
            return pages[0]
        return await ctx.new_page()

    async def close(self) -> None:
        """Clean shutdown of browser context."""
        if self._context:
            try:
                await self._context.close()
            except Exception as e:
                logger.warning("Error closing context: %s", e)
            self._context = None
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception as e:
                logger.warning("Error stopping playwright: %s", e)
            self._playwright = None
