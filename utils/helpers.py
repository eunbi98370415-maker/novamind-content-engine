"""
NovaMind Helpers
Utility functions used across the application.
"""

from datetime import datetime
from slugify import slugify as _slugify


def format_date(dt) -> str:
    """Format a datetime or date string to 'Apr 13, 2026'."""
    if dt is None:
        return "—"
    if isinstance(dt, str):
        # Try parsing common formats
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(dt, fmt)
                break
            except ValueError:
                continue
        else:
            return dt  # Return as-is if unparseable
    if isinstance(dt, datetime):
        return dt.strftime("%b %-d, %Y")
    return str(dt)


def truncate(text: str, max_len: int = 80) -> str:
    """Truncate text to max_len characters, adding ellipsis if needed."""
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[:max_len - 3].rstrip() + "..."


def word_count(text: str) -> int:
    """Count words in a string."""
    if not text:
        return 0
    return len(text.split())


def slugify_topic(topic: str) -> str:
    """Convert a topic string to a URL-safe slug."""
    return _slugify(topic, max_length=80, word_boundary=True)


def estimate_read_time(text: str) -> str:
    """Estimate reading time based on ~200 words per minute."""
    wc = word_count(text)
    minutes = max(1, round(wc / 200))
    return f"{minutes} min read"


def get_persona_color(persona_id: str) -> str:
    """Return the hex brand color for a given persona."""
    colors = {
        "agency_owner": "#6366f1",
        "startup_marketer": "#0ea5e9",
        "solo_creator": "#10b981",
    }
    return colors.get(persona_id, "#6b7280")


def get_persona_icon(persona_id: str) -> str:
    """Return the emoji icon for a given persona."""
    icons = {
        "agency_owner": "🏢",
        "startup_marketer": "🚀",
        "solo_creator": "✏️",
    }
    return icons.get(persona_id, "👤")


def get_persona_name(persona_id: str) -> str:
    """Return the display name for a given persona."""
    names = {
        "agency_owner": "Creative Agency Owner",
        "startup_marketer": "Marketing Manager (Startup)",
        "solo_creator": "Freelancer / Solo Creator",
    }
    return names.get(persona_id, persona_id.replace("_", " ").title())


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a float as a percentage string."""
    return f"{value:.{decimals}f}%"


def safe_json_loads(text: str, default=None):
    """Safely parse JSON, returning default on failure."""
    import json
    try:
        return json.loads(text)
    except Exception:
        return default if default is not None else {}
