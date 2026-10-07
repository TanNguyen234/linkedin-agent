"""Unified Content Service."""
import datetime
from typing import Dict, Any, Optional
from src.core.storage.database import LocalDatabase
from src.core.models.models import PostDraft
from src.core.security.approvals import request_approval, consume_approval
from src.intelligence.content.post_generator import create_post_draft
from src.intelligence.content.publishing.official import OfficialLinkedInPublisher

class ContentService:
    def __init__(self, db: LocalDatabase, settings):
        self.db = db
        self.settings = settings

    def generate_draft(self, topic: str, context_facts: Optional[list] = None) -> PostDraft:
        facts = context_facts or []
        draft = create_post_draft(topic, facts)
        self.db.save_post_draft(draft.dict())
        return draft

    def preview_draft(self, draft_id: str) -> Dict[str, Any]:
        draft_dict = self.db.get_post_draft(draft_id)
        if not draft_dict:
            raise ValueError(f"Draft {draft_id} not found.")
        token = request_approval("publish_post", {"draft_id": draft_id, "text": draft_dict["body"]})
        return {
            "draft_id": draft_id,
            "topic": draft_dict["topic"],
            "hook": draft_dict["hook"],
            "body": draft_dict["body"],
            "approval_token": token,
            "status": "READY_FOR_APPROVAL"
        }

    def publish_draft(self, draft_id: str, approval_token: str) -> Dict[str, Any]:
        draft_dict = self.db.get_post_draft(draft_id)
        if not draft_dict:
            raise ValueError(f"Draft {draft_id} not found.")
        
        ok, msg = consume_approval(approval_token, "publish_post", {"draft_id": draft_id, "text": draft_dict["body"]})
        if not ok:
            return {"status": "BLOCKED", "message": msg}
        
        token = self.settings.linkedin_access_token or "mock_token"
        publisher = OfficialLinkedInPublisher(token)
        success, res = publisher.publish_text_post(draft_dict["body"])
        if success:
            draft_dict["status"] = "PUBLISHED"
            draft_dict["post_urn"] = res
            draft_dict["published_at"] = datetime.datetime.now().isoformat()
            self.db.save_post_draft(draft_dict)
            return {"status": "PUBLISHED", "post_urn": res}
        else:
            return {"status": "FAILED", "error": res}
