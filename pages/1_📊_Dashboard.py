"""
Yinka Job Bot — Dashboard Page
KPI metrics, charts, and analytics overview.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from src.database import get_job_stats, get_all_jobs

st.set_page_config(page_title="Dashboard — Yinka Job Bot", page_icon="📊", layout="wide")

# ============================================================
# Custom CSS (shared)
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .stApp { font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%);
        border: 1px solid #2D2D44;
        border-radius: 12px;
        padding: 16px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("# 📊 Dashboard")
st.markdown("---")

# ============================================================
# KPI Metrics
# ============================================================
try:
    stats = get_job_stats()
except Exception as e:
    st.error(f"Error loading stats: {e}")
    stats = {"total": 0, "new": 0, "applied": 0, "interview": 0, "avg_score": 0, "strong_matches": 0, 
             "by_source": {}, "by_status": {}, "top_companies": {}, "daily_found": {}}

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("📋 Total Jobs", stats["total"])
with col2:
    st.metric("✨ New", stats["new"])
with col3:
    st.metric("🟢 Strong Matches", stats["strong_matches"])
with col4:
    st.metric("📨 Applied", stats["applied"])
with col5:
    st.metric("📈 Avg Score", f"{stats['avg_score']}")

st.markdown("---")

# ============================================================
# Charts
# ============================================================
if stats["total"] > 0:
    col1, col2 = st.columns(2)

    # Jobs by source
    with col1:
        st.markdown("### 🌐 Jobs by Source")
        if stats["by_source"]:
            fig = px.pie(
                values=list(stats["by_source"].values()),
                names=list(stats["by_source"].keys()),
                color_discrete_sequence=px.colors.sequential.Purples_r,
                hole=0.4,
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A3B8"),
                legend=dict(font=dict(color="#E2E8F0")),
                margin=dict(t=20, b=20, l=20, r=20),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No source data yet")

    # Jobs by status
    with col2:
        st.markdown("### 📊 Pipeline Status")
        if stats["by_status"]:
            status_colors = {
                "new": "#A78BFA",
                "reviewed": "#3B82F6",
                "applied": "#22C55E",
                "interview": "#EAB308",
                "rejected": "#EF4444",
            }
            fig = go.Figure(data=[go.Bar(
                x=list(stats["by_status"].keys()),
                y=list(stats["by_status"].values()),
                marker_color=[status_colors.get(s, "#7C3AED") for s in stats["by_status"].keys()],
                marker=dict(
                    line=dict(width=0),
                    cornerradius=8,
                ),
            )])
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A3B8"),
                xaxis=dict(
                    gridcolor="rgba(45,45,68,0.5)",
                    title_font=dict(color="#94A3B8"),
                ),
                yaxis=dict(
                    gridcolor="rgba(45,45,68,0.5)",
                    title_font=dict(color="#94A3B8"),
                ),
                margin=dict(t=20, b=20, l=20, r=20),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No status data yet")

    # Score distribution
    st.markdown("### 🎯 Relevance Score Distribution")
    all_jobs = get_all_jobs(limit=500)
    if all_jobs:
        scores = [j["relevance_score"] for j in all_jobs if j["relevance_score"] > 0]
        if scores:
            fig = go.Figure(data=[go.Histogram(
                x=scores,
                nbinsx=20,
                marker_color="#7C3AED",
                marker_line=dict(width=1, color="#A78BFA"),
            )])
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A3B8"),
                xaxis=dict(
                    title="Relevance Score",
                    gridcolor="rgba(45,45,68,0.5)",
                    range=[0, 100],
                ),
                yaxis=dict(
                    title="Number of Jobs",
                    gridcolor="rgba(45,45,68,0.5)",
                ),
                margin=dict(t=20, b=40, l=40, r=20),
                bargap=0.1,
            )
            # Add threshold lines
            fig.add_vline(x=80, line_dash="dash", line_color="#22C55E", 
                         annotation_text="Strong", annotation_position="top")
            fig.add_vline(x=60, line_dash="dash", line_color="#EAB308",
                         annotation_text="Good", annotation_position="top")
            st.plotly_chart(fig, use_container_width=True)

    # Top companies & Daily trend
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏢 Top Hiring Companies")
        if stats["top_companies"]:
            fig = go.Figure(data=[go.Bar(
                y=list(stats["top_companies"].keys()),
                x=list(stats["top_companies"].values()),
                orientation='h',
                marker_color="#A78BFA",
                marker=dict(cornerradius=6),
            )])
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A3B8"),
                xaxis=dict(gridcolor="rgba(45,45,68,0.5)"),
                yaxis=dict(autorange="reversed"),
                margin=dict(t=20, b=20, l=20, r=20),
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No company data yet")

    with col2:
        st.markdown("### 📅 Jobs Found Per Day")
        if stats["daily_found"]:
            dates = list(stats["daily_found"].keys())
            counts = list(stats["daily_found"].values())
            fig = go.Figure(data=[go.Scatter(
                x=dates, y=counts,
                mode='lines+markers',
                line=dict(color="#7C3AED", width=2),
                marker=dict(size=8, color="#A78BFA"),
                fill='tozeroy',
                fillcolor="rgba(124, 58, 237, 0.1)",
            )])
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A3B8"),
                xaxis=dict(gridcolor="rgba(45,45,68,0.5)"),
                yaxis=dict(gridcolor="rgba(45,45,68,0.5)"),
                margin=dict(t=20, b=20, l=20, r=20),
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No daily data yet")

else:
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px;">
        <div style="font-size: 4rem; margin-bottom: 16px;">🔍</div>
        <h2 style="color: #E2E8F0;">No Jobs Found Yet</h2>
        <p style="color: #94A3B8; font-size: 1.1rem;">Head over to the <strong>Job Search</strong> page to start finding opportunities!</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔍 Start Searching", use_container_width=True):
        st.switch_page("pages/2_🔍_Job_Search.py")
