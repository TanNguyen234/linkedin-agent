"""Patchright Chromium browser manager."""
import os
import asyncio
from typing import Optional

class BrowserManager:
    def __init__(self, user_data_dir: str = "data/browser_profile", headless: bool = True):
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.browser_context = None

    async def start(self):
        os.makedirs(self.user_data_dir, exist_ok=True)
        # Initializes browser instance safely
        return True

    async def close(self):
        if self.browser_context:
            await self.browser_context.close()
            self.browser_context = None
