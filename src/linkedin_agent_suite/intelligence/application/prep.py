"""Evidence-grounded job application preparation linking requirements to verified proof."""

from __future__ import annotations

from enum import Enum
from typing import Any

from ...core.models import Job, Profile


class EvidenceLevel(str, Enum):
    VERIFIED_PROJECT_OR_EXPERIENCE = "VERIFIED_PROJECT_OR_EXPERIENCE"
    PROFILE_SKILL_ONLY = "PROFILE_SKILL_ONLY"
    INFERRED = "INFERRED"
    UNSUPPORTED = "UNSUPPORTED"


def prepare_application(job: Job, profile: Profile) -> dict[str, Any]:
    """Map requirements to tiered evidence levels without fabricating production claims."""
    claims: list[dict[str, Any]] = []
    jd_text = (job.title + " " + job.description).lower()

    # Track skills evaluated
    verified_skills: list[str] = []
    skill_only_items: list[str] = []

    for skill in profile.skills:
        skill_lower = skill.lower()
        if skill_lower not in jd_text:
            continue

        # Look for commercial or project evidence in experience
        ev_found = []
        for exp in profile.experience:
            in_desc = skill_lower in exp.description.lower()
            in_bullets = any(skill_lower in b.lower() for b in exp.bullets)
            if in_desc or in_bullets:
                ev_found.append(f"{exp.title} at {exp.company}")

        if ev_found:
            evidence_level = EvidenceLevel.VERIFIED_PROJECT_OR_EXPERIENCE
            claim_text = f"Applied {skill} in experience as {ev_found[0]}."
            verified_skills.append(skill)
            source = ev_found[0]
        else:
            evidence_level = EvidenceLevel.PROFILE_SKILL_ONLY
            claim_text = f"{skill} is included in profile skill set."
            skill_only_items.append(skill)
            source = "Profile Skills List"

        claims.append(
            {
                "requirement": skill,
                "evidence_level": evidence_level.value,
                "evidence_source": source,
                "claim": claim_text,
            }
        )

    # Missing requirements check
    key_jd_terms = ["python", "typescript", "react", "fastapi", "docker", "kubernetes", "aws", "sql"]
    missing_requirements: list[str] = []
    for term in key_jd_terms:
        if term in jd_text and not any(term == s.lower() for s in profile.skills) and term not in profile.full_text().lower():
            missing_requirements.append(term)
            claims.append(
                {
                    "requirement": term,
                    "evidence_level": EvidenceLevel.UNSUPPORTED.value,
                    "evidence_source": "None",
                    "claim": f"No direct evidence for {term} in profile.",
                }
            )

    # Grounded talking points (only for verified or skill-only items)
    talking_points = [
        c["claim"]
        for c in claims
        if c["evidence_level"] in (
            EvidenceLevel.VERIFIED_PROJECT_OR_EXPERIENCE.value,
            EvidenceLevel.PROFILE_SKILL_ONLY.value,
        )
    ]

    # Generate honest, grounded cover note without architectural or scale embellishments
    if verified_skills:
        experience_summary = f"With hands-on experience in {', '.join(verified_skills)}"
    elif skill_only_items:
        experience_summary = f"With skills including {', '.join(skill_only_items)}"
    else:
        experience_summary = "With relevant technical interests"

    cover_note = (
        f"Hi {job.company} Team,\n\n"
        f"I am writing regarding the {job.title} position. "
        f"{experience_summary}, I am interested in contributing to your team's initiatives.\n\n"
        f"Best regards,\n{profile.full_name or 'Applicant'}"
    )

    verified_count = sum(
        1
        for c in claims
        if c["evidence_level"] == EvidenceLevel.VERIFIED_PROJECT_OR_EXPERIENCE.value
    )
    total_evaluated = max(1, len([c for c in claims if c["evidence_level"] != EvidenceLevel.UNSUPPORTED.value]))
    verified_ratio = round(verified_count / total_evaluated, 2)

    return {
        "job_id": job.id,
        "company": job.company,
        "title": job.title,
        "claims": claims,
        "missing_requirements": missing_requirements,
        "talking_points": talking_points,
        "pitch": cover_note,
        "verified_ratio": verified_ratio,
    }
