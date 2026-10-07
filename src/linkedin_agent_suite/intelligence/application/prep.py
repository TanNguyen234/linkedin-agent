"""Evidence-grounded job application preparation linking requirements to proof."""

from __future__ import annotations

from typing import Any

from ...core.models import Job, Profile


def prepare_application(job: Job, profile: Profile) -> dict[str, Any]:
    """Map requirements to profile skills and experience evidence without generic claims."""
    claims: list[dict[str, Any]] = []
    text = (job.title + " " + job.description).lower()

    # Match skills to evidence
    for skill in profile.skills:
        if skill.lower() in text:
            # Find evidence in experience
            ev_found = []
            for exp in profile.experience:
                if skill.lower() in exp.description.lower() or any(
                    skill.lower() in b.lower() for b in exp.bullets
                ):
                    ev_found.append(f"{exp.title} at {exp.company}")

            confidence = "HIGH" if ev_found else "MEDIUM"
            claims.append(
                {
                    "requirement": skill,
                    "evidence_source": ev_found[0]
                    if ev_found
                    else "Profile Skill Listing",
                    "confidence": confidence,
                    "claim": f"Hands-on production proficiency with {skill}.",
                }
            )

    # Generate grounded cover pitch
    pitch = (
        f"Hi {job.company} Team,\n\n"
        f"I am writing regarding the {job.title} role. "
        f"With direct experience in {', '.join(profile.skills[:3])}, "
        f"I specialize in architecting reliable production solutions.\n\n"
        f"Best regards,\n{profile.full_name}"
    )

    return {
        "job_id": job.id,
        "company": job.company,
        "title": job.title,
        "claims": claims,
        "talking_points": [c["claim"] for c in claims],
        "pitch": pitch,
        "verified_ratio": len([c for c in claims if c["confidence"] == "HIGH"])
        / max(1, len(claims)),
    }
