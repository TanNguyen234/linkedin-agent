"""Voice profile learner and style parameters."""
import json
import os
from typing import Dict, Any

DEFAULT_VOICE = {
    "preferred_language": "English",
    "tone": "Technical, pragmatic, evidence-based",
    "sentence_length": "Medium (12-20 words)",
    "emoji_density": "Low (max 1-2 per post)",
    "hashtag_density": "Minimal (max 2-3 tags)",
    "avoid_fluff": True
}

def load_voice_profile(path: str = "data/profile/voice.json") -> Dict[str, Any]:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_VOICE
