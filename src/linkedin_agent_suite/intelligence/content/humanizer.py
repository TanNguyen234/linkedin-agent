"""Editorial humanizer with deep writing quality rules ported from linkedin-agent-skill."""

from __future__ import annotations

import re
from typing import Any

# Banned AI Clichés & Buzzwords
BANNED_WORDS = [
    "delve",
    "tapestry",
    "testament",
    "beacon",
    "game-changer",
    "game changer",
    "transformative",
    "revolutionize",
    "pivotal",
    "foster",
    "embark",
    "unleash",
    "elevate",
    "synergy",
    "paradigm shift",
    "plethora",
    "harness",
    "realm",
    "furthermore",
    "moreover",
    "in conclusion",
    "it is worth noting",
]

# Invisible Unicode characters
INVISIBLE_CHARS = ["\u200b", "\u200c", "\u200d", "\ufeff", "\u2060", "\u00a0", "\u202f"]


def clean_invisible_unicode(text: str) -> str:
    for ch in INVISIBLE_CHARS:
        text = text.replace(ch, " ")
    return text


def detect_cliches(text: str) -> list[str]:
    lower = text.lower()
    return [word for word in BANNED_WORDS if word in lower]


def humanize_text(text: str) -> str:
    """Clean draft text removing slop, invisible characters, and formatting clutter."""
    cleaned = clean_invisible_unicode(text)

    # Strip excessive emojis (limit consecutive emojis)
    cleaned = re.sub(r"([\U00010000-\U0010ffff]){3,}", r"\1", cleaned)

    # Replace common AI phrases
    replacements = {
        r"\bdelve into\b": "examine",
        r"\ba testament to\b": "proof of",
        r"\bgame changer\b": "significant shift",
        r"\btransformative\b": "impactful",
        r"\bfoster\b": "build",
        r"\bharness the power of\b": "use",
        r"\ba tapestry of\b": "a collection of",
        r"\btapestry\b": "collection",
    }
    for pat, rep in replacements.items():
        cleaned = re.sub(pat, rep, cleaned, flags=re.IGNORECASE)

    return cleaned.strip()


def quality_report(text: str) -> dict[str, Any]:
    """Score text against editorial standards."""
    cliches = detect_cliches(text)
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    avg_len = sum(len(s.split()) for s in sentences) / max(1, len(sentences))

    penalty = len(cliches) * 15
    score = max(0, 100 - penalty)

    return {
        "score": score,
        "cliches_found": cliches,
        "sentence_count": len(sentences),
        "avg_words_per_sentence": round(avg_len, 1),
        "is_humanized": len(cliches) == 0,
        "is_clean": len(cliches) == 0,
    }
