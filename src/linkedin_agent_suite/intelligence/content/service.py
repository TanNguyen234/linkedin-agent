"""Unified Content Service."""
from __future__ import annotations

from typing import Any

from ...core.models import PostDraft, PublishResult
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

        # Duplicate publishing check
        if draft_dict.get("status") == "PUBLISHED" and draft_dict.get("post_urn"):
            return {
                "status": "BLOCKED",
                "message": f"Draft {draft_id} was already published ({draft_dict['post_urn']}). Duplicate publish prevented.",
                "post_urn": draft_dict["post_urn"],
            }

        payload = {"draft_id": draft_id, "text": draft_dict["body"]}
        ok, msg = approvals.consume_approval(approval_token, "publish_post", payload)
        if not ok:
            return {"status": "BLOCKED", "message": msg}

        try:
            publisher = OfficialLinkedInPublisher(
                settings=self.settings,
                access_token=self.settings.linkedin_access_token,
                enable_posting=self.settings.enable_official_posting,
                api_version=self.settings.linkedin_api_version,
            )
            result: PublishResult = publisher.publish_text_post(draft_dict["body"])
            if result.status == "PUBLISHED":
                draft_dict["status"] = "PUBLISHED"
                draft_dict["post_urn"] = result.post_urn
                draft_dict["published_at"] = result.published_at
                self.db.save_post_draft(draft_dict)
                return {"status": "PUBLISHED", "post_urn": result.post_urn}
            elif result.status == "UNCONFIRMED":
                draft_dict["status"] = "UNCONFIRMED"
                self.db.save_post_draft(draft_dict)
                return {
                    "status": "UNCONFIRMED",
                    "error_code": result.error_code,
                    "message": result.error_message,
                }
            else:
                return {
                    "status": result.status,
                    "error_code": result.error_code,
                    "error": result.error_message,
                }
        except Exception as e:
            return {"status": "BLOCKED", "error": str(e)}
