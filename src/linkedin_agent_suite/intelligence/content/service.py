"""Unified Content Service."""

import datetime
from typing import Any

from ...core.models import PostDraft
from ...core.security import approvals
from ...core.storage.database import LocalDatabase
from .post_generator import create_post_draft
from .publishing.official import OfficialLinkedInPublisher


class ContentService:
    def __init__(self, db: LocalDatabase, settings):
        self.db = db
        self.settings = settings

    def generate_draft(
        self, topic: str, context_facts: list | None = None
    ) -> PostDraft:
        facts = context_facts or []
        draft = create_post_draft(topic, facts)
        self.db.save_post_draft(draft.model_dump())
        return draft

    def preview_draft(self, draft_id: str) -> dict[str, Any]:
        draft_dict = self.db.get_post_draft(draft_id)
        if not draft_dict:
            raise ValueError(f"Draft {draft_id} not found.")
        payload = {"draft_id": draft_id, "text": draft_dict["body"]}
        token = approvals.request_approval("publish_post", payload)
        return {
            "draft_id": draft_id,
            "topic": draft_dict["topic"],
            "hook": draft_dict["hook"],
            "body": draft_dict["body"],
            "approval_token": token,
            "status": "READY_FOR_APPROVAL",
        }

    def publish_draft(self, draft_id: str, approval_token: str) -> dict[str, Any]:
        draft_dict = self.db.get_post_draft(draft_id)
        if not draft_dict:
            raise ValueError(f"Draft {draft_id} not found.")

        payload = {"draft_id": draft_id, "text": draft_dict["body"]}
        ok, msg = approvals.consume_approval(approval_token, "publish_post", payload)
        if not ok:
            return {"status": "BLOCKED", "message": msg}

        try:
            publisher = OfficialLinkedInPublisher(
                access_token=self.settings.linkedin_access_token,
                enable_posting=self.settings.enable_official_posting,
                api_version=self.settings.linkedin_api_version,
            )
            success, res = publisher.publish_text_post(draft_dict["body"])
            if success:
                draft_dict["status"] = "PUBLISHED"
                draft_dict["post_urn"] = res
                draft_dict["published_at"] = datetime.datetime.now().isoformat()
                self.db.save_post_draft(draft_dict)
                return {"status": "PUBLISHED", "post_urn": res}
            return {"status": "FAILED", "error": res}
        except Exception as e:
            return {"status": "BLOCKED", "error": str(e)}
