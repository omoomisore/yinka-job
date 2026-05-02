"""
Yinka Job Bot — AI Job Relevance Scorer
Uses Anthropic Claude, Google Gemini, or OpenAI to score each job's relevance to Yinka's profile.
"""

import json
import re
import time
from config import (
    AI_PROVIDER,
    GEMINI_API_KEY, GEMINI_SCORING_MODEL,
    OPENAI_API_KEY, OPENAI_SCORING_MODEL,
    ANTHROPIC_API_KEY, ANTHROPIC_SCORING_MODEL,
    RESUME_TEXT_PATH, INCLUDE_KEYWORDS, EXCLUDE_KEYWORDS,
    JOB_DESCRIPTION_THEMES, LOCATION_PREFERENCES, SCORE_THRESHOLDS,
)
from src.database import get_unscored_jobs, update_job_score


def _load_resume():
    """Load resume text."""
    try:
        return RESUME_TEXT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "Resume not found."


def _build_scoring_prompt(job, resume):
    """Build the scoring prompt (shared between providers)."""
    return f"""You are an expert job matching assistant. Analyze how well this job matches the candidate's profile.

## Candidate Profile (Resume):
{resume}

## Candidate Preferences:
- Looking for: UKG Pro WFM Analyst/Consultant, HRIS Analyst, Workforce Management Analyst, Payroll Systems Analyst (Healthcare preferred), Business Systems Analyst (HR/WFM domain)
- Preferred location: Remote (strongly preferred), or Hybrid/On-site within 30-40 miles of Potomac, MD (ZIP 20854, DC/MD/VA area)
- Preferred areas: {', '.join(LOCATION_PREFERENCES['preferred_areas'])}
- Desired themes in job description: {', '.join(JOB_DESCRIPTION_THEMES)}
- Should NOT be heavily coding-focused (no software engineering, data engineering, Python/Java dev roles)
- Keywords to look for: {', '.join(INCLUDE_KEYWORDS[:15])}
- Red flag keywords: {', '.join(EXCLUDE_KEYWORDS[:15])}

## Job to Evaluate:
- Title: {job.get('title', 'N/A')}
- Company: {job.get('company', 'N/A')}
- Location: {job.get('location', 'N/A')}
- Job Type: {job.get('job_type', 'N/A')}
- Salary: {job.get('salary_info', 'N/A')}
- Description:
{job.get('description', 'No description available')[:3000]}

## Scoring Criteria (weights):
1. UKG/WFM Match (30%): Does it involve UKG Pro WFM, Analytics, Data Hub, Kronos?
2. Skills Alignment (25%): Does it match her core skills (timekeeping, scheduling, pay rules, accruals, reporting)?
3. Experience Fit (15%): Does her 10+ years of experience match the seniority level?
4. Healthcare/Regulated (10%): Is it in healthcare or a regulated environment? (Bonus, not required)
5. Role Type (10%): Is it an Analyst/Consultant role vs. a coding/engineering role?
6. Location Fit (10%): Remote, or within 30-40 miles of Potomac, MD (DC metro area)?

## Required Output Format (JSON only, no markdown fences):
{{"score": <integer 0-100>, "recommendation": "<Strong Match|Good Match|Weak Match|Skip>", "reasoning": ["<bullet point 1>", "<bullet point 2>", "<bullet point 3>"], "red_flags": ["<any concerns, or empty list>"], "matching_skills": ["<skills from resume that match>"]}}

Respond ONLY with valid JSON. No other text, no markdown code fences."""


def _score_with_gemini(prompt, max_retries=3):
    """Score a job using Google Gemini API with retry logic."""
    from google import genai

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set. Add it to your .env file.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_SCORING_MODEL,
                contents=prompt,
                config={
                    "temperature": 0.2,
                    "max_output_tokens": 800,
                    "response_mime_type": "application/json",
                },
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "503" in error_str:
                wait = (attempt + 1) * 15  # 15s, 30s, 45s
                print(f"      Rate limited, waiting {wait}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait)
            else:
                raise
    raise Exception("Max retries exceeded for Gemini API")


def _score_with_openai(prompt):
    """Score a job using OpenAI API (fallback)."""
    from openai import OpenAI

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set. Add it to your .env file.")

    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model=OPENAI_SCORING_MODEL,
        messages=[
            {"role": "system", "content": "You are a precise job matching assistant that outputs only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=800,
        response_format={"type": "json_object"},
    )

    return response.choices[0].message.content


def _score_with_anthropic(prompt):
    """Score a job using Anthropic Claude API."""
    import anthropic

    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set. Add it to your .env file.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=ANTHROPIC_SCORING_MODEL,
        max_tokens=800,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    return response.content[0].text


def score_job(job):
    """
    Score a single job's relevance to Yinka's profile.

    Args:
        job: Dictionary with job details (title, company, description, location, etc.)

    Returns:
        Dictionary with score (0-100), reasoning, red_flags, recommendation
    """
    resume = _load_resume()
    prompt = _build_scoring_prompt(job, resume)

    try:
        if AI_PROVIDER == "anthropic":
            raw_response = _score_with_anthropic(prompt)
        elif AI_PROVIDER == "gemini":
            raw_response = _score_with_gemini(prompt)
        else:
            raw_response = _score_with_openai(prompt)

        # Clean response (remove markdown fences if present)
        clean = raw_response.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()

        result = json.loads(clean)

        # Validate score range
        result["score"] = max(0, min(100, int(result.get("score", 0))))

        # Ensure recommendation is valid
        valid_recs = ["Strong Match", "Good Match", "Weak Match", "Skip"]
        if result.get("recommendation") not in valid_recs:
            if result["score"] >= SCORE_THRESHOLDS["strong_match"]:
                result["recommendation"] = "Strong Match"
            elif result["score"] >= SCORE_THRESHOLDS["good_match"]:
                result["recommendation"] = "Good Match"
            elif result["score"] >= SCORE_THRESHOLDS["weak_match"]:
                result["recommendation"] = "Weak Match"
            else:
                result["recommendation"] = "Skip"

        return result

    except Exception as e:
        print(f"Error scoring job '{job.get('title', '?')}': {e}")
        return {
            "score": 0,
            "recommendation": "Error",
            "reasoning": [f"Scoring failed: {str(e)}"],
            "red_flags": ["Could not evaluate"],
            "matching_skills": [],
        }


def score_all_unscored():
    """
    Score all jobs that haven't been scored yet.

    Returns:
        Dictionary with scoring summary
    """
    unscored = get_unscored_jobs()

    if not unscored:
        print("All jobs are already scored.")
        return {"scored": 0, "errors": 0}

    print(f"Scoring {len(unscored)} jobs using {AI_PROVIDER.upper()}...")
    scored = 0
    errors = 0

    for i, job in enumerate(unscored, 1):
        print(f"   [{i}/{len(unscored)}] {job['title']} at {job['company']}...")

        result = score_job(job)

        if result.get("recommendation") != "Error":
            reasoning_text = json.dumps({
                "recommendation": result["recommendation"],
                "reasoning": result.get("reasoning", []),
                "red_flags": result.get("red_flags", []),
                "matching_skills": result.get("matching_skills", []),
            })
            update_job_score(job["id"], result["score"], reasoning_text)
            scored += 1

            emoji = "STRONG" if result["score"] >= 80 else "GOOD" if result["score"] >= 60 else "WEAK"
            print(f"      [{emoji}] Score: {result['score']} - {result['recommendation']}")
        else:
            errors += 1
            print(f"      [FAIL] Scoring failed")

        # Rate limit: wait between jobs (Gemini free = 15 RPM for 2.0-flash)
        if AI_PROVIDER == "gemini" and i < len(unscored):
            time.sleep(5)

    print(f"\nScoring complete: {scored} scored, {errors} errors")
    return {"scored": scored, "errors": errors}


def get_score_display(score):
    """Get a display-friendly score with color indicator."""
    if score >= SCORE_THRESHOLDS["strong_match"]:
        return {"label": "Strong Match", "color": "#22C55E", "emoji": "🟢"}
    elif score >= SCORE_THRESHOLDS["good_match"]:
        return {"label": "Good Match", "color": "#EAB308", "emoji": "🟡"}
    elif score >= SCORE_THRESHOLDS["weak_match"]:
        return {"label": "Weak Match", "color": "#F97316", "emoji": "🟠"}
    else:
        return {"label": "Skip", "color": "#EF4444", "emoji": "🔴"}
