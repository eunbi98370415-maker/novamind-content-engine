"""
NovaMind — Persona Library
Browse all three audience personas with full profile details.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st

from utils.config import MOCK_MODE, DATA_DIR
from db import database as db

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Persona Library — NovaMind",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.persona-card {
    background: white;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    border: 1px solid #e2e8f0;
    height: 100%;
}
.persona-icon-bg {
    width: 56px; height: 56px;
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 26px;
    margin-bottom: 12px;
}
.persona-name {
    font-size: 18px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 4px;
}
.persona-tagline {
    font-size: 13px;
    font-weight: 500;
    color: #64748b;
    margin-bottom: 16px;
}
.pill {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    margin: 2px 2px 2px 0;
}
.section-label {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #94a3b8;
    margin-bottom: 8px;
    margin-top: 16px;
}
.goal-item {
    font-size: 13px;
    color: #374151;
    padding: 4px 0;
    border-bottom: 1px solid #f1f5f9;
}
.pain-item {
    font-size: 13px;
    color: #374151;
    padding: 4px 0;
    border-bottom: 1px solid #fef2f2;
}
.messaging-box {
    background: #f8fafc;
    border-left: 4px solid;
    border-radius: 0 8px 8px 0;
    padding: 12px 14px;
    font-size: 13px;
    color: #1e293b;
    line-height: 1.5;
    margin-top: 8px;
}
.tone-badge {
    display: inline-block;
    background: #f1f5f9;
    color: #475569;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
}
.hook-chip {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    margin: 3px 3px 3px 0;
}
</style>
""", unsafe_allow_html=True)

# ── Init ───────────────────────────────────────────────────────────────────────
db.init_db()

with open(DATA_DIR / "personas.json") as f:
    PERSONAS = json.load(f)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ NovaMind")
    st.divider()
    if MOCK_MODE:
        st.markdown("🟡 **Mock Mode**")
    else:
        st.markdown("🟢 **Live API**")
    st.divider()
    st.caption("Personas define how NovaMind personalizes content for each audience segment.")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("# 🎯 Persona Library")
st.markdown("Three distinct audience segments, each with tailored messaging, tone, and content strategy.")
st.divider()

# ── Persona Cards ──────────────────────────────────────────────────────────────
cols = st.columns(3, gap="medium")

for col, persona in zip(cols, PERSONAS):
    color = persona.get("color", "#6366f1")
    # Light background version of the color
    light_bg = {
        "#6366f1": "#eef2ff",
        "#0ea5e9": "#e0f2fe",
        "#10b981": "#dcfce7",
    }.get(color, "#f8fafc")

    with col:
        # Icon background
        st.markdown(f"""
        <div class="persona-card">
            <div class="persona-icon-bg" style="background:{light_bg};">{persona['icon']}</div>
            <div class="persona-name">{persona['name']}</div>
            <div class="persona-tagline">"{persona['tagline']}"</div>
        """, unsafe_allow_html=True)

        # Demographic pills
        demo = persona.get("demographics", {})
        st.markdown(f"""
            <div>
                <span class="pill" style="background:{light_bg}; color:{color};">{demo.get('company_size', '')}</span>
                <span class="pill" style="background:{light_bg}; color:{color};">{demo.get('role', '')}</span>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"<div class='section-label'>Goals</div>", unsafe_allow_html=True)
        goals_html = "".join(f"<div class='goal-item'>✅ {g}</div>" for g in persona.get("goals", []))
        st.markdown(goals_html, unsafe_allow_html=True)

        st.markdown(f"<div class='section-label'>Pain Points</div>", unsafe_allow_html=True)
        pain_html = "".join(f"<div class='pain-item'>⚠️ {p}</div>" for p in persona.get("pain_points", []))
        st.markdown(pain_html, unsafe_allow_html=True)

        st.markdown(f"<div class='section-label'>Messaging Angle</div>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class="messaging-box" style="border-left-color:{color};">
                {persona.get('messaging_angle', '')}
            </div>
        """, unsafe_allow_html=True)

        st.markdown(f"<div class='section-label'>CTA Style</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:13px; color:#475569; line-height:1.5;'>{persona.get('cta_style', '')}</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='section-label'>Preferred Tone</div>", unsafe_allow_html=True)
        st.markdown(f"<span class='tone-badge'>{persona.get('preferred_tone', '')}</span>", unsafe_allow_html=True)

        st.markdown(f"<div class='section-label'>Content Hooks</div>", unsafe_allow_html=True)
        hooks_html = "".join(
            f"<span class='hook-chip' style='background:{light_bg}; color:{color};'>💡 {h}</span>"
            for h in persona.get("content_hooks", [])
        )
        st.markdown(hooks_html, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# ── How Personas Are Used ──────────────────────────────────────────────────────
st.markdown("<br><br>", unsafe_allow_html=True)
st.divider()
st.markdown("### How Personas Are Used in NovaMind")

exp_col1, exp_col2 = st.columns(2, gap="large")
with exp_col1:
    st.markdown("""
    **Content Personalization**

    When you generate a campaign, NovaMind creates a separate newsletter variant for each
    selected persona. Each variant uses that persona's preferred tone, leads with their
    specific pain points, and ends with a CTA style that matches how they make decisions.

    A blog post about *AI content automation* becomes:
    - An ROI-focused agency email ("Zero extra hours.")
    - A metrics-driven startup email ("Boost your CTR by 22%.")
    - A casual, time-saving creator email ("Let AI do the rest.")
    """)

with exp_col2:
    st.markdown("""
    **Segmentation & CRM**

    Every contact in your CRM is tagged with a persona ID. When you export newsletters,
    the right variant goes to the right segment — automatically. No manual list management,
    no copy-pasting into different campaigns.

    **Subject Line Optimization**

    Subject lines are generated specifically for each persona's vocabulary and psychological
    triggers. Agency owners respond to efficiency and ROI language. Startup marketers respond
    to data. Solo creators respond to empathy and time-saving framing.
    """)

st.markdown("")
st.info("💡 Personas are defined in `data/personas.json`. You can extend or modify them to match your real audience segments.")
