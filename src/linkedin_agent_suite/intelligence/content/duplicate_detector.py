"""Multi-tier duplicate post detection engine."""

from __future__ import annotations

import hashlib


class DuplicateDetector:
    @staticmethod
    def is_duplicate(
        new_text: str, historical_posts: list[str], threshold: float = 0.75
    ) -> bool:
        new_hash = hashlib.sha256(new_text.strip().lower().encode("utf-8")).hexdigest()
        new_tokens = set(new_text.lower().split())

        for post in historical_posts:
            h = hashlib.sha256(post.strip().lower().encode("utf-8")).hexdigest()
            if h == new_hash:
                return True
            tokens = set(post.lower().split())
            overlap = len(new_tokens & tokens) / max(1, len(new_tokens | tokens))
            if overlap >= threshold:
                return True
        return False


def is_duplicate_content(
    new_text: str, historical_posts: list[str], threshold: float = 0.75
) -> bool:
    """Convenience functional helper for duplicate checking."""
    return DuplicateDetector.is_duplicate(new_text, historical_posts, threshold)
