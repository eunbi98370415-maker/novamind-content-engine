"""
NovaMind — Content Generator
Full campaign generation: blog post + personalized newsletters + subject lines +
repurposing notes + performance predictions.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st

from utils.config import MOCK_MODE, DATA_DIR
from utils.helpers import (
    format_date, get_persona_icon, get_persona_name, get_persona_color,
    estimate_read_time, word_count, truncate
)
from db import database as db
from services.content_service import ContentService

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Content Generator — NovaMind",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.output-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.subject-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #6366f1;
    border-radius: 6px;
    padding: 12px 16px;
    font-weight: 600;
    color: #1e293b;
    font-size: 15px;
    margin-bottom: 8px;
}
.preview-box {
    background: #f1f5f9;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 13px;
    color: #475569;
    margin-bottom: 12px;
}
.cta-mock {
    display: inline-block;
    background: #6366f1;
    color: white;
    padding: 10px 24px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 14px;
    margin-top: 12px;
}
.persona-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
}
.metric-pill {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: center;
}
.metric-pill .pill-val {
    font-size: 22px;
    font-weight: 700;
    color: #0f172a;
}
.metric-pill .pill-label {
    font-size: 12px;
    color: #64748b;
    margin-top: 2px;
}
.success-banner {
    background: #dcfce7;
    border: 1px solid #bbf7d0;
    border-radius: 10px;
    padding: 14px 18px;
    color: #166534;
    font-weight: 600;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

# ── Init ───────────────────────────────────────────────────────────────────────
db.init_db()

# Load personas
with open(DATA_DIR / "personas.json") as f:
    PERSONAS = json.load(f)

with open(DATA_DIR / "sample_topics.json") as f:
    TOPICS_DATA = json.load(f)

PERSONA_MAP = {p["id"]: p for p in PERSONAS}

# Cached service instance
@st.cache_resource
def get_content_service():
    return ContentService()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ NovaMind")
    st.divider()
    if MOCK_MODE:
        st.markdown("🟡 **Mock Mode** — Demo content")
    else:
        st.markdown("🟢 **Live API** — Real generation")
    st.divider()
    st.caption("Fill in the form and click **Generate Campaign** to create a full content package.")

# ── Page Header ────────────────────────────────────────────────────────────────
st.markdown("# ✨ Content Generator")
st.markdown("Turn one topic into a complete, personalized campaign for every audience segment.")
st.divider()

# ── Two-Column Layout ──────────────────────────────────────────────────────────
form_col, output_col = st.columns([1, 2], gap="large")

# ─────────────────────────────────────────────────────────────────────────────
# LEFT: INPUT FORM
# ─────────────────────────────────────────────────────────────────────────────
with form_col:
    st.markdown("### Campaign Settings")

    # Topic input with example prefill
    default_topic = "From One Blog to 100 Personalized Campaigns: AI-Driven Content Repurposing for Small Teams"
    topic = st.text_input(
        "Topic / Blog Title",
        value=default_topic,
        placeholder="e.g. How AI is changing content marketing for small teams",
        help="Enter a topic, a blog title, or paste the first paragraph of your post."
    )

    angle = st.text_input(
        "Angle / Objective (optional)",
        placeholder="e.g. Focus on time-saving benefits for busy agency owners",
        help="Give the AI a specific angle or objective to focus on."
    )

    st.markdown("**Select Personas**")
    persona_options = {p["id"]: f"{p['icon']} {p['name']}" for p in PERSONAS}
    selected_persona_ids = st.multiselect(
        "Personas",
        options=list(persona_options.keys()),
        default=list(persona_options.keys()),
        format_func=lambda x: persona_options[x],
        label_visibility="collapsed",
    )

    tone = st.selectbox(
        "Tone",
        options=["Professional", "Conversational", "Bold", "Empathetic"],
        index=0,
        help="Sets the writing style for the blog and all newsletters."
    )

    cta_type = st.selectbox(
        "CTA Type",
        options=["Free Trial", "Newsletter Signup", "Book a Demo", "Download Guide"],
        index=0,
    )

    length = st.radio(
        "Content Length",
        options=["Short (400–600w)", "Medium (800–1000w)", "Long (1200–1500w)"],
        index=1,
        horizontal=False,
    )
    length_key = length.split(" ")[0]  # "Short", "Medium", or "Long"

    st.markdown("<br>", unsafe_allow_html=True)

    generate_clicked = st.button(
        "✨ Generate Campaign",
        type="primary",
        use_container_width=True,
        disabled=not topic or not selected_persona_ids,
    )

    if not topic:
        st.caption("⚠️ Please enter a topic to generate.")
    elif not selected_persona_ids:
        st.caption("⚠️ Select at least one persona.")

# ─────────────────────────────────────────────────────────────────────────────
# RIGHT: OUTPUT AREA
# ─────────────────────────────────────────────────────────────────────────────
with output_col:

    # ── Generate on button click ───────────────────────────────────────────────
    if generate_clicked and topic and selected_persona_ids:
        with st.spinner("✨ Generating your campaign... this may take a moment."):
            try:
                svc = get_content_service()
                campaign = svc.generate_campaign(
                    topic=topic,
                    angle=angle,
                    tone=tone,
                    cta_type=cta_type,
                    length=length_key,
                    persona_ids=selected_persona_ids,
                    personas_data=PERSONAS,
                )
                campaign_id = db.save_campaign(campaign)
                st.session_state["last_campaign"] = campaign
                st.session_state["last_campaign_id"] = campaign_id
                st.session_state["generation_success"] = True
            except Exception as e:
                st.error(f"Generation failed: {str(e)}")
                st.session_state["generation_success"] = False

    # ── Display results ────────────────────────────────────────────────────────
    if st.session_state.get("generation_success") and st.session_state.get("last_campaign"):
        campaign = st.session_state["last_campaign"]
        campaign_id = st.session_state.get("last_campaign_id", "—")

        st.markdown(f"""
        <div class="success-banner">
            ✅ Campaign #{campaign_id} generated and saved successfully!
        </div>
        """, unsafe_allow_html=True)

        blog = campaign.get("blog_content", {})
        newsletters = campaign.get("newsletters", {})
        subject_lines_map = campaign.get("subject_lines", {})
        repurposing = campaign.get("repurposing_notes", "")
        personas_used = selected_persona_ids if selected_persona_ids else campaign.get("personas", [])

        tab_blog, tab_newsletters, tab_subjects, tab_repurpose, tab_predictions = st.tabs([
            "📝 Blog Post",
            "📧 Newsletters",
            "💡 Subject Lines",
            "🔁 Repurposing",
            "📊 Predictions",
        ])

        # ── Blog Post Tab ──────────────────────────────────────────────────────
        with tab_blog:
            title = blog.get("title", "Generated Blog Post")
            meta = blog.get("meta_description", "")
            body = blog.get("body", "")
            read_time = blog.get("read_time") or estimate_read_time(body)
            wc = blog.get("word_count") or word_count(body)

            st.markdown(f"## {title}")

            pill_cols = st.columns(3)
            with pill_cols[0]:
                st.markdown(f'<div class="metric-pill"><div class="pill-val">{wc}</div><div class="pill-label">Words</div></div>', unsafe_allow_html=True)
            with pill_cols[1]:
                st.markdown(f'<div class="metric-pill"><div class="pill-val">{read_time}</div><div class="pill-label">Read Time</div></div>', unsafe_allow_html=True)
            with pill_cols[2]:
                st.markdown(f'<div class="metric-pill"><div class="pill-val">{tone}</div><div class="pill-label">Tone</div></div>', unsafe_allow_html=True)

            if meta:
                st.markdown(f"**Meta description:** *{meta}*")
            st.markdown("---")
            st.markdown(body)

            if blog.get("cta"):
                st.markdown(f'<div class="cta-mock">{blog["cta"]}</div>', unsafe_allow_html=True)

        # ── Newsletters Tab ────────────────────────────────────────────────────
        with tab_newsletters:
            if not newsletters:
                st.info("No newsletters were generated.")
            else:
                for pid in personas_used:
                    nl = newsletters.get(pid)
                    if not nl:
                        continue
                    persona = PERSONA_MAP.get(pid, {})
                    icon = persona.get("icon", "👤")
                    name = persona.get("name", pid)
                    color = persona.get("color", "#6366f1")

                    with st.expander(f"{icon} {name} Newsletter", expanded=(pid == personas_used[0])):
                        st.markdown(f'<div class="subject-box">📩 {nl.get("subject_line", "")}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="preview-box">👁 Preview: {nl.get("preview_text", "")}</div>', unsafe_allow_html=True)
                        st.markdown("**Email Body:**")
                        st.markdown(nl.get("body", "").replace("\n", "\n\n"))
                        cta_text = nl.get("cta_text", "")
                        if cta_text:
                            st.markdown(f'<div><a style="display:inline-block;background:{color};color:white;padding:10px 20px;border-radius:8px;font-weight:600;font-size:14px;text-decoration:none;">{cta_text}</a></div>', unsafe_allow_html=True)

        # ── Subject Lines Tab ──────────────────────────────────────────────────
        with tab_subjects:
            st.markdown("**3 A/B-test ready subject lines per persona.** Copy the one that fits your send.")
            for pid in personas_used:
                lines = subject_lines_map.get(pid, [])
                if not lines:
                    continue
                persona = PERSONA_MAP.get(pid, {})
                icon = persona.get("icon", "👤")
                name = persona.get("name", pid)
                color = persona.get("color", "#6366f1")

                st.markdown(f"##### {icon} {name}")
                for i, line in enumerate(lines, 1):
                    cols = st.columns([8, 1])
                    with cols[0]:
                        st.code(line, language=None)
                    with cols[1]:
                        st.markdown(f"**{50 - len(line)}c left**" if len(line) < 50 else "✅", unsafe_allow_html=True)
                st.markdown("")

        # ── Repurposing Tab ────────────────────────────────────────────────────
        with tab_repurpose:
            if repurposing:
                st.markdown(repurposing)
            else:
                st.info("Repurposing notes not available.")

        # ── Predictions Tab ────────────────────────────────────────────────────
        with tab_predictions:
            st.markdown("**Predicted Performance** — Based on historical benchmarks for each persona.")
            st.markdown("")

            BENCHMARKS = {
                "agency_owner":   {"open_rate": 28.0, "ctr": 4.2, "conversion": 1.8},
                "startup_marketer": {"open_rate": 24.0, "ctr": 5.8, "conversion": 2.4},
                "solo_creator":   {"open_rate": 34.0, "ctr": 3.1, "conversion": 1.2},
            }

            pred_cols = st.columns(len(personas_used) or 1)
            for col, pid in zip(pred_cols, personas_used):
                persona = PERSONA_MAP.get(pid, {})
                benchmarks = BENCHMARKS.get(pid, {})
                with col:
                    st.markdown(f"**{persona.get('icon', '')} {persona.get('name', pid)}**")
                    st.metric("Est. Open Rate", f"{benchmarks.get('open_rate', 0)}%")
                    st.metric("Est. CTR", f"{benchmarks.get('ctr', 0)}%")
                    st.metric("Est. Conversion", f"{benchmarks.get('conversion', 0)}%")

    else:
        # Empty state — no campaign generated yet
        st.markdown("""
        <div style="text-align:center; padding:80px 20px; background:#f8fafc;
                    border-radius:16px; border:2px dashed #e2e8f0;">
            <div style="font-size:48px; margin-bottom:16px;">✨</div>
            <div style="font-size:20px; font-weight:700; color:#1e293b; margin-bottom:8px;">
                Ready to generate your campaign
            </div>
            <div style="font-size:14px; color:#64748b; max-width:360px; margin:0 auto;">
                Configure your settings on the left and click
                <strong>Generate Campaign</strong> to produce a full blog post,
                personalized newsletters, and repurposing guide.
            </div>
        </div>
        """, unsafe_allow_html=True)
