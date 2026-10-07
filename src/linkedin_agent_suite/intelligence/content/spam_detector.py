"""Spam and duplicate detection."""


def is_duplicate(
    new_text: str, recent_posts: list[str], similarity_threshold: float = 0.75
) -> bool:
    new_words = set(new_text.lower().split())
    if not new_words:
        return False
    for p in recent_posts:
        old_words = set(p.lower().split())
        overlap = len(new_words & old_words) / max(len(new_words), 1)
        if overlap >= similarity_threshold:
            return True
    return False
