"""
Yinka Job Bot — AI Cover Letter Generator
Uses Anthropic Claude, Google Gemini, or OpenAI to generate tailored cover letters.
"""

import json
from datetime import datetime
from fpdf import FPDF
from pathlib import Path
from config import (
    AI_PROVIDER, GEMINI_API_KEY, GEMINI_MODEL,
    OPENAI_API_KEY, OPENAI_MODEL,
    ANTHROPIC_API_KEY, ANTHROPIC_MODEL,
    RESUME_TEXT_PATH,
    CANDIDATE_NAME, CANDIDATE_EMAIL, CANDIDATE_PHONE, CANDIDATE_LOCATION,
    BASE_DIR,
)
from src.database import insert_cover_letter, get_cover_letter


def _load_resume():
    """Load resume text."""
    try:
        return RESUME_TEXT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "Resume not found."


def _build_cover_letter_prompt(job, resume, tone="professional"):
    """Build cover letter prompt (shared between providers)."""
    tone_instructions = {
        "professional": "Write in a warm, professional tone that feels personal and genuine—not stiff or overly formal. Mirror the conversational yet competent voice of the resume.",
        "enthusiastic": "Write with genuine enthusiasm and energy, highlighting excitement about the role while remaining professional.",
        "concise": "Write a concise, impactful cover letter—no more than 3 short paragraphs. Every sentence should add value.",
    }

    return f"""You are an expert career coach and cover letter writer. Write a tailored cover letter for the following job posting based on the candidate's resume.

## Candidate Information:
- Name: {CANDIDATE_NAME}
- Email: {CANDIDATE_EMAIL}
- Phone: {CANDIDATE_PHONE}
- Location: {CANDIDATE_LOCATION}

## Candidate Resume:
{resume}

## Target Job:
- Title: {job.get('title', 'N/A')}
- Company: {job.get('company', 'N/A')}
- Location: {job.get('location', 'N/A')}
- Description:
{job.get('description', 'No description available')[:4000]}

## Writing Instructions:
{tone_instructions.get(tone, tone_instructions['professional'])}

## Key Requirements:
1. Open with a strong, specific hook mentioning the exact role and company
2. Highlight 3-4 specific achievements/experiences from the resume that DIRECTLY match the job requirements
3. Emphasize her UKG Pro WFM expertise (Analytics, Data Hub, Healthcare Productivity) as her differentiator
4. Mention her cross-functional collaboration experience (HR, Payroll, Finance, IT)
5. Reference specific compliance knowledge (FLSA, HIPAA, ACA, ERISA) if the job mentions compliance
6. Close with a confident call to action
7. Keep it to 3-4 paragraphs maximum
8. Do NOT use generic phrases like "I am writing to express my interest" — be specific and engaging
9. Do NOT include a header with address/date — just the body of the letter starting with "Dear"
10. Sign off with "{CANDIDATE_NAME}"

Write ONLY the cover letter text, nothing else."""


def _generate_with_gemini(prompt):
    """Generate text using Google Gemini API."""
    from google import genai

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set. Add it to your .env file.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config={
            "temperature": 0.7,
            "max_output_tokens": 1500,
        },
    )

    return response.text


def _generate_with_openai(prompt):
    """Generate text using OpenAI API (fallback)."""
    from openai import OpenAI

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set. Add it to your .env file.")

    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are an expert career coach who writes compelling, personalized cover letters."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1500,
    )

    return response.choices[0].message.content


def _generate_with_anthropic(prompt):
    """Generate text using Anthropic Claude API."""
    import anthropic

    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set. Add it to your .env file.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1500,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )

    return response.content[0].text


def generate_cover_letter(job, tone="professional"):
    """
    Generate a tailored cover letter for a specific job posting.

    Args:
        job: Dictionary with job details
        tone: Writing tone ("professional", "enthusiastic", "concise")

    Returns:
        Generated cover letter text
    """
    resume = _load_resume()
    prompt = _build_cover_letter_prompt(job, resume, tone)

    try:
        if AI_PROVIDER == "anthropic":
            cover_letter = _generate_with_anthropic(prompt)
        elif AI_PROVIDER == "gemini":
            cover_letter = _generate_with_gemini(prompt)
        else:
            cover_letter = _generate_with_openai(prompt)

        cover_letter = cover_letter.strip()

        # Save to database
        cl_id = insert_cover_letter(job["id"], cover_letter, tone)

        print(f"Cover letter generated for: {job['title']} at {job['company']}")
        return cover_letter

    except Exception as e:
        error_msg = f"Error generating cover letter: {str(e)}"
        print(f"ERROR: {error_msg}")
        return None


def generate_cover_letter_pdf(cover_letter_text, job, output_dir=None):
    """
    Generate a PDF version of the cover letter.

    Args:
        cover_letter_text: The cover letter content
        job: Job dictionary for naming
        output_dir: Directory to save the PDF

    Returns:
        Path to the generated PDF
    """
    output_dir = Path(output_dir) if output_dir else BASE_DIR / "cover_letters"
    output_dir.mkdir(exist_ok=True)

    # Clean filename
    company = "".join(c for c in job.get("company", "Company") if c.isalnum() or c in " -_")
    title = "".join(c for c in job.get("title", "Role") if c.isalnum() or c in " -_")
    filename = f"Cover_Letter_{company}_{title}.pdf"
    filepath = output_dir / filename

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=25)

    # Header
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, CANDIDATE_NAME, ln=True, align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"{CANDIDATE_LOCATION}  |  {CANDIDATE_PHONE}  |  {CANDIDATE_EMAIL}", ln=True, align="C")
    pdf.ln(3)

    # Date
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, datetime.now().strftime("%B %d, %Y"), ln=True)
    pdf.ln(3)

    # Divider
    pdf.set_draw_color(124, 58, 237)  # Purple accent
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    # Body
    pdf.set_font("Helvetica", "", 11)

    # Handle encoding issues
    safe_text = cover_letter_text.encode('latin-1', 'replace').decode('latin-1')

    for paragraph in safe_text.split('\n\n'):
        paragraph = paragraph.strip()
        if paragraph:
            pdf.multi_cell(0, 6, paragraph)
            pdf.ln(4)

    pdf.output(str(filepath))
    print(f"PDF saved: {filepath}")
    return filepath


def regenerate_cover_letter(job, tone="professional"):
    """Regenerate a cover letter with a different tone."""
    return generate_cover_letter(job, tone)
