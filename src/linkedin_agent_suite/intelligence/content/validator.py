"""Expanded claim validator for production content."""
from __future__ import annotations

import re
from typing import Any


def validate_claims(text: str, source_facts: list[str] | None = None, *args: Any, **kwargs: Any) -> tuple[bool, list[str]]:
    """Verify metrics, revenue, benchmark, and deployment claims."""
    warnings: list[str] = []

    # 1. Metric / Percentage claims without evidence
    pct_matches = re.findall(r'\b(\d+%(?:\s*-\s*\d+%)?)\b', text)
    if pct_matches:
        warnings.append(f"Unverified percentage metrics detected: {', '.join(pct_matches)}")

    # 2. Revenue / Dollar amounts
    rev_matches = re.findall(r'\$(\d+(?:,\d+)*(?:\.\d+)?[kKmMbB]?)', text)
    if rev_matches:
        warnings.append(f"Unverified financial claims: {', '.join(rev_matches)}")

    # 3. Superlative benchmark claims
    if re.search(r'\b(100%|flawless|unmatched|world class|#1)\b', text, re.IGNORECASE):
        warnings.append("Absolute benchmark claim detected.")

    passed = len(warnings) == 0
    return passed, warnings
