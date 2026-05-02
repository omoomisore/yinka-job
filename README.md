# 🎯 Yinka Job Bot

Automated job search, AI scoring, and one-click application assistant for UKG Pro WFM & HRIS roles.

## Features

- 🔍 **Multi-Board Search** — Searches LinkedIn, Indeed, Glassdoor, ZipRecruiter via Google Jobs API
- 🤖 **AI Scoring** — Claude AI evaluates each job's relevance (0-100 score with reasoning)
- 📄 **Cover Letter Generation** — Tailored cover letters generated per position via Claude
- 🚀 **One-Click Apply** — Playwright browser automation fills forms and submits autonomously
- 📈 **Dashboard** — Visual analytics with KPIs, charts, and pipeline tracking
- 📧 **Email Notifications** — Application confirmations and new match digests
- 📍 **Location Filter** — 30-40 mile radius from Potomac, MD (+ remote)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### 2. Configure API Keys

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

Required keys:
- **Anthropic API Key** — [console.anthropic.com](https://console.anthropic.com) (primary AI)
- **SerpAPI Key** — [serpapi.com](https://serpapi.com) (job search)
- **Gmail App Password** — For email notifications

### 3. Add Your Resume

Place your resume files in the `resume/` directory:
- `resume/yinka_resume.txt` — Plain text version (for AI scoring)
- `resume/yinka_resume.pdf` — PDF version (for uploads)

### 4. Launch Dashboard

```bash
streamlit run app.py
```

### 5. Apply to Jobs

1. Go to **Job Search** → Click **Search Now**
2. Click **Score Jobs** to AI-rank results
3. Click **🚀 Apply** on any job
4. Review the confirmation → **Confirm & Apply**
5. Watch the bot fill and submit the application autonomously

## Project Structure

```
yinka-job/
├── app.py                  # Main Streamlit app
├── config.py               # Configuration & search criteria
├── requirements.txt        # Dependencies
├── .env.example            # Environment variable template
├── .streamlit/config.toml  # Dark theme config
├── data/
│   ├── jobs.db             # SQLite database
│   └── screenshots/        # Application proof screenshots
├── resume/                 # Resume files (not tracked)
├── src/
│   ├── database.py         # Database layer (SQLite)
│   ├── job_search.py       # SerpAPI search engine + location filter
│   ├── job_scorer.py       # AI job scorer (Claude / Gemini / OpenAI)
│   ├── cover_letter.py     # AI cover letter generator
│   ├── auto_apply.py       # Playwright browser automation engine
│   ├── notifier.py         # Email notification system
│   └── scheduler.py        # Background job scheduler
└── pages/                  # Streamlit pages
    ├── 1_📊_Dashboard.py
    ├── 2_🔍_Job_Search.py
    ├── 3_📋_Applications.py
    ├── 4_📄_Cover_Letters.py
    └── 5_⚙️_Settings.py
```

## AI Providers

| Provider | Models | Role |
|----------|--------|------|
| **Anthropic Claude** (primary) | `claude-haiku-4-5` / `claude-sonnet-4` | Scoring + cover letters |
| Google Gemini (backup) | `gemini-2.0-flash` | Free fallback |
| OpenAI (backup) | `gpt-4o-mini` / `gpt-4o` | Paid fallback |

## Auto-Apply Pipeline

When you click **Apply**, the bot autonomously:

1. Opens a Chromium browser to the job listing
2. Finds and clicks the "Apply Now" button on the site
3. Auto-fills: Name, Email, Phone, Location, Resume, Cover Letter
4. Clicks Submit
5. Takes screenshot proof at each step
6. Sends you a confirmation email
7. Updates the dashboard

## Search Criteria

- **Target Roles**: UKG Pro WFM Analyst, HRIS Analyst, Workforce Management Consultant
- **Location**: Remote (preferred), or DC/MD/VA metro area (within 40 miles of Potomac, MD 20854)
- **Include**: UKG, WFM, HRIS, workforce analytics, timekeeping, scheduling
- **Exclude**: Software engineering, data engineering, heavy coding roles

## License

Private — For personal use only.
