"""Adaptive voice profile learning from approved posts."""

from __future__ import annotations

from typing import Any


class VoiceLearner:
    @staticmethod
    def compute_voice_profile(posts: list[str]) -> dict[str, Any]:
        if not posts:
            return {"style": "default", "avg_words": 150}

        total_words = sum(len(p.split()) for p in posts)
        avg_words = total_words // len(posts)
        emoji_count = sum(sum(1 for c in p if ord(c) > 127) for p in posts)

        return {
            "avg_length_words": avg_words,
            "emoji_density": round(emoji_count / max(1, total_words), 3),
            "sample_count": len(posts),
            "tone": "concise technical" if avg_words < 120 else "narrative technical",
        }
