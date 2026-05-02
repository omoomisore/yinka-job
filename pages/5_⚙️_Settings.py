"""
Yinka Job Bot — Settings Page
Configure API keys, search criteria, notifications, and scheduler.
"""

import streamlit as st
import os
from pathlib import Path
from src.database import get_search_history
from src.scheduler import start_scheduled_search, stop_scheduler, is_scheduler_running
from config import (
    SERPAPI_KEY, OPENAI_API_KEY, SMTP_EMAIL, NOTIFICATION_EMAIL,
    SEARCH_QUERIES, SEARCH_LOCATION, CANDIDATE_NAME, SEARCH_INTERVAL_HOURS,
    BASE_DIR, RESUME_PDF_PATH,
)

st.set_page_config(page_title="Settings — Yinka Job Bot", page_icon="⚙️", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .stApp { font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown("# ⚙️ Settings")
st.markdown("Configure your job search preferences and API keys.")
st.markdown("---")

# ============================================================
# API Key Status
# ============================================================
st.markdown("### 🔑 API Keys")

col1, col2, col3 = st.columns(3)

with col1:
    serpapi_status = "✅ Configured" if SERPAPI_KEY else "❌ Missing"
    st.markdown(f"""
    <div style="background: #1A1A2E; border: 1px solid #2D2D44; border-radius: 12px; padding: 16px;">
        <h4 style="color: #E2E8F0; margin-top: 0;">SerpAPI</h4>
        <p style="color: {'#22C55E' if SERPAPI_KEY else '#EF4444'};">{serpapi_status}</p>
        <p style="color: #64748B; font-size: 0.8rem;">Used for job search across all boards</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    openai_status = "✅ Configured" if OPENAI_API_KEY else "❌ Missing"
    st.markdown(f"""
    <div style="background: #1A1A2E; border: 1px solid #2D2D44; border-radius: 12px; padding: 16px;">
        <h4 style="color: #E2E8F0; margin-top: 0;">OpenAI</h4>
        <p style="color: {'#22C55E' if OPENAI_API_KEY else '#EF4444'};">{openai_status}</p>
        <p style="color: #64748B; font-size: 0.8rem;">Used for job scoring & cover letters</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    email_status = "✅ Configured" if SMTP_EMAIL else "❌ Missing"
    st.markdown(f"""
    <div style="background: #1A1A2E; border: 1px solid #2D2D44; border-radius: 12px; padding: 16px;">
        <h4 style="color: #E2E8F0; margin-top: 0;">Email (SMTP)</h4>
        <p style="color: {'#22C55E' if SMTP_EMAIL else '#EF4444'};">{email_status}</p>
        <p style="color: #64748B; font-size: 0.8rem;">Sends notification digests to {NOTIFICATION_EMAIL}</p>
    </div>
    """, unsafe_allow_html=True)

st.info("💡 API keys are configured in the `.env` file in the project root. Edit that file to update keys.")

st.markdown("---")

# ============================================================
# Search Configuration
# ============================================================
st.markdown("### 🔍 Search Configuration")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Current Search Queries:**")
    for q in SEARCH_QUERIES:
        st.markdown(f"- {q}")

with col2:
    st.markdown("**Search Settings:**")
    st.markdown(f"- **Location:** {SEARCH_LOCATION}")
    st.markdown(f"- **Candidate:** {CANDIDATE_NAME}")
    st.markdown(f"- **Notification Email:** {NOTIFICATION_EMAIL}")
    st.markdown(f"- **Search Interval:** Every {SEARCH_INTERVAL_HOURS} hours")

st.info("💡 To modify search queries or criteria, edit `config.py` in the project root.")

st.markdown("---")

# ============================================================
# Scheduler
# ============================================================
st.markdown("### ⏰ Automated Scheduler")

scheduler_running = is_scheduler_running()

col1, col2 = st.columns(2)

with col1:
    if scheduler_running:
        st.success("🟢 Scheduler is **RUNNING**")
        st.markdown(f"Searching every **{SEARCH_INTERVAL_HOURS} hours** automatically")
        if st.button("⏹️ Stop Scheduler"):
            stop_scheduler()
            st.success("Scheduler stopped")
            st.rerun()
    else:
        st.warning("🔴 Scheduler is **STOPPED**")
        if st.button("▶️ Start Scheduler"):
            from src.job_search import run_all_searches
            from src.job_scorer import score_all_unscored
            from src.notifier import send_new_jobs_digest
            start_scheduled_search(run_all_searches, score_all_unscored, send_new_jobs_digest)
            st.success(f"Scheduler started! Searching every {SEARCH_INTERVAL_HOURS} hours.")
            st.rerun()

with col2:
    st.markdown("**How it works:**")
    st.markdown("""
    1. Runs all search queries automatically
    2. Scores new results with AI
    3. Sends email digest of high-scoring matches
    4. Runs in the background while the dashboard is open
    """)

st.markdown("---")

# ============================================================
# Resume
# ============================================================
st.markdown("### 📄 Resume")

col1, col2 = st.columns(2)

with col1:
    resume_pdf_exists = RESUME_PDF_PATH.exists()
    if resume_pdf_exists:
        st.success(f"✅ Resume PDF found: `{RESUME_PDF_PATH.name}`")
    else:
        st.warning("⚠️ No resume PDF found in `resume/` folder")
    
    # Check for the original PDF
    original_pdf = BASE_DIR / "52emuseR.pdf"
    if original_pdf.exists() and not resume_pdf_exists:
        if st.button("📋 Copy resume to resume/ folder"):
            import shutil
            shutil.copy2(str(original_pdf), str(RESUME_PDF_PATH))
            st.success("Resume copied!")
            st.rerun()

with col2:
    resume_txt = BASE_DIR / "resume" / "yinka_resume.txt"
    if resume_txt.exists():
        st.success("✅ Resume text file found (used for AI context)")
    else:
        st.warning("⚠️ Resume text file missing")

st.markdown("---")

# ============================================================
# Search History
# ============================================================
st.markdown("### 📜 Recent Search History")

history = get_search_history(limit=20)
if history:
    for h in history:
        st.markdown(
            f"- **{h['query']}** in {h.get('location', 'N/A')} — "
            f"{h['results_count']} results — {h['searched_at'][:16]}"
        )
else:
    st.info("No searches run yet.")
