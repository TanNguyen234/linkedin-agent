"""Profile optimizer workflow."""

from typing import Any

from ..core.models import Profile
from ..intelligence.profile.audit import audit_profile
from ..intelligence.profile.generator import generate_headlines, rewrite_about


def run_profile_optimizer(
    profile: Profile, target_role: str = "agentic-ai-systems-engineer"
) -> dict[str, Any]:
    audit = audit_profile(profile, target_role)
    headlines = generate_headlines(profile, target_role)
    about = rewrite_about(profile, target_role)
    return {"audit": audit, "suggested_headlines": headlines, "suggested_about": about}
