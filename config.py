"""
Yinka Job Bot — Configuration
Central configuration for job search criteria, profile, and application preferences.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# ============================================================
# Paths
# ============================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RESUME_DIR = BASE_DIR / "resume"
DATA_DIR.mkdir(exist_ok=True)
RESUME_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "jobs.db"
RESUME_TEXT_PATH = RESUME_DIR / "yinka_resume.txt"
RESUME_PDF_PATH = RESUME_DIR / "yinka_resume.pdf"

# ============================================================
# API Keys
# ============================================================
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "olaomi@gmail.com")

# AI Provider: "anthropic", "gemini", or "openai"
AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic")

# ============================================================
# Candidate Profile
# ============================================================
CANDIDATE_NAME = "Yinka Omisore"
CANDIDATE_EMAIL = "olaomi@gmail.com"
CANDIDATE_PHONE = "410-800-3346"
CANDIDATE_LOCATION = "Potomac, MD"

# ============================================================
# Job Search Configuration
# ============================================================
SEARCH_QUERIES = [
    "UKG Pro WFM Analyst",
    "UKG Workforce Management Analyst",
    "HRIS Analyst UKG",
    "Workforce Management Consultant UKG",
    "Payroll Systems Analyst Healthcare",
    "Business Systems Analyst HR WFM",
    "UKG Pro Analyst",
    "UKG Implementation Consultant",
    "UKG Pro Consultant",
    "Workforce Management Analyst HRIS",
    "UKG Data Hub Analyst",
    "HR Technology Analyst UKG",
]

# Location preferences
SEARCH_LOCATION = "Washington, DC"  # SerpAPI location anchor
MAX_DISTANCE_MILES = 40  # From Potomac, MD

LOCATION_PREFERENCES = {
    "remote": True,         # Strongly preferred
    "hybrid": True,         # Open to it
    "onsite": True,         # Open if within distance
    "preferred_areas": [
        "Potomac, MD",
        "Rockville, MD",
        "Bethesda, MD",
        "Silver Spring, MD",
        "Washington, DC",
        "Arlington, VA",
        "Tysons, VA",
        "Reston, VA",
        "McLean, VA",
        "Columbia, MD",
        "Baltimore, MD",
        "Gaithersburg, MD",
        "Fairfax, VA",
    ],
}

# Keywords that MUST appear (at least some) for a good match
INCLUDE_KEYWORDS = [
    "UKG", "UKG Pro", "WFM", "Workforce Management",
    "HRIS", "Workforce Analytics", "Data Hub",
    "Timekeeping", "Scheduling", "Labor Optimization",
    "Pay Rules", "Accruals", "Payroll Systems",
    "HR Technology", "Workforce Productivity",
    "Kronos",  # Legacy name for UKG
]

# Keywords that signal the job is NOT a good fit
EXCLUDE_KEYWORDS = [
    "software engineer", "software developer",
    "data engineer", "python developer",
    "java developer", "devops engineer",
    "full stack developer", "front end developer",
    "back end developer", "machine learning engineer",
    "SRE", "site reliability", "platform engineer",
    "cloud engineer", "infrastructure engineer",
    "iOS developer", "Android developer",
    "Boomi developer",  # She supports Boomi integrations but isn't a dev
]

# Desired job description themes
JOB_DESCRIPTION_THEMES = [
    "UKG / WFM System Ownership (Analytics, Data Hub, Productivity)",
    "Timekeeping, scheduling, labor optimization configuration",
    "Pay rules, accruals, job codes configuration",
    "Workforce analytics and dashboards",
    "Labor cost analysis and executive reporting",
    "Cross-functional collaboration (HR, Payroll, Finance, IT)",
    "Translating business needs into system solutions",
    "Healthcare or regulated environment compliance",
    "FLSA, HIPAA, ACA, ERISA, OSHA compliance",
    "Process improvement and workflow optimization",
]

# ============================================================
# AI Scoring Configuration
# ============================================================
SCORING_WEIGHTS = {
    "ukg_wfm_match": 0.30,       # UKG Pro WFM, Analytics, Data Hub involvement
    "skills_alignment": 0.25,     # Match with her core skills
    "experience_fit": 0.15,       # Experience level appropriateness
    "healthcare_regulated": 0.10, # Healthcare or regulated industry (preferred)
    "role_type": 0.10,            # Analyst/Consultant vs. engineering
    "location_fit": 0.10,         # Remote, or within DC metro area
}

SCORE_THRESHOLDS = {
    "strong_match": 80,   # Auto-recommend
    "good_match": 60,     # Worth reviewing
    "weak_match": 40,     # Probably skip
    "skip": 0,            # Don't bother
}

# ============================================================
# AI Model Configuration
# ============================================================
# OpenAI (fallback)
OPENAI_MODEL = "gpt-4o"
OPENAI_SCORING_MODEL = "gpt-4o-mini"

# Gemini (backup)
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_SCORING_MODEL = "gemini-2.0-flash"

# Anthropic Claude (primary)
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"  # Best for cover letter generation
ANTHROPIC_SCORING_MODEL = "claude-haiku-4-5-20251001"  # Fast & cheap for bulk scoring

# ============================================================
# Application Preferences
# ============================================================
SEARCH_INTERVAL_HOURS = 6  # How often to auto-search
MAX_APPLICATIONS_PER_DAY = 10  # Safety limit
NOTIFICATION_ENABLED = True
