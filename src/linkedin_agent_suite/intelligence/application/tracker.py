"""Persistent SQLite application tracker."""
import datetime
import uuid
from typing import List, Dict, Any, Optional
from ...core.models import ApplicationTrackerItem, ApplicationStatus
from ...core.storage.database import LocalDatabase

class ApplicationTracker:
    def __init__(self, db: LocalDatabase):
        self.db = db

    def add_application(self, job_id: str, company: str, title: str, url: str, fit_score: Optional[float] = None) -> ApplicationTrackerItem:
        app_id = f"app-{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now().isoformat()
        item = ApplicationTrackerItem(
            id=app_id,
            job_id=job_id,
            company=company,
            title=title,
            url=url,
            status=ApplicationStatus.SAVED,
            fit_score=fit_score,
            created_at=now,
            updated_at=now
        )
        self.db.save_application(item.model_dump())
        return item

    def list_applications(self) -> List[Dict[str, Any]]:
        return self.db.get_applications()
