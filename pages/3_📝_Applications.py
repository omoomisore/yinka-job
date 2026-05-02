"""
Yinka Job Bot — Applications Tracking Page
Track submitted applications and their status through the pipeline.
"""

import streamlit as st
import pandas as pd
from src.database import get_all_applications, update_application_status, insert_application, get_all_jobs

st.set_page_config(page_title="Applications — Yinka Job Bot", page_icon="📝", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .stApp { font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown("# 📝 Applications")
st.markdown("Track your submitted applications and their progress.")
st.markdown("---")

# ============================================================
# Application Pipeline
# ============================================================
applications = get_all_applications()

if applications:
    # Pipeline stats
    statuses = {"applied": 0, "interviewing": 0, "offered": 0, "rejected": 0}
    for app in applications:
        s = app.get("status", "applied")
        if s in statuses:
            statuses[s] += 1

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📨 Applied", statuses["applied"])
    with col2:
        st.metric("🎤 Interviewing", statuses["interviewing"])
    with col3:
        st.metric("🎉 Offered", statuses["offered"])
    with col4:
        st.metric("❌ Rejected", statuses["rejected"])

    st.markdown("---")

    # Applications table
    st.markdown("### 📋 All Applications")
    
    for app in applications:
        status = app.get("status", "applied")
        status_icons = {
            "applied": "📨",
            "interviewing": "🎤",
            "offered": "🎉",
            "rejected": "❌",
        }
        status_colors = {
            "applied": "#3B82F6",
            "interviewing": "#EAB308",
            "offered": "#22C55E",
            "rejected": "#EF4444",
        }
        
        icon = status_icons.get(status, "📨")
        color = status_colors.get(status, "#3B82F6")

        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
            
            with col1:
                st.markdown(f"**{app.get('title', 'N/A')}**")
                st.markdown(f"🏢 {app.get('company', 'N/A')} &nbsp;|&nbsp; 📍 {app.get('location', 'N/A')}")
            
            with col2:
                st.markdown(f"""
                <div style="text-align: center;">
                    <span style="background: {color}22; color: {color}; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">
                        {icon} {status.title()}
                    </span>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                score = app.get("relevance_score", 0)
                st.markdown(f"**Score:** {score}")
                st.markdown(f"**Applied:** {app.get('applied_at', 'N/A')[:10]}")
            
            with col4:
                new_status = st.selectbox(
                    "Update status",
                    ["applied", "interviewing", "offered", "rejected"],
                    index=["applied", "interviewing", "offered", "rejected"].index(status) if status in ["applied", "interviewing", "offered", "rejected"] else 0,
                    key=f"status_{app['id']}",
                    label_visibility="collapsed",
                )
                if new_status != status:
                    if st.button("Update", key=f"update_{app['id']}"):
                        update_application_status(app["id"], new_status)
                        st.rerun()
                
                if app.get("apply_url"):
                    st.link_button("🔗 View Posting", app["apply_url"], use_container_width=True)

            st.markdown("---")

else:
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px;">
        <div style="font-size: 4rem; margin-bottom: 16px;">📭</div>
        <h2 style="color: #E2E8F0;">No Applications Yet</h2>
        <p style="color: #94A3B8; font-size: 1.1rem;">
            Go to the <strong>Job Search</strong> page to find jobs and start applying!
        </p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔍 Find Jobs", use_container_width=True):
        st.switch_page("pages/2_🔍_Job_Search.py")

# ============================================================
# Quick Apply Section
# ============================================================
st.markdown("---")
st.markdown("### ➕ Log Manual Application")

with st.expander("Log an application you submitted manually"):
    applied_jobs = get_all_jobs(min_score=40, limit=100)
    unapplied = [j for j in applied_jobs if j["status"] != "applied"]
    
    if unapplied:
        job_options = {f"{j['title']} at {j['company']}": j["id"] for j in unapplied}
        selected = st.selectbox("Select job", list(job_options.keys()))
        notes = st.text_area("Notes (optional)")
        
        if st.button("📨 Log Application"):
            job_id = job_options[selected]
            insert_application(job_id, method="manual", notes=notes)
            st.success("Application logged!")
            st.rerun()
    else:
        st.info("No eligible jobs to log. Search for jobs first!")
