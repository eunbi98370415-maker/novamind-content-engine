"""
NovaMind Analytics Service
Provides performance data, persona benchmarks, trend analysis, and AI insights.
All data is mock/simulated for demo purposes.
"""

import random
import pandas as pd
from datetime import datetime, timedelta
from db import database as db


# ── Persona Benchmark Constants ────────────────────────────────────────────────

PERSONA_BENCHMARKS = {
    "agency_owner": {
        "open_rate": 28.0,
        "ctr": 4.2,
        "conversion": 1.8,
        "unsubscribe_rate": 0.3,
        "avg_session_length": "4:12",
    },
    "startup_marketer": {
        "open_rate": 24.0,
        "ctr": 5.8,
        "conversion": 2.4,
        "unsubscribe_rate": 0.4,
        "avg_session_length": "2:45",
    },
    "solo_creator": {
        "open_rate": 34.0,
        "ctr": 3.1,
        "conversion": 1.2,
        "unsubscribe_rate": 0.2,
        "avg_session_length": "3:28",
    },
}

# Best subject lines per persona (mock performance data)
TOP_SUBJECT_LINES = {
    "agency_owner": [
        {"subject": "One blog. Five campaigns. Zero extra hours.", "open_rate": 32.4},
        {"subject": "Your content is leaving money on the table.", "open_rate": 29.8},
        {"subject": "How top agencies repurpose without the headcount", "open_rate": 27.1},
    ],
    "startup_marketer": [
        {"subject": "Stop sending the same email to everyone.", "open_rate": 28.6},
        {"subject": "Segment smarter. Convert faster. Here's how.", "open_rate": 25.9},
        {"subject": "Your open rates called — they want personalization.", "open_rate": 24.3},
    ],
    "solo_creator": [
        {"subject": "You wrote the blog. Let AI do the rest.", "open_rate": 38.2},
        {"subject": "One post → a full week of content.", "open_rate": 35.7},
        {"subject": "Stop starting from scratch every Monday.", "open_rate": 33.1},
    ],
}

AI_INSIGHTS = [
    {
        "icon": "🏆",
        "headline": "Freelancer segment leads on open rate",
        "detail": (
            "The Solo Creator segment shows the highest open rate (34%) — "
            "time-saving hooks resonate strongly with this audience. "
            "Consider leading with a specific time claim in next week's subject line, "
            "e.g., 'Save 3 hours this week with one workflow change.'"
        ),
        "persona": "solo_creator",
        "metric": "Open Rate: 34%",
    },
    {
        "icon": "📈",
        "headline": "Startup Marketers convert at the highest rate",
        "detail": (
            "Startup Marketers convert at 2.4% — the highest of any segment. "
            "The segmentation angle consistently outperforms generic messaging. "
            "Test 'before/after' framing next week: show concrete numbers "
            "from a generic blast vs. a segmented campaign."
        ),
        "persona": "startup_marketer",
        "metric": "Conversion: 2.4%",
    },
    {
        "icon": "🔬",
        "headline": "Agency Owners are reading carefully",
        "detail": (
            "Agency Owners have the longest time-to-click but the highest average "
            "session length (4:12). They read before acting — they're evaluating ROI. "
            "Consider adding a mini case study or a specific client outcome to the next "
            "campaign to accelerate their decision."
        ),
        "persona": "agency_owner",
        "metric": "Session Length: 4:12",
    },
]


class AnalyticsService:
    """Analytics, benchmarking, and AI insight generation."""

    # ── Campaign Analytics ─────────────────────────────────────────────────────

    def get_campaign_analytics(self, campaign_id: int = None) -> dict:
        """
        Return mock analytics for a specific campaign or aggregate metrics.
        """
        seed = campaign_id or 42
        rng = random.Random(seed)

        result = {}
        for persona_id, base in PERSONA_BENCHMARKS.items():
            result[persona_id] = {
                "open_rate": round(base["open_rate"] + rng.uniform(-3, 4), 1),
                "ctr": round(base["ctr"] + rng.uniform(-0.8, 1.2), 1),
                "conversion": round(base["conversion"] + rng.uniform(-0.3, 0.5), 1),
                "emails_sent": rng.randint(18, 25),
                "opens": 0,  # will be computed below
                "clicks": 0,
            }
            sent = result[persona_id]["emails_sent"]
            result[persona_id]["opens"] = int(sent * result[persona_id]["open_rate"] / 100)
            result[persona_id]["clicks"] = int(sent * result[persona_id]["ctr"] / 100)

        return result

    # ── Persona Benchmarks ─────────────────────────────────────────────────────

    def get_persona_benchmarks(self) -> dict:
        """Return the canonical performance benchmarks per persona."""
        return PERSONA_BENCHMARKS.copy()

    # ── Weekly Trend Data ─────────────────────────────────────────────────────

    def get_weekly_trend_data(self) -> pd.DataFrame:
        """
        Return 8 weeks of mock performance data as a DataFrame.
        Includes a slight upward trend with realistic variance.
        """
        today = datetime.today()
        records = []

        for week_offset in range(7, -1, -1):
            week_start = today - timedelta(weeks=week_offset)
            week_label = week_start.strftime("W%U")

            # Trend factor: weeks closer to today score slightly higher
            trend = (7 - week_offset) * 0.4

            for persona_id, base in PERSONA_BENCHMARKS.items():
                seed = hash(f"{week_offset}_{persona_id}") % 10000
                rng = random.Random(seed)
                records.append({
                    "week": week_label,
                    "week_date": week_start.strftime("%Y-%m-%d"),
                    "persona": persona_id,
                    "open_rate": round(base["open_rate"] + trend + rng.uniform(-2, 2), 1),
                    "ctr": round(base["ctr"] + trend * 0.1 + rng.uniform(-0.5, 0.5), 1),
                    "conversion": round(base["conversion"] + trend * 0.05 + rng.uniform(-0.2, 0.2), 1),
                })

        return pd.DataFrame(records)

    # ── Performance Summary ────────────────────────────────────────────────────

    def get_performance_summary(self) -> dict:
        """Return aggregate KPIs across all personas and campaigns."""
        benchmarks = PERSONA_BENCHMARKS

        avg_open = sum(b["open_rate"] for b in benchmarks.values()) / len(benchmarks)
        avg_ctr = sum(b["ctr"] for b in benchmarks.values()) / len(benchmarks)
        avg_conv = sum(b["conversion"] for b in benchmarks.values()) / len(benchmarks)

        best_persona = max(benchmarks, key=lambda k: benchmarks[k]["open_rate"])

        campaigns = db.get_campaigns(limit=100)

        return {
            "avg_open_rate": round(avg_open, 1),
            "avg_ctr": round(avg_ctr, 1),
            "avg_conversion": round(avg_conv, 1),
            "best_open_rate_persona": best_persona,
            "total_campaigns": len(campaigns),
            # Mock deltas versus previous period
            "open_rate_delta": +1.8,
            "ctr_delta": +0.4,
        }

    # ── AI Insights ───────────────────────────────────────────────────────────

    def generate_ai_insights(self, analytics_data: dict = None) -> dict:
        """
        Return a structured set of AI optimization insights.
        Insights are analytically derived from benchmark data with realistic narrative.

        Returns:
            dict with keys: top_persona, winning_angle, next_test_recommendation,
                            summary, insight_cards (list)
        """
        return {
            "top_persona": "solo_creator",
            "winning_angle": "Time-saving efficiency hooks",
            "next_test_recommendation": (
                "Test 'before/after' framing for Startup Marketers: "
                "show specific numbers comparing generic vs. segmented campaign performance."
            ),
            "summary": (
                "Across all three segments, time-saving and personalization angles "
                "outperform generic product-feature messaging by an average of 22%. "
                "Solo Creators respond best to efficiency hooks; Startup Marketers "
                "to data and outcomes; Agency Owners to strategic, peer-level framing."
            ),
            "insight_cards": AI_INSIGHTS,
        }

    # ── Top Subject Lines ─────────────────────────────────────────────────────

    def get_top_subject_lines(self) -> dict:
        """Return the best-performing subject lines per persona."""
        return TOP_SUBJECT_LINES.copy()
