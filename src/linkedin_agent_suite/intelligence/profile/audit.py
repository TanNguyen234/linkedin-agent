"""5-Dimension Profile Audit Engine."""
import re
from typing import Dict, Any
from ...core.models import Profile
from .keywords import ROLE_KEYWORDS, GENERIC_STRONG_SIGNALS, WEAK_PHRASES, keyword_coverage

def clamp(score: float) -> int:
    return max(0, min(100, int(round(score))))

def audit_profile(profile: Profile, target_role: str = "agentic-ai-systems-engineer") -> Dict[str, Any]:
    full_text = "\n".join([
        profile.headline,
        profile.about,
        "\n".join([f"{e.title} {e.company} {' '.join(e.bullets)} {e.description}" for e in profile.experience]),
        " ".join(profile.skills)
    ])
    
    keywords = ROLE_KEYWORDS.get(target_role, ROLE_KEYWORDS["agentic-ai-systems-engineer"])
    kw = keyword_coverage(full_text, keywords)
    
    skills_bonus = 20 if len(profile.skills) >= 20 else len(profile.skills)
    searchability_score = clamp(kw["score"] * 0.8 + skills_bonus)
    searchability = {
        "dimension": "Recruiter searchability",
        "score": searchability_score,
        "findings": [
            f"Keyword coverage for {target_role}: {kw['score']}% ({len(kw['present'])}/{len(keywords)})",
            f"Skills listed: {len(profile.skills)} (Target: 20-50)"
        ],
        "recommendations": [f"Add missing keywords: {', '.join(kw['missing'][:6])}"] if kw["missing"] else []
    }
    
    headline_len = len(profile.headline)
    about_words = len(profile.about.split())
    weak_hits = [p for p in WEAK_PHRASES if p in full_text.lower()]
    clarity_score = clamp(
        100 - len(weak_hits) * 12 -
        (40 if headline_len == 0 else 15 if headline_len > 220 else 0) -
        (25 if about_words < 50 else 10 if about_words > 500 else 0)
    )
    clarity = {
        "dimension": "Clarity",
        "score": clarity_score,
        "findings": [
            f"Headline length: {headline_len}/220 chars",
            f"About length: {about_words} words (sweet spot: 150-350)",
            f"Weak/cliche phrases: {', '.join(weak_hits) if weak_hits else 'None detected'}"
        ],
        "recommendations": ["Replace weak phrases with concrete impact."] if weak_hits else []
    }
    
    all_bullets = [b for e in profile.experience for b in e.bullets]
    with_nums = [b for b in all_bullets if re.search(r"\d", b)]
    strong_verbs = [b for b in all_bullets if any(b.lower().strip().startswith(v) for v in GENERIC_STRONG_SIGNALS)]
    
    credibility_score = 20 if not all_bullets else clamp((len(with_nums) / len(all_bullets)) * 60 + (len(strong_verbs) / len(all_bullets)) * 40)
    credibility = {
        "dimension": "Credibility & Metrics",
        "score": credibility_score,
        "findings": [
            f"{len(with_nums)}/{len(all_bullets)} bullets contain metrics",
            f"{len(strong_verbs)}/{len(all_bullets)} bullets start with strong verbs"
        ],
        "recommendations": ["Add quantitative metrics (latency, scale, cost, users) to experience bullets."] if len(with_nums) < len(all_bullets) / 2 else []
    }
    
    ai_kw = keyword_coverage(full_text, ROLE_KEYWORDS["agentic-ai-systems-engineer"])
    positioning_score = clamp(ai_kw["score"] + (15 if profile.featured_links else 0))
    positioning = {
        "dimension": "AI / Engineering Positioning",
        "score": positioning_score,
        "findings": [
            f"AI/agentic keyword coverage: {ai_kw['score']}%",
            f"Featured links: {len(profile.featured_links)}"
        ],
        "recommendations": [f"Weave in AI terms: {', '.join(ai_kw['missing'][:5])}"] if ai_kw["missing"] else []
    }
    
    has_cta = bool(re.search(r"\b(dm|reach out|contact|email|open to|let's talk)\b", profile.about, re.I))
    conversion_score = clamp((50 if has_cta else 10) + (25 if profile.featured_links else 0) + (25 if profile.custom_url else 0))
    conversion = {
        "dimension": "Conversion (CTA)",
        "score": conversion_score,
        "findings": [
            "Clear CTA present in About" if has_cta else "No CTA detected in About",
            f"Custom URL: {profile.custom_url or 'None'}"
        ],
        "recommendations": ["Add clear call to action at the bottom of About."] if not has_cta else []
    }
    
    dimensions = [searchability, clarity, credibility, positioning, conversion]
    overall = clamp(sum(d["score"] for d in dimensions) / len(dimensions))
    
    return {
        "target_role": target_role,
        "overall": overall,
        "dimensions": dimensions
    }
