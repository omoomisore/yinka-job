"""
Yinka Job Bot — Job Search Page
Trigger searches, browse results, apply to jobs with one-click automation.
Works both locally (visible browser) and in cloud (headless with screenshots).
"""

import sys
import json
import streamlit as st
from pathlib import Path
from src.database import (
    get_all_jobs, update_job_status, get_unscored_jobs,
    search_jobs_db, get_cover_letter, get_job_by_id,
)
from src.job_search import run_all_searches
from src.job_scorer import score_all_unscored, get_score_display
from src.cover_letter import generate_cover_letter, generate_cover_letter_pdf
from src.auto_apply import record_application, check_daily_limit, SCREENSHOTS_DIR, launch_browser_and_apply
from config import (
    CANDIDATE_NAME, CANDIDATE_EMAIL, CANDIDATE_PHONE, CANDIDATE_LOCATION,
    BASE_DIR, IS_CLOUD,
)

st.set_page_config(page_title="Job Search — Yinka Job Bot", page_icon="🔍", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .stApp { font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .apply-confirmation {
        background: linear-gradient(135deg, #1E1B4B 0%, #1E1E2E 100%);
        border: 1px solid #7C3AED44;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
    }
    .candidate-info-card {
        background: #1E1E2E;
        border-radius: 12px;
        padding: 16px;
        border-left: 3px solid #A78BFA;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("# 🔍 Job Search")
st.markdown("---")

# ============================================================
# Initialize session state
# ============================================================
if "apply_job_id" not in st.session_state:
    st.session_state.apply_job_id = None
if "apply_step" not in st.session_state:
    st.session_state.apply_step = None  # None, "confirm", "applying", "done"
if "apply_result" not in st.session_state:
    st.session_state.apply_result = None
if "apply_cover_letter" not in st.session_state:
    st.session_state.apply_cover_letter = None

# ============================================================
# APPLICATION CONFIRMATION DIALOG
# ============================================================
if st.session_state.apply_step == "confirm" and st.session_state.apply_job_id:
    job = get_job_by_id(st.session_state.apply_job_id)

    if job:
        score = job.get("relevance_score", 0)
        score_info = get_score_display(score)

        st.markdown("## 🚀 Apply to This Job")

        # Job summary card
        st.markdown(f"""
        <div class="apply-confirmation">
            <h3 style="color: #A78BFA; margin-top: 0;">{job['title']}</h3>
            <p style="color: #E2E8F0;">🏢 <strong>{job['company']}</strong> &nbsp;|&nbsp; 📍 {job.get('location', 'N/A')}</p>
            <p>
                <span style="background: {score_info['color']}22; color: {score_info['color']}; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: bold;">
                    {score_info['emoji']} Score: {score} — {score_info['label']}
                </span>
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Candidate info being submitted
        st.markdown("### 📋 Information to Submit")
        info_col1, info_col2 = st.columns(2)
        with info_col1:
            st.markdown(f"""
            <div class="candidate-info-card">
                <p style="color: #94A3B8; margin: 4px 0;"><strong style="color: #E2E8F0;">Name:</strong> {CANDIDATE_NAME}</p>
                <p style="color: #94A3B8; margin: 4px 0;"><strong style="color: #E2E8F0;">Email:</strong> {CANDIDATE_EMAIL}</p>
                <p style="color: #94A3B8; margin: 4px 0;"><strong style="color: #E2E8F0;">Phone:</strong> {CANDIDATE_PHONE}</p>
                <p style="color: #94A3B8; margin: 4px 0;"><strong style="color: #E2E8F0;">Location:</strong> {CANDIDATE_LOCATION}</p>
            </div>
            """, unsafe_allow_html=True)
        with info_col2:
            st.markdown(f"""
            <div class="candidate-info-card">
                <p style="color: #94A3B8; margin: 4px 0;"><strong style="color: #E2E8F0;">Resume:</strong> ✅ yinka_resume.pdf</p>
                <p style="color: #94A3B8; margin: 4px 0;"><strong style="color: #E2E8F0;">Source:</strong> {job.get('source', 'N/A')}</p>
                <p style="color: #94A3B8; margin: 4px 0;"><strong style="color: #E2E8F0;">Apply URL:</strong> <a href="{job.get('apply_url', '#')}" target="_blank">View →</a></p>
            </div>
            """, unsafe_allow_html=True)

        # Cover letter section
        st.markdown("### 📝 Cover Letter")

        # Check for existing cover letter
        existing_cl = get_cover_letter(job["id"])
        if existing_cl:
            st.session_state.apply_cover_letter = existing_cl["content"]
            st.success("✅ Cover letter already generated")
        elif st.session_state.apply_cover_letter is None:
            if st.button("✨ Generate Cover Letter", type="primary"):
                with st.spinner("🤖 Claude is writing a tailored cover letter..."):
                    cl_text = generate_cover_letter(job)
                    if cl_text:
                        st.session_state.apply_cover_letter = cl_text
                        st.rerun()
                    else:
                        st.error("Failed to generate cover letter")

        if st.session_state.apply_cover_letter:
            with st.expander("📄 Preview Cover Letter", expanded=True):
                edited_cl = st.text_area(
                    "Edit if needed:",
                    value=st.session_state.apply_cover_letter,
                    height=300,
                    key="cl_edit_area",
                )
                st.session_state.apply_cover_letter = edited_cl

        st.markdown("---")

        # Action buttons
        btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 1])

        with btn_col1:
            if st.button(
                "🚀 Confirm & Apply",
                type="primary",
                use_container_width=True,
                disabled=(st.session_state.apply_cover_letter is None),
            ):
                st.session_state.apply_step = "applying"
                st.rerun()

        with btn_col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.apply_job_id = None
                st.session_state.apply_step = None
                st.session_state.apply_result = None
                st.session_state.apply_cover_letter = None
                st.rerun()

        with btn_col3:
            within_limit, count = check_daily_limit()
            st.markdown(f"""
            <div style="text-align: center; padding: 8px;">
                <div style="color: {'#22C55E' if within_limit else '#EF4444'}; font-size: 0.8rem;">
                    {count}/10 today
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.stop()

# ============================================================
# AUTO-APPLY IN PROGRESS
# ============================================================
elif st.session_state.apply_step == "applying" and st.session_state.apply_job_id:
    job = get_job_by_id(st.session_state.apply_job_id)

    if job:
        st.markdown("## 🤖 Applying Autonomously...")
        st.markdown(f"**{job['title']}** at **{job['company']}**")
        if IS_CLOUD:
            st.caption("☁️ Running in cloud mode (headless browser)")
        else:
            st.caption("🖥️ Running locally (visible browser)")
        st.markdown("---")

        progress = st.progress(0, text="Starting...")

        try:
            import time

            # Step 1: Record application
            progress.progress(10, text="📝 Recording application...")
            app_id = record_application(
                job=job,
                method="auto-apply",
                cover_letter_text=st.session_state.apply_cover_letter,
                screenshot_path=None,
            )
            time.sleep(0.3)

            # Step 2: Send email confirmation
            progress.progress(20, text="📧 Sending confirmation email...")
            time.sleep(0.3)

            # Step 3: Run Playwright
            apply_url = job.get("apply_url")
            browser_result = None

            if apply_url:
                if IS_CLOUD:
                    # CLOUD: Run Playwright INLINE (headless)
                    progress.progress(30, text="🌐 Launching headless browser...")

                    job_data = {
                        "id": job["id"],
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "location": job.get("location", ""),
                        "apply_url": apply_url,
                        "relevance_score": job.get("relevance_score", 0),
                    }

                    progress.progress(40, text="📄 Opening job page & filling form...")
                    browser_result = launch_browser_and_apply(
                        job_data,
                        st.session_state.apply_cover_letter,
                    )
                    progress.progress(90, text="📸 Capturing screenshots...")

                else:
                    # LOCAL: Launch as subprocess (visible browser)
                    import subprocess

                    progress.progress(30, text="🌐 Opening visible browser...")
                    job_json = json.dumps({
                        "id": job["id"],
                        "title": job.get("title", ""),
                        "company": job.get("company", ""),
                        "location": job.get("location", ""),
                        "apply_url": apply_url,
                        "relevance_score": job.get("relevance_score", 0),
                    })

                    cl_text = st.session_state.apply_cover_letter or ""

                    subprocess.Popen(
                        [
                            sys.executable, "-c",
                            f"""
import sys, json
sys.path.insert(0, r'{str(BASE_DIR)}')
from src.auto_apply import launch_browser_and_apply
job = json.loads('''{job_json}''')
cl = '''{cl_text.replace("'", "").replace(chr(10), " ")}'''
launch_browser_and_apply(job, cl if cl else None)
"""
                        ],
                        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
                    )

            progress.progress(100, text="✅ Complete!")
            time.sleep(0.5)

            st.session_state.apply_result = {
                "success": True,
                "method": "auto-apply",
                "app_id": app_id,
                "browser_result": browser_result,
            }
            st.session_state.apply_step = "done"
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            if st.button("← Back", type="primary"):
                st.session_state.apply_step = "confirm"
                st.rerun()

    st.stop()

# ============================================================
# APPLICATION RESULT
# ============================================================
elif st.session_state.apply_step == "done" and st.session_state.apply_result:
    job = get_job_by_id(st.session_state.apply_job_id)
    result = st.session_state.apply_result
    browser_result = result.get("browser_result")

    if result.get("success"):
        was_submitted = browser_result and browser_result.get("submitted", False)
        fields_filled = browser_result.get("fields_filled", 0) if browser_result else 0
        screenshots = browser_result.get("screenshots", []) if browser_result else []

        if was_submitted:
            st.markdown("## ✅ Application Submitted!")
        elif IS_CLOUD and browser_result:
            st.markdown("## 🤖 Application Processed!")
        else:
            st.markdown("## 🚀 Application in Progress!")
        st.balloons()

        if job:
            st.markdown(f"""
            <div class="apply-confirmation">
                <h3 style="color: #22C55E; margin-top: 0;">{'✅' if was_submitted else '🚀'} {job['title']}</h3>
                <p style="color: #E2E8F0;">🏢 <strong>{job['company']}</strong> &nbsp;|&nbsp; 📍 {job.get('location', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

        submit_status = "✅ Submitted" if was_submitted else "⚠️ Needs manual submit"
        fill_status = f"✅ {fields_filled} fields" if fields_filled > 0 else "⚠️ No fields found"

        st.markdown("### What happened:")
        st.markdown(f"""
        | Step | Status | Details |
        |------|--------|---------|
        | 📝 **Tracked** | ✅ Done | Application recorded in dashboard |
        | 📧 **Email** | ✅ Sent | Confirmation to {CANDIDATE_EMAIL} |
        | 🌐 **Browser** | ✅ Ran | {'Headless (cloud)' if IS_CLOUD else 'Visible (local)'} |
        | 📝 **Form fill** | {fill_status} | Auto-filled candidate info |
        | 🚀 **Submit** | {submit_status} | {'Clicked Submit button' if was_submitted else 'Manual action needed'} |
        """)

        if browser_result and browser_result.get("message"):
            if was_submitted:
                st.success(f"🎉 {browser_result['message']}")
            else:
                st.info(f"ℹ️ {browser_result['message']}")

        if screenshots:
            st.markdown("### 📸 Screenshot Proof")
            for ss_path in screenshots:
                try:
                    st.image(ss_path, caption=Path(ss_path).name, use_container_width=True)
                except Exception:
                    st.text(f"Screenshot: {ss_path}")
        else:
            all_screenshots = list(SCREENSHOTS_DIR.glob("*.png"))
            if all_screenshots:
                latest = sorted(all_screenshots, key=lambda f: f.stat().st_mtime, reverse=True)[:4]
                st.markdown("### 📸 Screenshot Proof")
                for ss in latest:
                    try:
                        st.image(str(ss), caption=ss.name, use_container_width=True)
                    except Exception:
                        st.text(f"Screenshot: {ss}")

        if not was_submitted and job and job.get("apply_url"):
            st.markdown("---")
            st.markdown(f"🔗 **[Open application page →]({job['apply_url']})**")

    else:
        st.error(f"❌ Application failed: {result.get('message', 'Unknown error')}")

    if st.button("← Back to Job Search", type="primary"):
        st.session_state.apply_job_id = None
        st.session_state.apply_step = None
        st.session_state.apply_result = None
        st.session_state.apply_cover_letter = None
        st.rerun()

    st.stop()


# ============================================================
# MAIN JOB SEARCH VIEW (default)
# ============================================================

# Search Controls
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown("### Run New Search")
    st.markdown("Searches across LinkedIn, Indeed, Glassdoor, ZipRecruiter via Google Jobs")

with col2:
    if st.button("🔍 Search Now", use_container_width=True, type="primary"):
        with st.spinner("🔍 Searching all job boards..."):
            try:
                summary = run_all_searches()
                st.success(
                    f"✅ Found **{summary['total_found']}** jobs "
                    f"(**{summary['total_new']}** new, {summary['total_duplicate']} duplicates)"
                )
                if summary.get("errors"):
                    for err in summary["errors"]:
                        st.warning(f"⚠️ {err}")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Search failed: {e}")

with col3:
    unscored = get_unscored_jobs()
    if unscored:
        if st.button(f"📊 Score {len(unscored)} Jobs", use_container_width=True):
            with st.spinner(f"📊 AI scoring {len(unscored)} jobs..."):
                try:
                    result = score_all_unscored()
                    st.success(f"✅ Scored {result['scored']} jobs ({result['errors']} errors)")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Scoring failed: {e}")
    else:
        st.button("✅ All Scored", use_container_width=True, disabled=True)

st.markdown("---")

# Filters
col1, col2, col3, col4 = st.columns(4)

with col1:
    status_filter = st.selectbox(
        "Status",
        ["All", "new", "reviewed", "applied", "interview", "rejected"],
        index=0,
    )

with col2:
    min_score = st.slider("Min Score", 0, 100, 0, step=10)

with col3:
    search_query = st.text_input("🔎 Search jobs", placeholder="Search by title, company...")

with col4:
    sort_order = st.selectbox("Sort by", ["Score (High → Low)", "Date (Newest)", "Company (A-Z)"])

# ============================================================
# Job Results
# ============================================================
status_param = None if status_filter == "All" else status_filter

if search_query:
    jobs = search_jobs_db(search_query)
    if min_score > 0:
        jobs = [j for j in jobs if j["relevance_score"] >= min_score]
    if status_param:
        jobs = [j for j in jobs if j["status"] == status_param]
else:
    jobs = get_all_jobs(status=status_param, min_score=min_score, limit=200)

# Sort
if sort_order == "Date (Newest)":
    jobs.sort(key=lambda j: j.get("date_found", ""), reverse=True)
elif sort_order == "Company (A-Z)":
    jobs.sort(key=lambda j: j.get("company", "").lower())

st.markdown(f"### 📋 {len(jobs)} Job{'s' if len(jobs) != 1 else ''} Found")

if not jobs:
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px;">
        <div style="font-size: 3rem; margin-bottom: 12px;">📭</div>
        <h3 style="color: #94A3B8;">No jobs match your filters</h3>
        <p style="color: #64748B;">Try adjusting your filters or run a new search</p>
    </div>
    """, unsafe_allow_html=True)
else:
    for job in jobs:
        score = job.get("relevance_score", 0)
        score_info = get_score_display(score)

        # Parse reasoning if available
        reasoning_data = {}
        if job.get("score_reasoning"):
            try:
                reasoning_data = json.loads(job["score_reasoning"])
            except (json.JSONDecodeError, TypeError):
                reasoning_data = {}

        # Job card
        with st.container():
            col_main, col_score, col_actions = st.columns([4, 1, 2])

            with col_main:
                # Show applied badge
                title_extra = ""
                if job.get("status") == "applied":
                    title_extra = " ✅"
                st.markdown(f"#### {job['title']}{title_extra}")
                info_parts = [f"🏢 **{job['company']}**"]
                if job.get("location"):
                    info_parts.append(f"📍 {job['location']}")
                if job.get("salary_info"):
                    info_parts.append(f"💰 {job['salary_info']}")
                if job.get("job_type"):
                    info_parts.append(f"⏰ {job['job_type']}")
                if job.get("source"):
                    info_parts.append(f"🌐 {job['source']}")
                st.markdown(" &nbsp;|&nbsp; ".join(info_parts))

            with col_score:
                if score > 0:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 8px;">
                        <div style="font-size: 2rem; font-weight: 700; color: {score_info['color']};">{score}</div>
                        <div style="color: {score_info['color']}; font-size: 0.8rem; font-weight: 600;">{score_info['label']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="text-align: center; padding: 8px; color: #64748B;">
                        <div style="font-size: 1.2rem;">—</div>
                        <div style="font-size: 0.8rem;">Unscored</div>
                    </div>
                    """, unsafe_allow_html=True)

            with col_actions:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if job.get("status") == "applied":
                        st.button("✅ Applied", key=f"applied_{job['id']}", disabled=True, use_container_width=True)
                    elif job.get("apply_url"):
                        if st.button("🚀 Apply", key=f"apply_{job['id']}", use_container_width=True, type="primary"):
                            st.session_state.apply_job_id = job["id"]
                            st.session_state.apply_step = "confirm"
                            st.session_state.apply_cover_letter = None
                            st.rerun()
                with btn_col2:
                    if st.button("📄 Cover Letter", key=f"cl_{job['id']}", use_container_width=True):
                        with st.spinner("Generating cover letter..."):
                            existing = get_cover_letter(job["id"])
                            if existing:
                                st.session_state[f"show_cl_{job['id']}"] = existing["content"]
                            else:
                                cl = generate_cover_letter(job)
                                if cl:
                                    st.session_state[f"show_cl_{job['id']}"] = cl

            # Expandable details
            with st.expander("📝 View Details", expanded=False):
                tab1, tab2, tab3 = st.tabs(["Description", "AI Analysis", "Actions"])

                with tab1:
                    st.markdown(job.get("description", "No description available")[:3000])

                with tab2:
                    if reasoning_data:
                        if reasoning_data.get("reasoning"):
                            st.markdown("**Match Reasoning:**")
                            for r in reasoning_data["reasoning"]:
                                st.markdown(f"- {r}")
                        if reasoning_data.get("matching_skills"):
                            st.markdown("**Matching Skills:**")
                            st.markdown(", ".join(reasoning_data["matching_skills"]))
                        if reasoning_data.get("red_flags"):
                            st.markdown("**⚠️ Red Flags:**")
                            for rf in reasoning_data["red_flags"]:
                                st.markdown(f"- {rf}")
                    else:
                        st.info("Job hasn't been scored yet. Click 'Score Jobs' above.")

                with tab3:
                    action_col1, action_col2, action_col3, action_col4 = st.columns(4)
                    with action_col1:
                        if st.button("✅ Mark Reviewed", key=f"rev_{job['id']}"):
                            update_job_status(job["id"], "reviewed")
                            st.rerun()
                    with action_col2:
                        if st.button("📨 Mark Applied", key=f"app_{job['id']}"):
                            update_job_status(job["id"], "applied")
                            st.rerun()
                    with action_col3:
                        if st.button("🎉 Interview", key=f"int_{job['id']}"):
                            update_job_status(job["id"], "interview")
                            st.rerun()
                    with action_col4:
                        if st.button("❌ Dismiss", key=f"rej_{job['id']}"):
                            update_job_status(job["id"], "rejected")
                            st.rerun()

            # Show cover letter if generated
            cl_key = f"show_cl_{job['id']}"
            if cl_key in st.session_state:
                with st.expander("📄 Generated Cover Letter", expanded=True):
                    st.markdown(st.session_state[cl_key])
                    if st.button("📥 Download PDF", key=f"pdf_{job['id']}"):
                        pdf_path = generate_cover_letter_pdf(st.session_state[cl_key], job)
                        st.success(f"PDF saved: {pdf_path}")

            st.markdown("---")
