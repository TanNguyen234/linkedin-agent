"""Browser publisher fallback with manual confirmation."""
from typing import Tuple

class BrowserPublisher:
    def publish_post(self, text: str) -> Tuple[bool, str]:
        return False, "Browser publishing is gated: prefer official API or approve manual post."
