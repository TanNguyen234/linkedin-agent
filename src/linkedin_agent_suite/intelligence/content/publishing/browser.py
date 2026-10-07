"""Browser publisher fallback with manual confirmation."""


class BrowserPublisher:
    def publish_post(self, text: str) -> tuple[bool, str]:
        return (
            False,
            "Browser publishing is gated: prefer official API or approve manual post.",
        )
