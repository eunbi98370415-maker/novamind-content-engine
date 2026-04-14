"""
NovaMind — Weekly Automation
Configure the scheduler, view status, and run jobs on-demand.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
from datetime import datetime

from utils.config import MOCK_MODE, DATA_DIR
from utils.helpers import format_date, get_persona_icon, get_persona_name
from db import database as db
from services.scheduler_service import SchedulerService, DAYS_OF_WEEK, DEFAULT_SETTINGS

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Weekly Automation — NovaMind",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.status-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #e2e8f0;
    margin-bottom: 12px;
}
.status-label { font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
.status-value { font-size: 22px; font-weight: 700; color: #0f172a; margin-top: 4px; }
.badge-on  { background:#dcfce7; color:#166534; padding:4px 12px; border-radius:20px; font-size:13px; font-weight:600; }
.badge-off { background:#f1f5f9; color:#64748b;  padding:4px 12px; border-radius:20px; font-size:13px; font-weight:600; }
.job-row {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.job-status-success { background:#dcfce7; color:#166534; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.job-status-failed  { background:#fee2e2; color:#991b1b; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.job-status-running { background:#fef9c3; color:#92400e; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.job-status-pending { background:#f1f5f9; color:#475569; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ── Init ───────────────────────────────────────────────────────────────────────
db.init_db()

with open(DATA_DIR / "sample_topics.json") as f:
    TOPICS_DATA = json.load(f)

TOPIC_CATEGORIES = [cat["category"] for cat in TOPICS_DATA]

@st.cache_resource
def get_scheduler():
    return SchedulerService()

scheduler = get_scheduler()

PERSONA_OPTIONS = {
    "agency_owner": "🏢 Creative Agency Owner",
    "startup_marketer": "🚀 Marketing Manager (Startup)",
    "solo_creator": "✏️ Freelancer / Solo Creator",
}

TIMES = [f"{h:02d}:{m:02d}" for h in range(6, 23) for m in (0,)]  # 06:00 to 22:00

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ NovaMind")
    st.divider()
    if MOCK_MODE:
        st.markdown("🟡 **Mock Mode**")
    else:
        st.markdown("🟢 **Live API**")
    st.divider()
    st.caption("Configure your weekly automation schedule. Enable it to auto-generate campaigns each week.")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("# 🗓️ Weekly Automation")
st.markdown("Configure automated weekly campaign generation. Set it once, let NovaMind run every Monday.")
st.divider()

# ── Load current settings ──────────────────────────────────────────────────────
current_settings = scheduler.get_settings()
scheduler_status = scheduler.get_status()

# ── Two-column layout ──────────────────────────────────────────────────────────
settings_col, status_col = st.columns([1, 1], gap="large")

# ─────────────────────────────────────────────────────────────────────────────
# LEFT: SETTINGS FORM
# ─────────────────────────────────────────────────────────────────────────────
with settings_col:
    st.markdown("### ⚙️ Automation Settings")

    with st.form("scheduler_form"):
        enabled = st.toggle(
            "Enable Weekly Generation",
            value=bool(current_settings.get("enabled", False)),
            help="When enabled, NovaMind will automatically generate a campaign on the scheduled day/time."
        )

        day = st.selectbox(
            "Generation Day",
            options=DAYS_OF_WEEK,
            index=DAYS_OF_WEEK.index(current_settings.get("day_of_week", "Monday")),
        )

        time_val = current_settings.get("time_of_day", "09:00")
        time_idx = TIMES.index(time_val) if time_val in TIMES else 3  # default 09:00
        time_of_day = st.selectbox(
            "Time of Day",
            options=TIMES,
            index=time_idx,
            format_func=lambda t: datetime.strptime(t, "%H:%M").strftime("%-I:%M %p"),
        )

        topic_cat = st.selectbox(
            "Default Topic Category",
            options=TOPIC_CATEGORIES,
            index=TOPIC_CATEGORIES.index(current_settings.get("topic_category", "AI & Automation"))
                  if current_settings.get("topic_category", "AI & Automation") in TOPIC_CATEGORIES else 0,
        )

        default_personas_val = current_settings.get("default_personas", list(PERSONA_OPTIONS.keys()))
        personas_sel = st.multiselect(
            "Default Personas",
            options=list(PERSONA_OPTIONS.keys()),
            default=[p for p in default_personas_val if p in PERSONA_OPTIONS],
            format_func=lambda x: PERSONA_OPTIONS[x],
        )

        tone_options = ["Professional", "Conversational", "Bold", "Empathetic"]
        tone_val = current_settings.get("default_tone", "Professional")
        tone_sel = st.selectbox(
            "Default Tone",
            options=tone_options,
            index=tone_options.index(tone_val) if tone_val in tone_options else 0,
        )

        cta_options = ["Free Trial", "Newsletter Signup", "Book a Demo", "Download Guide"]
        cta_val = current_settings.get("default_cta", "Free Trial")
        cta_sel = st.selectbox(
            "Default CTA",
            options=cta_options,
            index=cta_options.index(cta_val) if cta_val in cta_options else 0,
        )

        length_options = ["Short", "Medium", "Long"]
        length_val = current_settings.get("default_length", "Medium")
        length_sel = st.selectbox(
            "Default Content Length",
            options=length_options,
            index=length_options.index(length_val) if length_val in length_options else 1,
        )

        save_btn = st.form_submit_button("💾 Save Settings", type="primary", use_container_width=True)

    if save_btn:
        new_settings = {
            "enabled": enabled,
            "day_of_week": day,
            "time_of_day": time_of_day,
            "topic_category": topic_cat,
            "default_personas": personas_sel,
            "default_tone": tone_sel,
            "default_cta": cta_sel,
            "default_length": length_sel,
        }
        scheduler.save_settings(new_settings)
        st.success("✅ Settings saved successfully.")
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### ▶️ Run Now")
    st.markdown("Trigger a generation job immediately using the default settings above.")

    if st.button("▶️ Run Weekly Job Now", type="primary", use_container_width=True):
        st.session_state["confirm_run"] = True

    if st.session_state.get("confirm_run"):
        st.warning("⚠️ This will generate a full campaign using your default settings. Proceed?")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Yes, run it", use_container_width=True):
                with st.spinner("Running weekly job..."):
                    result = scheduler.run_weekly_job()
                st.session_state["confirm_run"] = False
                if result["status"] == "success":
                    st.success(f"✅ {result['message']}")
                    st.session_state["run_result"] = result
                else:
                    st.error(f"❌ {result['message']}")
                st.rerun()
        with c2:
            if st.button("✗ Cancel", use_container_width=True):
                st.session_state["confirm_run"] = False
                st.rerun()

    if st.session_state.get("run_result"):
        res = st.session_state["run_result"]
        st.success(f"Last job: Campaign #{res.get('campaign_id')} — {res.get('topic', '')[:50]}")
        if st.button("View in Export →"):
            st.session_state["view_campaign_id"] = res.get("campaign_id")
            st.switch_page("pages/6_Export.py")

# ─────────────────────────────────────────────────────────────────────────────
# RIGHT: STATUS + JOB HISTORY
# ─────────────────────────────────────────────────────────────────────────────
with status_col:
    st.markdown("### 📊 Scheduler Status")

    # Status cards
    is_enabled = scheduler_status.get("enabled", False)
    status_label = "Enabled" if is_enabled else "Disabled"
    status_badge = "badge-on" if is_enabled else "badge-off"

    st.markdown(f"""
    <div class="status-card">
        <div class="status-label">Status</div>
        <div style="margin-top:6px;">
            <span class="{status_badge}">{status_label}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    next_run = scheduler_status.get("next_run")
    next_run_str = "—"
    if next_run and is_enabled:
        if isinstance(next_run, datetime):
            next_run_str = next_run.strftime("%a, %b %-d at %-I:%M %p")
        else:
            next_run_str = str(next_run)

    st.markdown(f"""
    <div class="status-card">
        <div class="status-label">Next Scheduled Run</div>
        <div class="status-value">{next_run_str}</div>
    </div>
    """, unsafe_allow_html=True)

    last_run = scheduler_status.get("last_run")
    last_run_str = format_date(last_run) if last_run else "Never"

    st.markdown(f"""
    <div class="status-card">
        <div class="status-label">Last Run</div>
        <div class="status-value">{last_run_str}</div>
    </div>
    """, unsafe_allow_html=True)

    total_runs = scheduler_status.get("total_runs", 0)
    st.markdown(f"""
    <div class="status-card">
        <div class="status-label">Total Successful Runs</div>
        <div class="status-value">{total_runs}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Job History ────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 Job History")

    jobs = scheduler.get_job_history(limit=10)

    if not jobs:
        st.markdown("""
        <div style="text-align:center; padding:32px; background:#f8fafc;
                    border-radius:10px; border:2px dashed #e2e8f0; color:#94a3b8;">
            No jobs have run yet. Run your first job above.
        </div>
        """, unsafe_allow_html=True)
    else:
        # Table header
        hdr = st.columns([2, 1, 3, 2])
        for col, label in zip(hdr, ["Date/Time", "Status", "Topic", "Personas"]):
            col.markdown(f"**{label}**")
        st.divider()

        for job in jobs:
            row = st.columns([2, 1, 3, 2])
            status = job.get("status", "pending")
            run_at = format_date(job.get("run_at", ""))
            topic = job.get("topic") or "—"
            personas = job.get("personas", [])

            badge_cls = {
                "success": "job-status-success",
                "failed": "job-status-failed",
                "running": "job-status-running",
            }.get(status, "job-status-pending")

            with row[0]:
                st.caption(run_at)
            with row[1]:
                st.markdown(f'<span class="{badge_cls}">{status}</span>', unsafe_allow_html=True)
            with row[2]:
                st.caption(topic[:40] + ("..." if len(topic) > 40 else ""))
            with row[3]:
                icons = " ".join(get_persona_icon(p) for p in personas) if personas else "—"
                st.caption(icons)
