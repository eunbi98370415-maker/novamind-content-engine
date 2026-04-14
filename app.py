"""
NovaMind — Weekly Content Engine
Main dashboard entry point.
Run with: streamlit run app.py
"""

import sys
import os

# Ensure project root is on sys.path so all imports work regardless of cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from datetime import datetime

from utils.config import APP_NAME, APP_VERSION, MOCK_MODE
from utils.helpers import format_date, truncate, get_persona_icon, get_persona_name
from db import database as db

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NovaMind — Content Engine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* ── Metric cards ── */
.metric-card {
    background: white;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.04);
    border: 1px solid #f1f5f9;
    height: 100%;
}
.metric-card .metric-label {
    font-size: 13px;
    font-weight: 500;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 8px;
}
.metric-card .metric-value {
    font-size: 32px;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.1;
}
.metric-card .metric-sub {
    font-size: 12px;
    color: #94a3b8;
    margin-top: 4px;
}

/* ── Persona badges ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
}
.badge-agency { background: #eef2ff; color: #6366f1; }
.badge-startup { background: #e0f2fe; color: #0284c7; }
.badge-creator { background: #dcfce7; color: #16a34a; }
.badge-success { background: #dcfce7; color: #16a34a; }
.badge-warning { background: #fef9c3; color: #a16207; }
.badge-info    { background: #e0f2fe; color: #0284c7; }
.badge-purple  { background: #eef2ff; color: #6366f1; }

/* ── Mode badge ── */
.mode-badge-live {
    background: #dcfce7; color: #15803d;
    padding: 4px 12px; border-radius: 20px;
    font-size: 12px; font-weight: 600;
    display: inline-block;
}
.mode-badge-mock {
    background: #fef9c3; color: #a16207;
    padding: 4px 12px; border-radius: 20px;
    font-size: 12px; font-weight: 600;
    display: inline-block;
}

/* ── Section headers ── */
.section-header {
    font-size: 18px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 4px;
}
.section-sub {
    font-size: 14px;
    color: #64748b;
    margin-bottom: 16px;
}

/* ── Campaign row ── */
.campaign-row {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 8px;
}

/* ── Insight card ── */
.insight-card {
    background: linear-gradient(135deg, #f8faff 0%, #f0f4ff 100%);
    border: 1px solid #e0e7ff;
    border-radius: 12px;
    padding: 20px;
    height: 100%;
}
.insight-card .insight-icon {
    font-size: 24px;
    margin-bottom: 8px;
}
.insight-card .insight-headline {
    font-size: 15px;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 6px;
}
.insight-card .insight-detail {
    font-size: 13px;
    color: #475569;
    line-height: 1.55;
}

/* ── Streamlit overrides ── */
div[data-testid="stSidebarContent"] {
    padding-top: 24px;
}
div[data-testid="metric-container"] {
    background: white;
    border: 1px solid #f1f5f9;
    border-radius: 10px;
    padding: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
</style>
""", unsafe_allow_html=True)

# ── Database Init ──────────────────────────────────────────────────────────────
db.init_db()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ NovaMind")
    st.markdown(f"*Weekly Content Engine* · v{APP_VERSION}")
    st.divider()

    if MOCK_MODE:
        st.markdown('<span class="mode-badge-mock">🟡 Mock Mode</span>', unsafe_allow_html=True)
        st.caption("No API key detected. Using realistic mock content.")
    else:
        st.markdown('<span class="mode-badge-live">🟢 Live API</span>', unsafe_allow_html=True)
        st.caption("Connected to live LLM provider.")

    st.divider()
    st.caption("Navigate using the pages above.")
    st.caption("© 2026 NovaMind")

# ── Main Content ───────────────────────────────────────────────────────────────

# Header
col_title, col_badge = st.columns([4, 1])
with col_title:
    st.markdown("# ⚡ NovaMind")
    st.markdown("**Weekly Content Engine** — Repurpose once, reach everyone.")
with col_badge:
    st.markdown("<br>", unsafe_allow_html=True)
    if MOCK_MODE:
        st.markdown('<span class="mode-badge-mock">🟡 Mock Mode</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="mode-badge-live">🟢 Live API</span>', unsafe_allow_html=True)

st.divider()

# ── Summary Metrics ────────────────────────────────────────────────────────────
campaigns = db.get_campaigns(limit=100)
total_campaigns = len(campaigns)
last_generated = campaigns[0]["created_at"] if campaigns else None

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Campaigns Generated</div>
        <div class="metric-value">{total_campaigns}</div>
        <div class="metric-sub">Total all time</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Active Personas</div>
        <div class="metric-value">3</div>
        <div class="metric-sub">Agency · Startup · Creator</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Avg Open Rate</div>
        <div class="metric-value">28.7%</div>
        <div class="metric-sub">+1.8% vs last period</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    last_gen_label = format_date(last_generated) if last_generated else "—"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Last Generated</div>
        <div class="metric-value" style="font-size:22px;">{last_gen_label}</div>
        <div class="metric-sub">Most recent campaign</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Quick Actions ──────────────────────────────────────────────────────────────
st.markdown('<p class="section-header">Quick Actions</p>', unsafe_allow_html=True)
qa_col1, qa_col2, qa_col3 = st.columns([2, 2, 4])
with qa_col1:
    if st.button("✨ Generate New Campaign →", type="primary", use_container_width=True):
        st.switch_page("pages/1_Content_Generator.py")
with qa_col2:
    if st.button("📊 View Analytics →", use_container_width=True):
        st.switch_page("pages/5_Analytics.py")

st.markdown("<br>", unsafe_allow_html=True)

# ── Recent Campaigns ────────────────────────────────────────────────────────────
st.markdown('<p class="section-header">Recent Campaigns</p>', unsafe_allow_html=True)

recent = db.get_campaigns(limit=5)

if not recent:
    st.markdown("""
    <div style="text-align:center; padding:60px 20px; background:#f8fafc; border-radius:12px; border:2px dashed #e2e8f0;">
        <div style="font-size:40px; margin-bottom:12px;">📭</div>
        <div style="font-size:18px; font-weight:600; color:#334155; margin-bottom:8px;">No campaigns yet</div>
        <div style="font-size:14px; color:#64748b;">Generate your first campaign to get started.</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("✨ Generate your first campaign →", type="primary"):
        st.switch_page("pages/1_Content_Generator.py")
else:
    # Header row
    hdr = st.columns([2, 4, 2, 1, 1])
    for col, label in zip(hdr, ["Date", "Topic", "Personas", "Status", "Action"]):
        col.markdown(f"**{label}**")
    st.divider()

    for campaign in recent:
        row = st.columns([2, 4, 2, 1, 1])
        with row[0]:
            st.caption(format_date(campaign.get("created_at", "")))
        with row[1]:
            st.write(truncate(campaign.get("topic", "Untitled"), 60))
        with row[2]:
            personas = campaign.get("personas", [])
            if isinstance(personas, list):
                icons = " ".join(get_persona_icon(p) for p in personas)
                st.write(icons)
            else:
                st.write("—")
        with row[3]:
            status = campaign.get("status", "draft")
            badge_class = "badge-success" if status == "published" else "badge-info"
            st.markdown(f'<span class="badge {badge_class}">{status}</span>', unsafe_allow_html=True)
        with row[4]:
            if st.button("View", key=f"view_{campaign['id']}"):
                st.session_state["view_campaign_id"] = campaign["id"]
                st.switch_page("pages/6_Export.py")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("View all campaigns →", use_container_width=False):
        st.switch_page("pages/6_Export.py")

# ── How It Works ───────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.divider()
st.markdown('<p class="section-header">How NovaMind Works</p>', unsafe_allow_html=True)
st.markdown('<p class="section-sub">From one topic to a full, segmented content campaign in minutes.</p>', unsafe_allow_html=True)

step_cols = st.columns(4)
steps = [
    ("1️⃣", "Enter a Topic", "Paste a blog post, paste a URL, or just describe your topic in one sentence."),
    ("2️⃣", "Select Personas", "Choose which audience segments should receive this week's campaign."),
    ("3️⃣", "Generate", "NovaMind writes the blog, 3 newsletters, subject lines, and a repurposing guide."),
    ("4️⃣", "Export & Send", "Download or copy the content, then send via your existing email platform."),
]
for col, (icon, title, desc) in zip(step_cols, steps):
    with col:
        st.markdown(f"""
        <div class="metric-card" style="text-align:center;">
            <div style="font-size:28px; margin-bottom:8px;">{icon}</div>
            <div style="font-weight:700; margin-bottom:6px; color:#0f172a;">{title}</div>
            <div style="font-size:13px; color:#64748b; line-height:1.5;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
