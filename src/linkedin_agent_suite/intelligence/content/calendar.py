"""SQLite-backed content calendar & scheduler with recovery."""

from __future__ import annotations

import time
from typing import Any

from ...core.storage.database import LocalDatabase


class ContentCalendar:
    def __init__(self, db: LocalDatabase):
        self.db = db
        self._init_schema()

    def _init_schema(self):
        with self.db.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_posts (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    scheduled_epoch INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                )
            """)

    def schedule_post(self, post_id: str, content: str, epoch_time: int):
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO scheduled_posts (id, content, scheduled_epoch, status, created_at)
                VALUES (?, ?, ?, 'SCHEDULED', ?)
            """,
                (post_id, content, epoch_time, int(time.time())),
            )

    def get_due_posts(self) -> list[dict[str, Any]]:
        now = int(time.time())
        with self.db.get_connection() as conn:
            cur = conn.execute(
                "SELECT * FROM scheduled_posts WHERE status = 'SCHEDULED' AND scheduled_epoch <= ?",
                (now,),
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

    def mark_published(self, post_id: str):
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE scheduled_posts SET status = 'PUBLISHED' WHERE id = ?",
                (post_id,),
            )
