"""Browser-based publishing fallback."""
from typing import Tuple

class BrowserPublisher:
    def __init__(self, browser_manager=None):
        self.browser_manager = browser_manager

    def publish_post(self, text: str) -> Tuple[bool, str]:
        # Gated fallback: browser posting requires manual interaction confirmation
        return False, "Browser publishing is gated: please use official API or approve manual post."
