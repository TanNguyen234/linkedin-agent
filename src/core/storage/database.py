"""Local SQLite database for applications, jobs, drafts, and profile."""
import sqlite3
import os
import json
from typing import List, Optional, Dict, Any

class LocalDatabase:
    def __init__(self, db_path: str = "data/suite.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    url TEXT,
                    description TEXT,
                    tags TEXT,
                    source TEXT,
                    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id TEXT PRIMARY KEY,
                    job_id TEXT,
                    company TEXT,
                    title TEXT,
                    status TEXT,
                    apply_url TEXT,
                    notes TEXT,
                    cover_note TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS post_drafts (
                    id TEXT PRIMARY KEY,
                    source_type TEXT,
                    topic TEXT,
                    hook TEXT,
                    body TEXT,
                    status TEXT,
                    scheduled_at TEXT,
                    published_at TEXT,
                    post_urn TEXT,
                    created_at TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS profile_store (
                    id TEXT PRIMARY KEY,
                    data TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def save_job(self, job: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO jobs (id, title, company, location, url, description, tags, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job["id"], job["title"], job["company"], job.get("location", ""),
                job["url"], job.get("description", ""), json.dumps(job.get("tags", [])), job.get("source", "linkedin")
            ))

    def get_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM jobs ORDER BY cached_at DESC LIMIT ?", (limit,)).fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["tags"] = json.loads(item["tags"]) if item["tags"] else []
                results.append(item)
            return results

    def save_application(self, app: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO applications (id, job_id, company, title, status, apply_url, notes, cover_note, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                app["id"], app["job_id"], app["company"], app["title"], app["status"],
                app["apply_url"], app.get("notes", ""), app.get("cover_note", ""),
                app["created_at"], app["updated_at"]
            ))

    def get_applications(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM applications ORDER BY updated_at DESC").fetchall()
            return [dict(r) for r in rows]

    def save_post_draft(self, draft: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO post_drafts (id, source_type, topic, hook, body, status, scheduled_at, published_at, post_urn, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                draft["id"], draft["source_type"], draft["topic"], draft["hook"], draft["body"],
                draft["status"], draft.get("scheduled_at"), draft.get("published_at"), draft.get("post_urn"), draft["created_at"]
            ))

    def get_post_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM post_drafts WHERE id = ?", (draft_id,)).fetchone()
            return dict(row) if row else None

    def get_post_drafts(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM post_drafts ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def save_profile_snapshot(self, profile_data: Dict[str, Any]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO profile_store (id, data) VALUES ('current', ?)", (json.dumps(profile_data),))

    def get_profile_snapshot(self) -> Optional[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT data FROM profile_store WHERE id = 'current'").fetchone()
            return json.loads(row[0]) if row else None
