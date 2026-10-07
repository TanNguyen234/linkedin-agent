"""Hook generation and complete post builder."""

import datetime
import uuid

from ...core.models import PostDraft
from .humanizer import humanize_text
from .validator import validate_claims


def generate_hooks(topic: str) -> list[str]:
    return [
        f"Most architectures for {topic} fail due to brittle state management. Here is what worked:",
        f"We just deployed an update for {topic}. Three engineering lessons learned from production:",
        f"If you are designing {topic}, avoid this common failure mode before scaling:",
    ]


def create_post_draft(
    topic: str, context_facts: list[str], hook_index: int = 0
) -> PostDraft:
    hooks = generate_hooks(topic)
    selected_hook = hooks[min(hook_index, len(hooks) - 1)]

    body_core = (
        f"{selected_hook}\n\n"
        f"1. Keep contracts explicit rather than guessing schemas.\n"
        f"2. Decouple business logic from external adapter frameworks.\n"
        f"3. Verify with deterministic tests instead of relying on mocks alone.\n\n"
        f"What is your preferred pattern when dealing with this in production?\n\n"
        f"#SoftwareEngineering #SystemDesign"
    )

    clean_body = humanize_text(body_core)
    is_valid, warnings = validate_claims(clean_body)

    draft_id = f"post-{uuid.uuid4().hex[:8]}"
    return PostDraft(
        id=draft_id,
        source_type="manual",
        topic=topic,
        hook=selected_hook,
        body=clean_body,
        status="DRAFT" if is_valid else "VALIDATION_WARNING",
        evidence=context_facts,
        created_at=datetime.datetime.now().isoformat(),
    )
