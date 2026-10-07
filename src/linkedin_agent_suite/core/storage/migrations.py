"""Database migration runner with schema versioning."""
import sqlite3

LATEST_SCHEMA_VERSION = 2

MIGRATIONS = {
    1: """
        CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
        INSERT OR IGNORE INTO schema_version (version) VALUES (1);
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
        );
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
        );
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
        );
        CREATE TABLE IF NOT EXISTS profile_store (
            id TEXT PRIMARY KEY,
            data TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """,
    2: """
        ALTER TABLE post_drafts ADD COLUMN evidence TEXT DEFAULT '[]';
        CREATE TABLE IF NOT EXISTS content_calendar (
            id TEXT PRIMARY KEY,
            slot_day TEXT,
            theme TEXT,
            post_id TEXT,
            scheduled_time TEXT
        );
        UPDATE schema_version SET version = 2;
    """
}

def apply_migrations(db_path: str):
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);")
        row = conn.execute("SELECT version FROM schema_version LIMIT 1;").fetchone()
        current_version = row[0] if row else 0

        for ver in range(current_version + 1, LATEST_SCHEMA_VERSION + 1):
            if ver in MIGRATIONS:
                conn.executescript(MIGRATIONS[ver])
