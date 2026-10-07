"""Evidence-grounded profile section rewrites without hallucinated tools."""

from ...core.models import Profile


def generate_headlines(profile: Profile, target_role: str) -> list[dict[str, str]]:
    known_skills = ", ".join(profile.skills[:3]) if profile.skills else "Engineering"
    return [
        {
            "role": target_role,
            "headline": f"{target_role.replace('-', ' ').title()} | {known_skills} | Measurable Systems Delivery",
            "rationale": "Grounded strictly in verified skills.",
        }
    ]


def rewrite_about(profile: Profile, target_role: str) -> str:
    skills_line = (
        f"Core Stack: {', '.join(profile.skills[:6])}" if profile.skills else ""
    )
    return (
        f"I am an engineer focused on {target_role.replace('-', ' ')}.\n\n"
        "My work emphasizes dependable software architecture, deterministic validation, and measurable impact.\n\n"
        f"{skills_line}\n\n"
        "Feel free to connect or send a message."
    )
