"""
NovaMind — CRM Contacts
Contact management, segmentation view, and CSV exports.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd

from utils.config import MOCK_MODE
from utils.helpers import get_persona_icon, get_persona_name, get_persona_color
from db import database as db
from services.crm_service import CRMService

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CRM Contacts — NovaMind",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stat-card {
    background: white;
    border-radius: 12px;
    padding: 18px 20px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.stat-label { font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
.stat-value { font-size: 28px; font-weight: 700; color: #0f172a; margin-top: 4px; }

.seg-card {
    background: white;
    border-radius: 12px;
    padding: 16px 20px;
    border: 1px solid #e2e8f0;
}
.seg-name { font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 4px; }
.seg-count { font-size: 26px; font-weight: 800; margin-bottom: 12px; }

.lifecycle-bar-container { margin-bottom: 4px; }
.lifecycle-row { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; }
.lifecycle-label { font-size: 11px; color: #64748b; width: 70px; flex-shrink: 0; }
.lifecycle-bar { height: 8px; border-radius: 4px; }

.badge { display: inline-block; padding: 2px 8px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.badge-agency   { background:#eef2ff; color:#6366f1; }
.badge-startup  { background:#e0f2fe; color:#0284c7; }
.badge-creator  { background:#dcfce7; color:#16a34a; }

.export-card {
    background: white;
    border-radius: 12px;
    padding: 18px 20px;
    border: 1px solid #e2e8f0;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ── Init ───────────────────────────────────────────────────────────────────────
db.init_db()

@st.cache_resource
def get_crm():
    return CRMService()

crm = get_crm()

LIFECYCLE_STAGES = ["subscriber", "lead", "MQL", "SQL", "customer"]
LEAD_STATUSES = ["new", "contacted", "qualified", "nurturing", "converted"]
PERSONA_OPTIONS = {"All": "All Personas", "agency_owner": "🏢 Agency Owner", "startup_marketer": "🚀 Startup Marketer", "solo_creator": "✏️ Solo Creator"}
LIFECYCLE_COLORS = {
    "subscriber": "#94a3b8",
    "lead": "#60a5fa",
    "MQL": "#818cf8",
    "SQL": "#f59e0b",
    "customer": "#10b981",
}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ NovaMind")
    st.divider()
    if MOCK_MODE:
        st.markdown("🟡 **Mock Mode**")
    else:
        st.markdown("🟢 **Live API**")
    st.divider()
    st.caption("63 contacts across 3 persona segments. Filter and export for your email platform.")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("# 👥 CRM Contacts")
st.markdown("View, filter, and export your segmented contact list. Each persona maps to a personalized newsletter.")
st.divider()

# ── Stats Row ─────────────────────────────────────────────────────────────────
stats = crm.get_contact_stats()
seg_summary = crm.get_segment_summary()

stat_cols = st.columns(3)
with stat_cols[0]:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Total Contacts</div>
        <div class="stat-value">{stats['total']}</div>
    </div>
    """, unsafe_allow_html=True)
with stat_cols[1]:
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Segments Active</div>
        <div class="stat-value">3</div>
    </div>
    """, unsafe_allow_html=True)
with stat_cols[2]:
    # Most common lifecycle
    by_lc = stats.get("by_lifecycle", {})
    top_stage = max(by_lc, key=by_lc.get) if by_lc else "—"
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-label">Top Lifecycle Stage</div>
        <div class="stat-value" style="font-size:20px;">{top_stage.upper()}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Filter Bar ─────────────────────────────────────────────────────────────────
st.markdown("### 🔍 Filter Contacts")
filter_cols = st.columns([2, 2, 2, 3])
with filter_cols[0]:
    persona_filter = st.selectbox("Persona", options=list(PERSONA_OPTIONS.keys()), format_func=lambda x: PERSONA_OPTIONS[x])
with filter_cols[1]:
    lifecycle_filter = st.multiselect("Lifecycle Stage", options=LIFECYCLE_STAGES, default=[])
with filter_cols[2]:
    status_filter = st.multiselect("Lead Status", options=LEAD_STATUSES, default=[])
with filter_cols[3]:
    search = st.text_input("Search", placeholder="Name, company, or email...")

filtered_df = crm.get_contacts(
    persona_filter=persona_filter if persona_filter != "All" else None,
    lifecycle_filter=lifecycle_filter if lifecycle_filter else None,
    status_filter=status_filter if status_filter else None,
    search=search if search else None,
)

st.markdown(f"**{len(filtered_df)} contacts** match your filters.")
st.markdown("<br>", unsafe_allow_html=True)

# ── Segment Summary Cards ──────────────────────────────────────────────────────
st.markdown("### 📊 Segment Overview")
seg_cols = st.columns(3)

for col, seg in zip(seg_cols, seg_summary):
    pid = seg["persona_id"]
    color = get_persona_color(pid)
    icon = get_persona_icon(pid)
    lc_breakdown = seg.get("lifecycle_breakdown", {})
    total_seg = seg["count"]

    # Build lifecycle bars
    bars_html = ""
    for stage in LIFECYCLE_STAGES:
        count = lc_breakdown.get(stage, 0)
        pct = (count / total_seg * 100) if total_seg > 0 else 0
        bar_color = LIFECYCLE_COLORS.get(stage, "#94a3b8")
        bars_html += f"""
        <div class="lifecycle-row">
            <span class="lifecycle-label">{stage}</span>
            <div style="flex:1; background:#f1f5f9; border-radius:4px; height:8px;">
                <div style="width:{pct:.0f}%; background:{bar_color}; height:8px; border-radius:4px;"></div>
            </div>
            <span style="font-size:11px; color:#64748b; width:20px; text-align:right;">{count}</span>
        </div>"""

    with col:
        st.markdown(f"""
        <div class="seg-card">
            <div class="seg-name">{icon} {seg['persona_name']}</div>
            <div class="seg-count" style="color:{color};">{total_seg}</div>
            <div>{bars_html}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Contacts Table ─────────────────────────────────────────────────────────────
st.markdown("### 📋 Contacts")

def make_persona_badge(persona_id: str) -> str:
    badge_map = {
        "agency_owner": "badge-agency",
        "startup_marketer": "badge-startup",
        "solo_creator": "badge-creator",
    }
    icon = get_persona_icon(persona_id)
    label = persona_id.replace("_", " ").title()
    cls = badge_map.get(persona_id, "")
    return f'<span class="badge {cls}">{icon} {label}</span>'

# Build display DataFrame
if not filtered_df.empty:
    display_df = filtered_df.copy()
    display_df["Name"] = display_df["first_name"] + " " + display_df["last_name"]
    display_cols = {
        "Name": "Name",
        "email": "Email",
        "company": "Company",
        "job_title": "Job Title",
        "persona": "Persona",
        "lifecycle_stage": "Lifecycle",
        "lead_status": "Status",
        "country": "Country",
        "last_engaged": "Last Engaged",
    }
    show_df = display_df[[c for c in display_cols if c in display_df.columns]].rename(columns=display_cols)

    st.dataframe(
        show_df,
        use_container_width=True,
        height=420,
        column_config={
            "Persona": st.column_config.TextColumn("Persona"),
            "Lifecycle": st.column_config.TextColumn("Lifecycle"),
            "Email": st.column_config.TextColumn("Email"),
        }
    )
else:
    st.info("No contacts match your current filters.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Newsletter Assignment ───────────────────────────────────────────────────────
st.markdown("### 📧 Newsletter Assignment by Segment")
st.markdown("Contacts who will receive each persona's newsletter this week:")

for seg in seg_summary:
    pid = seg["persona_id"]
    icon = get_persona_icon(pid)
    name = seg["persona_name"]
    seg_df = crm.get_segment_for_newsletter(pid)
    count = len(seg_df)

    with st.expander(f"{icon} {name} — {count} recipients"):
        if seg_df.empty:
            st.info("No contacts in this segment.")
        else:
            preview = seg_df[["first_name", "last_name", "email", "company", "lifecycle_stage"]].head(5)
            preview["Name"] = preview["first_name"] + " " + preview["last_name"]
            st.dataframe(
                preview[["Name", "email", "company", "lifecycle_stage"]],
                use_container_width=True,
                hide_index=True,
            )
            if count > 5:
                st.caption(f"...and {count - 5} more contacts.")

st.markdown("<br>", unsafe_allow_html=True)

# ── Export Section ─────────────────────────────────────────────────────────────
st.markdown("### 📥 Export Contacts")

exp_col1, exp_col2, exp_col3, exp_col4 = st.columns(4)

with exp_col1:
    st.markdown("""
    <div class="export-card">
        <div style="font-size:24px; margin-bottom:8px;">📄</div>
        <div style="font-weight:600; margin-bottom:4px;">All Contacts</div>
        <div style="font-size:12px; color:#64748b; margin-bottom:12px;">All 63 contacts, CSV</div>
    </div>
    """, unsafe_allow_html=True)
    all_csv = crm.export_contacts_csv()
    st.download_button(
        "⬇ Download All",
        data=all_csv,
        file_name="novamind_all_contacts.csv",
        mime="text/csv",
        use_container_width=True,
    )

export_personas = [
    ("agency_owner", "🏢 Agency Owners", "21 contacts"),
    ("startup_marketer", "🚀 Startup Marketers", "21 contacts"),
    ("solo_creator", "✏️ Solo Creators", "21 contacts"),
]
for col, (pid, label, note) in zip([exp_col2, exp_col3, exp_col4], export_personas):
    with col:
        st.markdown(f"""
        <div class="export-card">
            <div style="font-size:24px; margin-bottom:8px;">{get_persona_icon(pid)}</div>
            <div style="font-weight:600; margin-bottom:4px;">{label}</div>
            <div style="font-size:12px; color:#64748b; margin-bottom:12px;">{note}, CSV</div>
        </div>
        """, unsafe_allow_html=True)
        csv_data = crm.export_contacts_csv(persona_filter=pid)
        st.download_button(
            f"⬇ Download",
            data=csv_data,
            file_name=f"novamind_{pid}_contacts.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"export_{pid}",
        )
