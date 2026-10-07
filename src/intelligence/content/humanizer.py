"""Removes generic AI cliches and polishes natural cadence."""
import re

BANNED_AI_WORDS = [
    "delve", "testament", "tapestry", "game changer", "revolutionary",
    "in today's fast-paced world", "furthermore", "moreover", "beacon", "unleash"
]

def humanize_text(text: str) -> str:
    cleaned = text
    for w in BANNED_AI_WORDS:
        cleaned = re.sub(re.escape(w), "", cleaned, flags=re.I)
    # Remove repeated exclamation marks or emoji spam
    cleaned = re.sub(r"!{2,}", "!", cleaned)
    cleaned = re.sub(r"🚀{2,}", "🚀", cleaned)
    return cleaned.strip()
