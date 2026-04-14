"""
NovaMind — Analytics & Performance
Visualize campaign performance, persona benchmarks, and AI-powered insights.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from utils.config import MOCK_MODE
from utils.helpers import get_persona_name, get_persona_color, get_persona_icon, format_percentage
from db import database as db
from services.analytics_service import AnalyticsService

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Analytics — NovaMind",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.kpi-card {
    background: white;
    border-radius: 12px;
    padding: 18px 22px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.kpi-label { font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }
.kpi-value { font-size: 30px; font-weight: 800; color: #0f172a; margin-top: 4px; }
.kpi-delta-pos { font-size: 13px; color: #16a34a; font-weight: 600; }
.kpi-delta-neg { font-size: 13px; color: #dc2626; font-weight: 600; }

.insight-section {
    background: linear-gradient(135deg, #f8faff 0%, #f0f4ff 100%);
    border: 1px solid #e0e7ff;
    border-radius: 16px;
    padding: 28px;
}
.insight-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    border: 1px solid #e0e7ff;
    height: 100%;
}
.insight-icon { font-size: 28px; margin-bottom: 10px; }
.insight-headline { font-size: 15px; font-weight: 700; color: #1e293b; margin-bottom: 8px; }
.insight-detail { font-size: 13px; color: #475569; line-height: 1.6; }
.insight-metric { font-size: 12px; font-weight: 600; color: #6366f1; margin-top: 10px; }

.table-header { font-weight: 700; font-size: 13px; color: #374151; }
</style>
""", unsafe_allow_html=True)

# ── Init ───────────────────────────────────────────────────────────────────────
db.init_db()

@st.cache_resource
def get_analytics():
    return AnalyticsService()

analytics = get_analytics()

PERSONA_DISPLAY = {
    "agency_owner": ("🏢", "Agency Owner", "#6366f1"),
    "startup_marketer": ("🚀", "Startup Marketer", "#0ea5e9"),
    "solo_creator": ("✏️", "Solo Creator", "#10b981"),
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
    st.caption("Performance data is based on historical benchmarks and mock analytics.")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("# 📊 Analytics & Performance")
st.markdown("Track open rates, click-through rates, and conversion across all persona segments.")
st.divider()

# ── Time Range Selector ────────────────────────────────────────────────────────
time_range = st.radio(
    "Time Range",
    options=["Last 4 weeks", "Last 8 weeks", "All time"],
    index=1,
    horizontal=True,
)
weeks_to_show = {"Last 4 weeks": 4, "Last 8 weeks": 8, "All time": 8}[time_range]

# ── KPI Row ────────────────────────────────────────────────────────────────────
summary = analytics.get_performance_summary()
campaigns = db.get_campaigns(limit=100)
total_campaigns = len(campaigns)
best_persona_id = summary.get("best_open_rate_persona", "solo_creator")
best_icon, best_name, _ = PERSONA_DISPLAY.get(best_persona_id, ("", best_persona_id, "#6366f1"))

kpi_cols = st.columns(4)

with kpi_cols[0]:
    delta = summary.get("open_rate_delta", 0)
    delta_sign = "+" if delta >= 0 else ""
    delta_cls = "kpi-delta-pos" if delta >= 0 else "kpi-delta-neg"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Overall Open Rate</div>
        <div class="kpi-value">{summary['avg_open_rate']}%</div>
        <div class="{delta_cls}">{delta_sign}{delta}% vs prev period</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[1]:
    delta_ctr = summary.get("ctr_delta", 0)
    delta_sign = "+" if delta_ctr >= 0 else ""
    delta_cls = "kpi-delta-pos" if delta_ctr >= 0 else "kpi-delta-neg"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Overall CTR</div>
        <div class="kpi-value">{summary['avg_ctr']}%</div>
        <div class="{delta_cls}">{delta_sign}{delta_ctr}% vs prev period</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[2]:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Total Campaigns</div>
        <div class="kpi-value">{total_campaigns}</div>
        <div style="font-size:12px; color:#94a3b8;">All time</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_cols[3]:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Best Performing Persona</div>
        <div class="kpi-value" style="font-size:20px;">{best_icon} {best_name}</div>
        <div style="font-size:12px; color:#94a3b8;">Highest open rate</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ─────────────────────────────────────────────────────────────────────
trend_df = analytics.get_weekly_trend_data()

# Filter to selected weeks
if weeks_to_show < 8:
    trend_df = trend_df.groupby("persona").apply(
        lambda x: x.tail(weeks_to_show)
    ).reset_index(drop=True)

# Persona name mapping for chart labels
# detect persona column safely
if "persona" in trend_df.columns:
    persona_col = "persona"
elif "Persona" in trend_df.columns:
    persona_col = "Persona"
else:
    persona_col = None

if persona_col:
    trend_df["Persona"] = trend_df[persona_col].map({
        "agency_owner": "Agency Owner",
        "startup_marketer": "Startup Marketer",
        "solo_creator": "Solo Creator",
    })


color_map = {
    "Agency Owner": "#6366f1",
    "Startup Marketer": "#0ea5e9",
    "Solo Creator": "#10b981",
}

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    fig1 = px.line(
        trend_df,
        x="week",
        y="open_rate",
        color="Persona",
        markers=True,
        title="Open Rate Trends by Persona",
        labels={"open_rate": "Open Rate (%)", "week": "Week"},
        color_discrete_map=color_map,
    )
    fig1.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(t=60, b=30, l=40, r=20),
        yaxis=dict(range=[15, 45], ticksuffix="%"),
        height=340,
    )
    fig1.update_traces(line=dict(width=2.5), marker=dict(size=6))
    st.plotly_chart(fig1, use_container_width=True)

with chart_col2:
    benchmarks = analytics.get_persona_benchmarks()
    bar_data = pd.DataFrame([
        {"Persona": PERSONA_DISPLAY[k][1], "CTR (%)": v["ctr"], "color": PERSONA_DISPLAY[k][2]}
        for k, v in benchmarks.items()
    ])
    fig2 = px.bar(
        bar_data,
        x="Persona",
        y="CTR (%)",
        title="Click-Through Rate by Segment",
        color="Persona",
        color_discrete_map={v[1]: v[2] for v in PERSONA_DISPLAY.values()},
        text="CTR (%)",
    )
    fig2.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Inter, sans-serif", size=12),
        showlegend=False,
        margin=dict(t=60, b=30, l=40, r=20),
        yaxis=dict(ticksuffix="%"),
        height=340,
    )
    fig2.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    st.plotly_chart(fig2, use_container_width=True)

# ── Conversion Rate Chart ──────────────────────────────────────────────────────
conv_data = pd.DataFrame([
    {"Persona": PERSONA_DISPLAY[k][1], "Conversion Rate (%)": v["conversion"], "color": PERSONA_DISPLAY[k][2]}
    for k, v in benchmarks.items()
])
fig3 = px.bar(
    conv_data.sort_values("Conversion Rate (%)"),
    x="Conversion Rate (%)",
    y="Persona",
    orientation="h",
    title="Conversion Rate Comparison",
    color="Persona",
    color_discrete_map={v[1]: v[2] for v in PERSONA_DISPLAY.values()},
    text="Conversion Rate (%)",
)
fig3.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(family="Inter, sans-serif", size=12),
    showlegend=False,
    margin=dict(t=60, b=30, l=40, r=60),
    xaxis=dict(ticksuffix="%"),
    height=260,
)
fig3.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
st.plotly_chart(fig3, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Best Subject Lines ─────────────────────────────────────────────────────────
st.markdown("### 💌 Best Performing Subject Lines")
top_subjects = analytics.get_top_subject_lines()

subj_cols = st.columns(3)
for col, (pid, subjects) in zip(subj_cols, top_subjects.items()):
    icon, name, color = PERSONA_DISPLAY.get(pid, ("", pid, "#6366f1"))
    with col:
        st.markdown(f"**{icon} {name}**")
        for s in subjects:
            bar_width = int(s["open_rate"] / 45 * 100)
            st.markdown(f"""
            <div style="background:#f8fafc; border-radius:8px; padding:10px 12px; margin-bottom:8px; border:1px solid #e2e8f0;">
                <div style="font-size:13px; font-weight:500; color:#1e293b; margin-bottom:6px;">"{s['subject']}"</div>
                <div style="display:flex; align-items:center; gap:8px;">
                    <div style="flex:1; background:#e2e8f0; border-radius:4px; height:6px;">
                        <div style="width:{bar_width}%; background:{color}; height:6px; border-radius:4px;"></div>
                    </div>
                    <span style="font-size:12px; font-weight:700; color:{color};">{s['open_rate']}%</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── AI Insights ───────────────────────────────────────────────────────────────
st.markdown("---")
insights_data = analytics.generate_ai_insights()

st.markdown("""
<div class="insight-section">
    <h3 style="margin-top:0; margin-bottom:6px; color:#1e293b;">🤖 AI Optimization Insights</h3>
    <p style="margin-top:0; margin-bottom:20px; color:#64748b; font-size:14px;">
        Patterns detected across all campaigns and segments. Updated weekly.
    </p>
""", unsafe_allow_html=True)

insight_cols = st.columns(3)
for col, card in zip(insight_cols, insights_data["insight_cards"]):
    with col:
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-icon">{card['icon']}</div>
            <div class="insight-headline">{card['headline']}</div>
            <div class="insight-detail">{card['detail']}</div>
            <div class="insight-metric">{card['metric']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Summary paragraph
with st.expander("📋 Full AI Analysis Summary"):
    st.markdown(f"""
    **Weekly Performance Summary**

    {insights_data['summary']}

    **Top Persona:** {get_persona_icon(insights_data['top_persona'])} {get_persona_name(insights_data['top_persona'])}

    **Winning Angle This Period:** {insights_data['winning_angle']}

    **Recommended Next Test:** {insights_data['next_test_recommendation']}
    """)
