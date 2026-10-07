"""Validates factual claims to prevent hallucination."""
import re
from typing import List, Tuple

def validate_claims(post_body: str, source_facts: List[str]) -> Tuple[bool, List[str]]:
    warnings = []
    # Check for fabricated metrics ($100k, 10x, 99.9%)
    numbers = re.findall(r"\b\d+(?:\.\d+)?%|\$\d+(?:,\d+)?|\b\d+x\b", post_body)
    for n in numbers:
        matched = any(n in fact for fact in source_facts)
        if not matched:
            warnings.append(f"Unverified metric detected: '{n}'. Ensure this is backed by real project data.")
    return len(warnings) == 0, warnings
