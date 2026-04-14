"""
NovaMind — Export & Deliverables
Download all campaign assets: blog post, newsletters, CRM contacts, and full JSON.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
from datetime import datetime

from utils.config import MOCK_MODE
from utils.helpers import format_date, truncate, get_persona_icon, get_persona_name, word_count
from db import database as db
from services.crm_service import CRMService

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Export — NovaMind",
    page_icon="📥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.export-card {
    background: white;
    border-radius: 12px;
    padding: 22px 24px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    height: 100%;
}
.export-card-title {
    font-size: 16px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 4px;
}
.export-card-desc {
    font-size: 13px;
    color: #64748b;
    margin-bottom: 14px;
    line-height: 1.5;
}
.format-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 10px;
}
.format-md  { background: #e0e7ff; color: #4338ca; }
.format-csv { background: #dcfce7; color: #166534; }
.format-json { background: #fef9c3; color: #92400e; }
.size-hint { font-size: 12px; color: #94a3b8; margin-bottom: 12px; }
.preview-frame {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 14px;
    font-size: 12px;
    color: #475569;
    max-height: 160px;
    overflow: hidden;
    line-height: 1.55;
    white-space: pre-wrap;
    font-family: 'Menlo', monospace;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ── Init ───────────────────────────────────────────────────────────────────────
db.init_db()

@st.cache_resource
def get_crm():
    return CRMService()

crm = get_crm()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ NovaMind")
    st.divider()
    if MOCK_MODE:
        st.markdown("🟡 **Mock Mode**")
    else:
        st.markdown("🟢 **Live API**")
    st.divider()
    st.caption("Export any campaign as Markdown, CSV, or JSON. All files are ready to use in your email platform.")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("# 📥 Export & Deliverables")
st.markdown("Download blog posts, newsletters, CRM contacts, and full campaign data.")
st.divider()

# ── Campaign Selector ──────────────────────────────────────────────────────────
campaigns = db.get_campaigns(limit=30)

if not campaigns:
    st.markdown("""
    <div style="text-align:center; padding:80px 20px; background:#f8fafc;
                border-radius:16px; border:2px dashed #e2e8f0;">
        <div style="font-size:40px; margin-bottom:12px;">📭</div>
        <div style="font-size:18px; font-weight:600; color:#334155; margin-bottom:8px;">No campaigns found</div>
        <div style="font-size:14px; color:#64748b;">Generate your first campaign to unlock exports.</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("✨ Generate a campaign →", type="primary"):
        st.switch_page("pages/1_Content_Generator.py")
    st.stop()

# Build selector options
campaign_options = {
    c["id"]: f"#{c['id']} — {truncate(c['topic'], 60)} ({format_date(c['created_at'])})"
    for c in campaigns
}

# Check if a campaign was pre-selected (e.g., from dashboard View button)
preselect_id = st.session_state.get("view_campaign_id")
default_idx = 0
if preselect_id and preselect_id in campaign_options:
    ids = list(campaign_options.keys())
    default_idx = ids.index(preselect_id)

selected_id = st.selectbox(
    "Select Campaign",
    options=list(campaign_options.keys()),
    index=default_idx,
    format_func=lambda x: campaign_options[x],
)

campaign = db.get_campaign(selected_id)

if not campaign:
    st.error("Campaign not found.")
    st.stop()

# ── Campaign Info Banner ───────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:14px 18px; margin-bottom:20px;">
    <strong>Campaign #{campaign['id']}</strong> — {campaign.get('topic', 'Untitled')}
    <span style="float:right; color:#64748b; font-size:13px;">{format_date(campaign.get('created_at'))}</span>
</div>
""", unsafe_allow_html=True)

# ── Unpack campaign data ───────────────────────────────────────────────────────
blog = campaign.get("blog_content") or {}
newsletters = campaign.get("newsletters") or {}
subject_lines = campaign.get("subject_lines") or {}
repurposing = campaign.get("repurposing_notes") or ""
personas = campaign.get("personas") or []

# ── Build export content ───────────────────────────────────────────────────────

def build_blog_md(blog: dict, campaign: dict) -> str:
    title = blog.get("title", "Blog Post")
    meta = blog.get("meta_description", "")
    body = blog.get("body", "")
    cta = blog.get("cta", "")
    topic = campaign.get("topic", "")
    date = format_date(campaign.get("created_at", ""))

    lines = [
        f"# {title}",
        "",
        f"> *Meta: {meta}*" if meta else "",
        f"> *Topic: {topic}* | Generated: {date}",
        "",
        "---",
        "",
        body,
    ]
    if cta:
        lines += ["", "---", "", f"**{cta}**"]
    return "\n".join(l for l in lines)


def build_campaign_summary_md(campaign: dict, blog: dict, personas: list) -> str:
    lines = [
        "# NovaMind Campaign Summary",
        "",
        f"**Topic:** {campaign.get('topic', '')}",
        f"**Generated:** {format_date(campaign.get('created_at'))}",
        f"**Tone:** {campaign.get('tone', '')}",
        f"**CTA Type:** {campaign.get('cta_type', '')}",
        f"**Length:** {campaign.get('length_preference', '')}",
        f"**Personas:** {', '.join(get_persona_name(p) for p in personas)}",
        "",
        "---",
        "",
        f"## Blog Post",
        f"**Title:** {blog.get('title', '')}",
        f"**Words:** {word_count(blog.get('body', ''))}",
        f"**Meta:** {blog.get('meta_description', '')}",
        "",
    ]
    return "\n".join(lines)


def build_newsletters_md(newsletters: dict, subject_lines: dict, personas: list) -> str:
    lines = ["# NovaMind — Newsletter Bundle", ""]
    for pid in personas:
        nl = newsletters.get(pid, {})
        sls = subject_lines.get(pid, [])
        icon = get_persona_icon(pid)
        name = get_persona_name(pid)
        lines += [
            f"## {icon} {name}",
            "",
            f"**Subject Line:** {nl.get('subject_line', '')}",
            f"**Preview Text:** {nl.get('preview_text', '')}",
            "",
            nl.get("body", ""),
            "",
            f"**CTA:** {nl.get('cta_text', '')}",
            "",
            "**Alternative Subject Lines:**",
        ]
        for i, sl in enumerate(sls, 1):
            lines.append(f"{i}. {sl}")
        lines += ["", "---", ""]
    return "\n".join(lines)


# Build all exports
blog_md = build_blog_md(blog, campaign)
summary_md = build_campaign_summary_md(campaign, blog, personas)
newsletters_md = build_newsletters_md(newsletters, subject_lines, personas)
campaign_json = json.dumps(campaign, indent=2, default=str)
contacts_csv = crm.export_contacts_csv()

# Estimated sizes
def approx_size(text: str) -> str:
    kb = len(text.encode("utf-8")) / 1024
    return f"~{kb:.1f} KB"

# ── Export Grid ─────────────────────────────────────────────────────────────────
st.markdown("### 📦 Export Options")

# Row 1
row1_col1, row1_col2 = st.columns(2, gap="large")

with row1_col1:
    st.markdown(f"""
    <div class="export-card">
        <span class="format-badge format-md">Markdown</span>
        <div class="export-card-title">📝 Blog Post</div>
        <div class="export-card-desc">
            Complete blog post with title, meta description, full body, and CTA.
            Ready to paste into your CMS or publish directly.
        </div>
        <div class="size-hint">{approx_size(blog_md)} · {word_count(blog.get('body', ''))} words</div>
        <div class="preview-frame">{truncate(blog.get('body', ''), 400)}</div>
    </div>
    """, unsafe_allow_html=True)
    st.download_button(
        "⬇ Download Blog Post (.md)",
        data=blog_md,
        file_name=f"novamind_blog_{selected_id}.md",
        mime="text/markdown",
        use_container_width=True,
        key="dl_blog",
    )

with row1_col2:
    st.markdown(f"""
    <div class="export-card">
        <span class="format-badge format-md">Markdown</span>
        <div class="export-card-title">📋 Campaign Summary</div>
        <div class="export-card-desc">
            High-level campaign brief including topic, settings, persona list,
            and blog metadata. Useful for team handoffs or documentation.
        </div>
        <div class="size-hint">{approx_size(summary_md)}</div>
        <div class="preview-frame">{truncate(summary_md, 400)}</div>
    </div>
    """, unsafe_allow_html=True)
    st.download_button(
        "⬇ Download Campaign Summary (.md)",
        data=summary_md,
        file_name=f"novamind_summary_{selected_id}.md",
        mime="text/markdown",
        use_container_width=True,
        key="dl_summary",
    )

st.markdown("<br>", unsafe_allow_html=True)

# Row 2
row2_col1, row2_col2 = st.columns(2, gap="large")

with row2_col1:
    nl_preview = newsletters_md[:400] + "..." if len(newsletters_md) > 400 else newsletters_md
    st.markdown(f"""
    <div class="export-card">
        <span class="format-badge format-md">Markdown</span>
        <div class="export-card-title">📧 Newsletters Bundle</div>
        <div class="export-card-desc">
            All {len(personas)} newsletter variants in one file — subject lines,
            preview text, body copy, CTAs, and alternative subject line options.
        </div>
        <div class="size-hint">{approx_size(newsletters_md)} · {len(personas)} variants</div>
        <div class="preview-frame">{truncate(nl_preview, 400)}</div>
    </div>
    """, unsafe_allow_html=True)
    st.download_button(
        "⬇ Download Newsletters Bundle (.md)",
        data=newsletters_md,
        file_name=f"novamind_newsletters_{selected_id}.md",
        mime="text/markdown",
        use_container_width=True,
        key="dl_newsletters",
    )

with row2_col2:
    seg_summary = crm.get_segment_summary()
    contact_counts = {s["persona_id"]: s["count"] for s in seg_summary}
    total_contacts = sum(contact_counts.values())

    st.markdown(f"""
    <div class="export-card">
        <span class="format-badge format-csv">CSV</span>
        <div class="export-card-title">👥 CRM Contacts</div>
        <div class="export-card-desc">
            Full contact list ({total_contacts} contacts) with persona segments,
            lifecycle stages, and lead statuses. Import directly into your email platform.
        </div>
        <div class="size-hint">{approx_size(contacts_csv)} · {total_contacts} contacts</div>
        <div style="margin-bottom:12px;">
            {"".join(f'<span style="background:#f1f5f9;border-radius:6px;padding:3px 8px;font-size:12px;margin-right:6px;">{get_persona_icon(p)} {n}</span>' for p, n in contact_counts.items())}
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.download_button(
        "⬇ Download Contacts (.csv)",
        data=contacts_csv,
        file_name="novamind_contacts.csv",
        mime="text/csv",
        use_container_width=True,
        key="dl_contacts",
    )

st.markdown("<br>", unsafe_allow_html=True)

# Row 3 — Full Campaign JSON
st.markdown("### 🗂️ Full Campaign Data (JSON)")
with st.expander("Preview raw campaign JSON"):
    st.code(campaign_json[:3000] + ("\n..." if len(campaign_json) > 3000 else ""), language="json")

json_col1, json_col2, json_col3 = st.columns([2, 1, 3])
with json_col1:
    st.markdown(f"""
    <div style="background:#fef9c3; border-radius:6px; padding:5px 12px; display:inline-block; font-size:11px; font-weight:700; color:#92400e; text-transform:uppercase; letter-spacing:0.05em;">JSON</div>
    <span style="font-size:13px; color:#475569; margin-left:8px;">{approx_size(campaign_json)}</span>
    """, unsafe_allow_html=True)
with json_col2:
    st.download_button(
        "⬇ Download Full JSON",
        data=campaign_json,
        file_name=f"novamind_campaign_{selected_id}.json",
        mime="application/json",
        use_container_width=True,
        key="dl_json",
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Individual Newsletter Exports ──────────────────────────────────────────────
if newsletters and personas:
    st.markdown("### 📩 Individual Newsletter Exports")
    nl_exp_cols = st.columns(len(personas))
    for col, pid in zip(nl_exp_cols, personas):
        nl = newsletters.get(pid, {})
        sls = subject_lines.get(pid, [])
        icon = get_persona_icon(pid)
        name = get_persona_name(pid)
        single_md = f"# {icon} {name} Newsletter\n\n**Subject:** {nl.get('subject_line', '')}\n**Preview:** {nl.get('preview_text', '')}\n\n---\n\n{nl.get('body', '')}\n\n**CTA:** {nl.get('cta_text', '')}\n\n---\n\n**Subject Line Options:**\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(sls))
        with col:
            st.markdown(f"**{icon} {name}**")
            st.download_button(
                f"⬇ Download",
                data=single_md,
                file_name=f"novamind_{pid}_newsletter_{selected_id}.md",
                mime="text/markdown",
                use_container_width=True,
                key=f"dl_nl_{pid}",
            )
