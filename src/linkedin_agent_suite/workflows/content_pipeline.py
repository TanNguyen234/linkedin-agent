"""Content pipeline workflow."""

from typing import Any

from ..intelligence.content.service import ContentService


def run_content_pipeline(
    service: ContentService, topic: str, facts: list
) -> dict[str, Any]:
    draft = service.generate_draft(topic, facts)
    preview = service.preview_draft(draft.id)
    return preview
