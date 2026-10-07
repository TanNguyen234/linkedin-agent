"""Persistent SQLite application tracker across all hiring stages."""

from __future__ import annotations

from typing import Any

from ...core.models import ApplicationStatus
from ...core.storage.database import LocalDatabase


class ApplicationTracker:
    def __init__(self, db: LocalDatabase):
        self.db = db
        self._init_schema()

    def _init_schema(self):
        with self.db.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    company TEXT NOT NULL,
                    role TEXT NOT NULL,
                    url TEXT,
                    status TEXT NOT NULL,
                    fit_score REAL DEFAULT 0.0,
                    date_discovered TEXT,
                    date_applied TEXT,
                    notes TEXT,
                    cover_note TEXT
                )
            """)

    def track_job(
        self,
        app_id: str,
        job_id: str,
        company: str,
        role: str,
        status: ApplicationStatus = ApplicationStatus.SAVED,
        fit_score: float = 0.0,
        notes: str = "",
    ):
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO applications (id, job_id, company, role, status, fit_score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (app_id, job_id, company, role, status.value, fit_score, notes),
            )

    def update_status(self, app_id: str, new_status: ApplicationStatus):
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE applications SET status = ? WHERE id = ?",
                (new_status.value, app_id),
            )

    def list_applications(
        self, status: ApplicationStatus | None = None
    ) -> list[dict[str, Any]]:
        with self.db.get_connection() as conn:
            if status:
                cur = conn.execute(
                    "SELECT * FROM applications WHERE status = ?", (status.value,)
                )
            else:
                cur = conn.execute("SELECT * FROM applications")
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
