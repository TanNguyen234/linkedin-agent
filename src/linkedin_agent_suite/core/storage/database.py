"""Local SQLite database implementation."""

import json
import os
import sqlite3
from typing import Any

from .migrations import apply_migrations


class LocalDatabase:
    def __init__(self, db_path: str = "data/suite.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        apply_migrations(self.db_path)

    def get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def save_job(self, job: dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO jobs (id, title, company, location, url, description, tags, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    job["id"],
                    job["title"],
                    job["company"],
                    job.get("location", ""),
                    job["url"],
                    job.get("description", ""),
                    json.dumps(job.get("tags", [])),
                    job.get("source", "linkedin"),
                ),
            )

    def get_jobs(self, limit: int = 50) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY cached_at DESC LIMIT ?", (limit,)
            ).fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["tags"] = json.loads(item["tags"]) if item["tags"] else []
                results.append(item)
            return results

    def save_application(self, app: dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO applications (id, job_id, company, title, status, apply_url, notes, cover_note, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    app["id"],
                    app["job_id"],
                    app["company"],
                    app["title"],
                    str(app["status"]),
                    app.get("url", app.get("apply_url", "")),
                    app.get("notes", ""),
                    app.get("cover_note", ""),
                    app["created_at"],
                    app["updated_at"],
                ),
            )

    def get_applications(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM applications ORDER BY updated_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def save_post_draft(self, draft: dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO post_drafts (id, source_type, topic, hook, body, status, scheduled_at, published_at, post_urn, evidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    draft["id"],
                    draft.get("source_type", "manual"),
                    draft["topic"],
                    draft["hook"],
                    draft["body"],
                    draft["status"],
                    draft.get("scheduled_at"),
                    draft.get("published_at"),
                    draft.get("post_urn"),
                    json.dumps(draft.get("evidence", [])),
                    draft["created_at"],
                ),
            )

    def get_post_draft(self, draft_id: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM post_drafts WHERE id = ?", (draft_id,)
            ).fetchone()
            if not row:
                return None
            res = dict(row)
            res["evidence"] = json.loads(res["evidence"]) if res.get("evidence") else []
            return res

    def get_post_drafts(self) -> list[dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM post_drafts ORDER BY created_at DESC"
            ).fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["evidence"] = (
                    json.loads(item["evidence"]) if item.get("evidence") else []
                )
                results.append(item)
            return results

    def save_profile_snapshot(self, profile_data: dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO profile_store (id, data) VALUES ('current', ?)",
                (json.dumps(profile_data),),
            )

    def get_profile_snapshot(self) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT data FROM profile_store WHERE id = 'current'"
            ).fetchone()
            return json.loads(row[0]) if row else None
