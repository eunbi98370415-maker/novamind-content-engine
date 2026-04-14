"""
NovaMind Scheduler Service
Manages weekly automation settings, job history, and on-demand generation.
"""

import json
from datetime import datetime, timedelta
from db import database as db
from utils.helpers import get_persona_name


DEFAULT_SETTINGS = {
    "enabled": False,
    "day_of_week": "Monday",
    "time_of_day": "09:00",
    "default_personas": ["agency_owner", "startup_marketer", "solo_creator"],
    "default_tone": "Professional",
    "default_cta": "Free Trial",
    "default_length": "Medium",
    "topic_category": "AI & Automation",
}

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_TO_INT = {d: i for i, d in enumerate(DAYS_OF_WEEK)}  # Monday=0


class SchedulerService:
    """Manages automation scheduling and job execution."""

    # ── Settings ───────────────────────────────────────────────────────────────

    def get_settings(self) -> dict:
        """Load scheduler settings from DB, filling in defaults."""
        settings = {}
        for key, default_val in DEFAULT_SETTINGS.items():
            val = db.get_setting(f"scheduler_{key}", default_val)
            # Coerce booleans stored as strings back to bool
            if isinstance(default_val, bool):
                if isinstance(val, str):
                    val = val.lower() in ("true", "1", "yes")
                else:
                    val = bool(val)
            settings[key] = val
        return settings

    def save_settings(self, settings: dict):
        """Persist scheduler settings to DB."""
        for key, value in settings.items():
            db.save_setting(f"scheduler_{key}", value)

    # ── Scheduling Logic ───────────────────────────────────────────────────────

    def get_next_run_date(self) -> datetime:
        """
        Calculate the next scheduled run datetime based on stored settings.
        Returns the next occurrence of the configured day+time.
        """
        settings = self.get_settings()
        day_name = settings.get("day_of_week", "Monday")
        time_str = settings.get("time_of_day", "09:00")

        target_weekday = DAY_TO_INT.get(day_name, 0)
        hour, minute = map(int, time_str.split(":"))

        now = datetime.now()
        days_ahead = (target_weekday - now.weekday()) % 7

        # If today is the target day but the time has already passed, schedule for next week
        if days_ahead == 0:
            scheduled_today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if now >= scheduled_today:
                days_ahead = 7

        next_run = (now + timedelta(days=days_ahead)).replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )
        return next_run

    # ── Job History ────────────────────────────────────────────────────────────

    def get_job_history(self, limit: int = 10) -> list:
        """Return recent weekly job log entries with enriched fields."""
        jobs = db.get_weekly_jobs(limit=limit)
        enriched = []
        for job in jobs:
            enriched_job = dict(job)
            # Attach campaign topic if available
            if job.get("campaign_id"):
                campaign = db.get_campaign(job["campaign_id"])
                if campaign:
                    enriched_job["topic"] = campaign.get("topic", "")
                    enriched_job["personas"] = campaign.get("personas", [])
                else:
                    enriched_job["topic"] = "—"
                    enriched_job["personas"] = []
            else:
                enriched_job["topic"] = "—"
                enriched_job["personas"] = []
            enriched.append(enriched_job)
        return enriched

    # ── On-Demand Job Execution ───────────────────────────────────────────────

    def run_weekly_job(self, topic: str = None) -> dict:
        """
        Execute a weekly generation job immediately.
        Uses default settings from DB (or falls back to DEFAULT_SETTINGS).

        Args:
            topic: optional topic override; if None, picks from default category

        Returns:
            dict with keys: campaign_id, topic, status, message
        """
        # Log job start
        job_id = db.log_weekly_job("running")

        try:
            settings = self.get_settings()

            # Resolve topic
            if not topic:
                topic = self._pick_default_topic(settings.get("topic_category", "AI & Automation"))

            # Import here to avoid circular dependencies at module level
            from services.content_service import ContentService
            from utils.config import DATA_DIR
            import json as _json

            # Load persona data
            personas_path = DATA_DIR / "personas.json"
            with open(personas_path) as f:
                all_personas = _json.load(f)

            persona_ids = settings.get("default_personas", DEFAULT_SETTINGS["default_personas"])

            svc = ContentService()
            campaign = svc.generate_campaign(
                topic=topic,
                angle="",
                tone=settings.get("default_tone", "Professional"),
                cta_type=settings.get("default_cta", "Free Trial"),
                length=settings.get("default_length", "Medium"),
                persona_ids=persona_ids,
                personas_data=all_personas,
            )

            campaign_id = db.save_campaign(campaign)

            # Update job log with success + campaign_id
            conn = self._update_job_status(job_id, "success", campaign_id)

            return {
                "campaign_id": campaign_id,
                "topic": topic,
                "status": "success",
                "message": f"Campaign #{campaign_id} generated successfully.",
            }

        except Exception as e:
            self._update_job_status(job_id, "failed")
            return {
                "campaign_id": None,
                "topic": topic or "—",
                "status": "failed",
                "message": f"Job failed: {str(e)}",
            }

    def _pick_default_topic(self, category: str) -> str:
        """Pick the first topic from the given category in sample_topics.json."""
        from utils.config import DATA_DIR
        import json as _json

        topics_path = DATA_DIR / "sample_topics.json"
        with open(topics_path) as f:
            data = _json.load(f)

        for cat in data:
            if cat["category"] == category and cat["topics"]:
                return cat["topics"][0]

        # Fallback
        return "From One Blog to 100 Personalized Campaigns: AI-Driven Content Repurposing for Small Teams"

    def _update_job_status(self, job_id: int, status: str, campaign_id: int = None):
        """Update an existing weekly_jobs row."""
        import sqlite3
        from utils.config import DB_PATH

        conn = sqlite3.connect(str(DB_PATH))
        if campaign_id is not None:
            conn.execute(
                "UPDATE weekly_jobs SET status = ?, campaign_id = ? WHERE id = ?",
                (status, campaign_id, job_id),
            )
        else:
            conn.execute(
                "UPDATE weekly_jobs SET status = ? WHERE id = ?",
                (status, job_id),
            )
        conn.commit()
        conn.close()

    # ── Status ────────────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        """
        Return a status summary for the scheduler.

        Returns:
            dict with keys: enabled, next_run, last_run, total_runs
        """
        settings = self.get_settings()
        jobs = db.get_weekly_jobs(limit=100)
        successful_jobs = [j for j in jobs if j.get("status") == "success"]

        last_run = None
        if successful_jobs:
            last_run = successful_jobs[0].get("run_at")

        next_run = None
        if settings.get("enabled"):
            next_run = self.get_next_run_date()

        return {
            "enabled": settings.get("enabled", False),
            "next_run": next_run,
            "last_run": last_run,
            "total_runs": len(successful_jobs),
        }
