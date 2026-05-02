"""
Yinka Job Bot — Main Streamlit Application
Entry point for the multi-page dashboard.
"""

import streamlit as st
from src.database import init_db, get_job_stats

# Initialize database
init_db()

# ============================================================
# Page Configuration
# ============================================================
st.set_page_config(
    page_title="Yinka Job Bot",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# Custom CSS for Premium Styling
# ============================================================
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F0F1A 0%, #1A1A2E 100%);
        border-right: 1px solid #2D2D44;
    }
    
    [data-testid="stSidebar"] .stMarkdown h1 {
        color: #A78BFA;
        font-size: 1.5rem;
        font-weight: 700;
    }
    
    /* Metric cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%);
        border: 1px solid #2D2D44;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    [data-testid="stMetricLabel"] {
        color: #94A3B8 !important;
        font-size: 0.85rem !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #E2E8F0 !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 24px;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(124, 58, 237, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%);
        box-shadow: 0 4px 16px rgba(124, 58, 237, 0.5);
        transform: translateY(-1px);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #1A1A2E;
        border-radius: 8px;
        border: 1px solid #2D2D44;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: #1A1A2E;
        border-radius: 8px;
        border: 1px solid #2D2D44;
        color: #94A3B8;
        padding: 8px 16px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%) !important;
        color: white !important;
        border: none !important;
    }
    
    /* DataFrames / Tables */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Success/Warning/Error boxes */
    .stAlert {
        border-radius: 10px;
    }
    
    /* Custom card style */
    .job-card {
        background: linear-gradient(135deg, #1A1A2E 0%, #16213E 100%);
        border: 1px solid #2D2D44;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 12px;
        transition: all 0.3s ease;
    }
    
    .job-card:hover {
        border-color: #7C3AED;
        box-shadow: 0 4px 16px rgba(124, 58, 237, 0.2);
    }
    
    .score-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .score-strong { background: #22C55E22; color: #22C55E; }
    .score-good { background: #EAB30822; color: #EAB308; }
    .score-weak { background: #F9731622; color: #F97316; }
    .score-skip { background: #EF444422; color: #EF4444; }
    
    /* Divider */
    hr {
        border-color: #2D2D44;
    }
    
    /* Welcome hero */
    .hero-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #A78BFA, #7C3AED, #6D28D9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    
    .hero-subtitle {
        color: #94A3B8;
        font-size: 1.1rem;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Sidebar
# ============================================================
with st.sidebar:
    st.markdown("# 🎯 Yinka Job Bot")
    st.markdown("---")
    
    # Quick stats
    try:
        stats = get_job_stats()
        st.metric("Total Jobs Found", stats["total"])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Strong Matches", stats["strong_matches"])
        with col2:
            st.metric("Applied", stats["applied"])
        
        st.markdown("---")
    except Exception:
        pass
    
    st.markdown("""
    <div style="color: #64748B; font-size: 0.8rem; padding: 8px;">
        <p>🤖 Automated job search for<br><strong style="color: #A78BFA;">Yinka Omisore</strong></p>
        <p>UKG Pro WFM • HRIS • Workforce Management</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# Main Landing Page
# ============================================================
st.markdown("""
<div style="text-align: center; padding: 40px 0 20px 0;">
    <div class="hero-title">🎯 Yinka Job Bot</div>
    <p class="hero-subtitle">Automated Job Search & Application Assistant</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Quick action cards
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="job-card" style="text-align: center; padding: 30px;">
        <div style="font-size: 2.5rem; margin-bottom: 12px;">🔍</div>
        <h3 style="color: #E2E8F0; margin: 0;">Search Jobs</h3>
        <p style="color: #94A3B8; font-size: 0.9rem;">Find new UKG & WFM opportunities across all major job boards</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Go to Search →", key="nav_search", use_container_width=True):
        st.switch_page("pages/2_🔍_Job_Search.py")

with col2:
    st.markdown("""
    <div class="job-card" style="text-align: center; padding: 30px;">
        <div style="font-size: 2.5rem; margin-bottom: 12px;">📊</div>
        <h3 style="color: #E2E8F0; margin: 0;">Dashboard</h3>
        <p style="color: #94A3B8; font-size: 0.9rem;">View analytics, scores, and track your application pipeline</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("View Dashboard →", key="nav_dash", use_container_width=True):
        st.switch_page("pages/1_📊_Dashboard.py")

with col3:
    st.markdown("""
    <div class="job-card" style="text-align: center; padding: 30px;">
        <div style="font-size: 2.5rem; margin-bottom: 12px;">📄</div>
        <h3 style="color: #E2E8F0; margin: 0;">Cover Letters</h3>
        <p style="color: #94A3B8; font-size: 0.9rem;">AI-generated cover letters tailored to each position</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("View Letters →", key="nav_cl", use_container_width=True):
        st.switch_page("pages/4_📄_Cover_Letters.py")

# How it works
st.markdown("---")
st.markdown("### ⚡ How It Works")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div style="text-align: center; padding: 16px;">
        <div style="background: #7C3AED22; width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 12px auto; font-size: 1.3rem;">1</div>
        <h4 style="color: #E2E8F0; margin: 0;">Search</h4>
        <p style="color: #94A3B8; font-size: 0.85rem;">Scans LinkedIn, Indeed, Glassdoor & ZipRecruiter via Google Jobs</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="text-align: center; padding: 16px;">
        <div style="background: #7C3AED22; width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 12px auto; font-size: 1.3rem;">2</div>
        <h4 style="color: #E2E8F0; margin: 0;">Score</h4>
        <p style="color: #94A3B8; font-size: 0.85rem;">AI evaluates each job against Yinka's profile & preferences</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="text-align: center; padding: 16px;">
        <div style="background: #7C3AED22; width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 12px auto; font-size: 1.3rem;">3</div>
        <h4 style="color: #E2E8F0; margin: 0;">Generate</h4>
        <p style="color: #94A3B8; font-size: 0.85rem;">Creates tailored cover letters highlighting matching experience</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div style="text-align: center; padding: 16px;">
        <div style="background: #7C3AED22; width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 12px auto; font-size: 1.3rem;">4</div>
        <h4 style="color: #E2E8F0; margin: 0;">Apply</h4>
        <p style="color: #94A3B8; font-size: 0.85rem;">Direct links to apply with generated cover letter ready to go</p>
    </div>
    """, unsafe_allow_html=True)
