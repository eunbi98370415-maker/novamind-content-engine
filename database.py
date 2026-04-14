"""
NovaMind Database Layer
SQLite-backed persistence for campaigns, settings, and job history.
Uses Python's built-in sqlite3 — no external dependencies.
"""

import sqlite3
import json
from datetime import datetime
from utils.config import DB_PATH


def _get_connection():
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


def init_db():
    """Create all tables if they do not already exist."""
    conn = _get_connection()
    cursor = conn.cursor()

    # ── Campaigns ─────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            topic            TEXT    NOT NULL,
            angle            TEXT,
            tone             TEXT,
            cta_type         TEXT,
            length_preference TEXT,
            personas         TEXT,   -- JSON list of persona ids
            blog_content     TEXT,   -- JSON dict {title, body, ...}
            newsletters      TEXT,   -- JSON dict keyed by persona_id
            repurposing_notes TEXT,
            subject_lines    TEXT,   -- JSON dict keyed by persona_id
            created_at       TEXT    NOT NULL DEFAULT (datetime('now')),
            status           TEXT    NOT NULL DEFAULT 'draft'
        )
    """)

    # ── Settings ───────────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key        TEXT PRIMARY KEY,
            value      TEXT,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── Weekly Job Logs ────────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_jobs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at      TEXT    NOT NULL DEFAULT (datetime('now')),
            status      TEXT    NOT NULL DEFAULT 'pending',
            campaign_id INTEGER,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()


# ── Campaign CRUD ──────────────────────────────────────────────────────────────

def save_campaign(campaign_dict: dict) -> int:
    """Insert a campaign record and return the new row ID."""
    conn = _get_connection()
    cursor = conn.cursor()

    # Serialise nested objects to JSON strings
    def to_json(val):
        if val is None:
            return None
        if isinstance(val, (dict, list)):
            return json.dumps(val)
        return val

    cursor.execute("""
        INSERT INTO campaigns
            (topic, angle, tone, cta_type, length_preference, personas,
             blog_content, newsletters, repurposing_notes, subject_lines, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        campaign_dict.get("topic", ""),
        campaign_dict.get("angle", ""),
        campaign_dict.get("tone", ""),
        campaign_dict.get("cta_type", ""),
        campaign_dict.get("length_preference", ""),
        to_json(campaign_dict.get("personas", [])),
        to_json(campaign_dict.get("blog_content", {})),
        to_json(campaign_dict.get("newsletters", {})),
        campaign_dict.get("repurposing_notes", ""),
        to_json(campaign_dict.get("subject_lines", {})),
        campaign_dict.get("status", "draft"),
    ))

    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def _row_to_dict(row) -> dict:
    """Convert a sqlite3.Row to a plain dict, parsing JSON fields."""
    d = dict(row)
    for field in ("personas", "blog_content", "newsletters", "subject_lines"):
        if d.get(field):
            try:
                d[field] = json.loads(d[field])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


def get_campaigns(limit: int = 20) -> list:
    """Return the most recent campaigns as a list of dicts."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM campaigns ORDER BY created_at DESC LIMIT ?", (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_campaign(campaign_id: int) -> dict | None:
    """Return a single campaign dict by ID, or None if not found."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
    row = cursor.fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def update_campaign_status(campaign_id: int, status: str):
    """Update the status field of a campaign."""
    conn = _get_connection()
    conn.execute(
        "UPDATE campaigns SET status = ? WHERE id = ?", (status, campaign_id)
    )
    conn.commit()
    conn.close()


# ── Settings ──────────────────────────────────────────────────────────────────

def get_setting(key: str, default=None):
    """Return the value for a settings key, or default if not found."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return default
    value = row["value"]
    # Try JSON decode for structured values
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


def save_setting(key: str, value):
    """Upsert a setting key/value pair."""
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    elif not isinstance(value, str):
        value = str(value)

    conn = _get_connection()
    conn.execute("""
        INSERT INTO settings (key, value, updated_at)
        VALUES (?, ?, datetime('now'))
        ON CONFLICT(key) DO UPDATE SET
            value      = excluded.value,
            updated_at = excluded.updated_at
    """, (key, value))
    conn.commit()
    conn.close()


# ── Weekly Job Logs ────────────────────────────────────────────────────────────

def get_weekly_jobs(limit: int = 10) -> list:
    """Return the most recent weekly job log entries."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM weekly_jobs ORDER BY run_at DESC LIMIT ?", (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def log_weekly_job(status: str, campaign_id: int = None) -> int:
    """Insert a weekly job log entry and return its ID."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO weekly_jobs (run_at, status, campaign_id)
        VALUES (datetime('now'), ?, ?)
    """, (status, campaign_id))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id
