"""
Yinka Job Bot — Cover Letters Page
Browse, edit, and download AI-generated cover letters.
"""

import streamlit as st
from src.database import get_all_cover_letters, update_cover_letter, get_job_by_id
from src.cover_letter import generate_cover_letter, generate_cover_letter_pdf

st.set_page_config(page_title="Cover Letters — Yinka Job Bot", page_icon="📄", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    .stApp { font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

st.markdown("# 📄 Cover Letters")
st.markdown("AI-generated cover letters tailored to each position.")
st.markdown("---")

# ============================================================
# Cover Letters List
# ============================================================
cover_letters = get_all_cover_letters()

if cover_letters:
    st.markdown(f"### {len(cover_letters)} Cover Letter{'s' if len(cover_letters) != 1 else ''} Generated")
    
    for cl in cover_letters:
        with st.expander(f"📄 {cl.get('title', 'N/A')} — {cl.get('company', 'N/A')}  |  {cl.get('created_at', '')[:10]}"):
            
            # Display cover letter
            st.markdown("---")
            st.markdown(cl["content"])
            st.markdown("---")
            
            # Actions
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("📥 Download PDF", key=f"dl_{cl['id']}"):
                    job = get_job_by_id(cl["job_id"])
                    if job:
                        pdf_path = generate_cover_letter_pdf(cl["content"], job)
                        st.success(f"✅ PDF saved: {pdf_path}")
            
            with col2:
                if st.button("🔄 Regenerate", key=f"regen_{cl['id']}"):
                    job = get_job_by_id(cl["job_id"])
                    if job:
                        with st.spinner("Regenerating..."):
                            new_cl = generate_cover_letter(job)
                            if new_cl:
                                st.success("✅ New cover letter generated!")
                                st.rerun()
            
            with col3:
                tone = st.selectbox(
                    "Tone",
                    ["professional", "enthusiastic", "concise"],
                    key=f"tone_{cl['id']}",
                    label_visibility="collapsed",
                )
                if st.button("🎨 Regenerate with tone", key=f"tone_btn_{cl['id']}"):
                    job = get_job_by_id(cl["job_id"])
                    if job:
                        with st.spinner(f"Regenerating with {tone} tone..."):
                            new_cl = generate_cover_letter(job, tone=tone)
                            if new_cl:
                                st.success(f"✅ {tone.title()} cover letter generated!")
                                st.rerun()
            
            with col4:
                pass  # Spacer
            
            # Edit section
            st.markdown("#### ✏️ Edit")
            edited_content = st.text_area(
                "Edit cover letter",
                value=cl["content"],
                height=300,
                key=f"edit_{cl['id']}",
                label_visibility="collapsed",
            )
            if edited_content != cl["content"]:
                if st.button("💾 Save Changes", key=f"save_{cl['id']}"):
                    update_cover_letter(cl["id"], edited_content)
                    st.success("✅ Changes saved!")
                    st.rerun()

else:
    st.markdown("""
    <div style="text-align: center; padding: 60px 20px;">
        <div style="font-size: 4rem; margin-bottom: 16px;">📝</div>
        <h2 style="color: #E2E8F0;">No Cover Letters Yet</h2>
        <p style="color: #94A3B8; font-size: 1.1rem;">
            Cover letters are generated when you click "Cover Letter" on a job in the <strong>Job Search</strong> page.
        </p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🔍 Find Jobs", use_container_width=True):
        st.switch_page("pages/2_🔍_Job_Search.py")
