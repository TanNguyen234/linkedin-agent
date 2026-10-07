"""Hook generation and complete post builder."""
import uuid
import datetime
from typing import Dict, Any, List
from src.core.models.models import PostDraft
from src.intelligence.content.humanizer import humanize_text
from src.intelligence.content.validator import validate_claims

def generate_hooks(topic: str) -> List[str]:
    return [
        f"Most approaches to {topic} fail because of fragile state management. Here is what actually worked:",
        f"We just deployed an end-to-end update for {topic}. Three engineering lessons learned the hard way:",
        f"If you're building with {topic}, avoid this common architecture trap before scaling:"
    ]

def create_post_draft(topic: str, context_facts: List[str], hook_index: int = 0) -> PostDraft:
    hooks = generate_hooks(topic)
    selected_hook = hooks[min(hook_index, len(hooks) - 1)]
    
    body_core = (
        f"{selected_hook}\n\n"
        f"1. Keep contracts explicit rather than guessing schemas.\n"
        f"2. Decouple your business logic from adapter frameworks.\n"
        f"3. Verify with deterministic tests instead of relying on mocks alone.\n\n"
        f"What is your preferred pattern when dealing with this in production?\n\n"
        f"#SoftwareEngineering #SystemDesign"
    )
    
    clean_body = humanize_text(body_core)
    is_valid, warnings = validate_claims(clean_body, context_facts)
    
    draft_id = f"post-{uuid.uuid4().hex[:8]}"
    return PostDraft(
        id=draft_id,
        source_type="manual",
        topic=topic,
        hook=selected_hook,
        body=clean_body,
        status="DRAFT",
        created_at=datetime.datetime.now().isoformat()
    )
