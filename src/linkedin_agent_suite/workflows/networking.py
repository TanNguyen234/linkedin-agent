"""Networking workflow: find target -> inspect -> draft outreach."""
from typing import Tuple
from ..core.models import Profile
from ..core.security import approvals

def prepare_networking_outreach(target_name: str, target_role: str, target_company: str, my_profile: Profile) -> Tuple[str, str]:
    note = (
        f"Hi {target_name},\n\n"
        f"I saw your work at {target_company} and wanted to connect. "
        f"I specialize in {my_profile.skills[0] if my_profile.skills else 'software engineering'} "
        f"and enjoy keeping up with {target_role} updates.\n\n"
        f"Best,\n{my_profile.full_name or 'Peer'}"
    )
    payload = {"target_name": target_name, "company": target_company, "note": note}
    token = approvals.request_approval("networking_outreach", payload)
    return note, token
