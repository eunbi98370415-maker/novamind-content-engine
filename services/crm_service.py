"""
NovaMind CRM Service
Reads from mock_contacts.csv and provides contact management functionality.
"""

import io
import pandas as pd
from utils.config import DATA_DIR
from utils.helpers import get_persona_name


CONTACTS_CSV = DATA_DIR / "mock_contacts.csv"

LIFECYCLE_ORDER = ["subscriber", "lead", "MQL", "SQL", "customer"]


class CRMService:
    """Contact management and segmentation service."""

    def __init__(self):
        self._df: pd.DataFrame | None = None

    def _load(self) -> pd.DataFrame:
        """Load contacts CSV, caching in memory."""
        if self._df is None:
            self._df = pd.read_csv(CONTACTS_CSV, dtype=str).fillna("")
        return self._df.copy()

    # ── Public Methods ─────────────────────────────────────────────────────────

    def get_contacts(
        self,
        persona_filter: str = None,
        status_filter: list = None,
        lifecycle_filter: list = None,
        search: str = None,
    ) -> pd.DataFrame:
        """
        Return filtered contacts as a DataFrame.

        Args:
            persona_filter: persona id string or None for all
            status_filter: list of lead_status values, or None for all
            lifecycle_filter: list of lifecycle_stage values, or None for all
            search: text to match against first_name, last_name, company
        """
        df = self._load()

        if persona_filter and persona_filter != "All":
            df = df[df["persona"] == persona_filter]

        if status_filter:
            df = df[df["lead_status"].isin(status_filter)]

        if lifecycle_filter:
            df = df[df["lifecycle_stage"].isin(lifecycle_filter)]

        if search:
            search_lower = search.lower()
            mask = (
                df["first_name"].str.lower().str.contains(search_lower, na=False)
                | df["last_name"].str.lower().str.contains(search_lower, na=False)
                | df["company"].str.lower().str.contains(search_lower, na=False)
                | df["email"].str.lower().str.contains(search_lower, na=False)
            )
            df = df[mask]

        return df.reset_index(drop=True)

    def get_contact_stats(self) -> dict:
        """
        Return aggregate statistics about the contact database.

        Returns:
            dict with keys: total, by_persona (dict), by_lifecycle (dict),
                            by_lead_status (dict)
        """
        df = self._load()

        by_persona = df["persona"].value_counts().to_dict()
        by_lifecycle = df["lifecycle_stage"].value_counts().to_dict()
        by_lead_status = df["lead_status"].value_counts().to_dict()

        return {
            "total": len(df),
            "by_persona": by_persona,
            "by_lifecycle": by_lifecycle,
            "by_lead_status": by_lead_status,
        }

    def get_segment_for_newsletter(self, persona_id: str) -> pd.DataFrame:
        """Return all contacts for a given persona (newsletter segment)."""
        return self.get_contacts(persona_filter=persona_id)

    def export_contacts_csv(self, persona_filter: str = None) -> str:
        """
        Return filtered contacts as a CSV string for download.

        Args:
            persona_filter: persona id or None for all contacts
        """
        df = self.get_contacts(persona_filter=persona_filter)
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        return buffer.getvalue()

    def get_segment_summary(self) -> list:
        """
        Return a summary list with per-persona contact counts and lifecycle breakdown.

        Returns:
            list of dicts: [{persona_id, persona_name, count, lifecycle_breakdown}]
        """
        df = self._load()
        summary = []

        for persona_id in ["agency_owner", "startup_marketer", "solo_creator"]:
            seg = df[df["persona"] == persona_id]
            lifecycle_breakdown = {
                stage: int((seg["lifecycle_stage"] == stage).sum())
                for stage in LIFECYCLE_ORDER
            }
            summary.append({
                "persona_id": persona_id,
                "persona_name": get_persona_name(persona_id),
                "count": len(seg),
                "lifecycle_breakdown": lifecycle_breakdown,
            })

        return summary

    def get_display_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Return a display-friendly version of the contacts DataFrame
        with a full name column and sorted columns.
        """
        if df.empty:
            return df

        display_df = df.copy()
        display_df["Name"] = display_df["first_name"] + " " + display_df["last_name"]

        cols = ["Name", "email", "company", "job_title", "persona",
                "lifecycle_stage", "lead_status", "country", "last_engaged"]
        available = [c for c in cols if c in display_df.columns]
        return display_df[available].rename(columns={
            "email": "Email",
            "company": "Company",
            "job_title": "Job Title",
            "persona": "Persona",
            "lifecycle_stage": "Lifecycle Stage",
            "lead_status": "Lead Status",
            "country": "Country",
            "last_engaged": "Last Engaged",
        })
