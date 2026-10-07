"""Anti-AI cliche detector and humanizer."""
import re

BANNED_AI_WORDS = [
    "delve", "testament", "tapestry", "game changer", "revolutionary",
    "in today's fast-paced world", "furthermore", "moreover", "beacon", "unleash"
]

def humanize_text(text: str) -> str:
    cleaned = text
    for w in BANNED_AI_WORDS:
        cleaned = re.sub(r"\b" + re.escape(w) + r"\b", "", cleaned, flags=re.I)
    cleaned = re.sub(r"!{2,}", "!", cleaned)
    cleaned = re.sub(r"🚀{2,}", "🚀", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()

def quality_report(text: str) -> dict:
    hits = [w for w in BANNED_AI_WORDS if re.search(r"\b" + re.escape(w) + r"\b", text, re.I)]
    return {
        "word_count": len(text.split()),
        "cliches_found": hits,
        "is_clean": len(hits) == 0
    }
