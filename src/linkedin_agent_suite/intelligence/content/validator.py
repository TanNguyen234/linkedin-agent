"""Hard claim validation gate: blocks unverified numbers and unknown results."""
import re
from typing import List, Tuple

def validate_claims(post_body: str, source_facts: List[str]) -> Tuple[bool, List[str]]:
    warnings = []
    # Identify quantitative numbers ($100k, 10x, 99.9%, 500ms)
    numbers = re.findall(r"\b\d+(?:\.\d+)?%|\$\d+(?:,\d+)?|\b\d+x\b|\b\d+\s*(?:ms|k|m)\b", post_body)
    for n in numbers:
        matched = any(n.lower() in fact.lower() for fact in source_facts)
        if not matched:
            warnings.append(f"Unverified metric detected: '{n}'. Metric is not present in verified source facts.")
    return len(warnings) == 0, warnings
