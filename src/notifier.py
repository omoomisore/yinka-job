"""
Yinka Job Bot — Email Notification Sender
Sends job search summaries and application notifications via email.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
from pathlib import Path
from config import SMTP_EMAIL, SMTP_PASSWORD, NOTIFICATION_EMAIL, CANDIDATE_NAME


def send_email(subject, body_html, attachments=None):
    """
    Send an email notification.
    
    Args:
        subject: Email subject line
        body_html: HTML email body
        attachments: List of file paths to attach
    
    Returns:
        True if sent successfully, False otherwise
    """
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("⚠️ Email not configured. Set SMTP_EMAIL and SMTP_PASSWORD in .env")
        return False

    msg = MIMEMultipart()
    msg["From"] = SMTP_EMAIL
    msg["To"] = NOTIFICATION_EMAIL
    msg["Subject"] = subject

    msg.attach(MIMEText(body_html, "html"))

    # Add attachments
    if attachments:
        for filepath in attachments:
            path = Path(filepath)
            if path.exists():
                with open(path, "rb") as f:
                    attachment = MIMEApplication(f.read(), _subtype=path.suffix[1:])
                    attachment.add_header(
                        "Content-Disposition", "attachment", filename=path.name
                    )
                    msg.attach(attachment)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        print(f"✅ Email sent: {subject}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


def send_new_jobs_digest(jobs, search_summary=None):
    """
    Send a digest of newly found high-scoring jobs.
    
    Args:
        jobs: List of job dictionaries (should be high-scoring ones)
        search_summary: Optional search summary dict
    """
    if not jobs:
        return

    now = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
    # Build job cards HTML
    job_cards = ""
    for job in jobs:
        score = job.get("relevance_score", 0)
        if score >= 80:
            score_color = "#22C55E"
            score_label = "Strong Match"
        elif score >= 60:
            score_color = "#EAB308"
            score_label = "Good Match"
        else:
            score_color = "#F97316"
            score_label = "Weak Match"

        apply_link = job.get("apply_url", "#")
        
        job_cards += f"""
        <div style="background: #1E1E2E; border-radius: 12px; padding: 20px; margin-bottom: 16px; border-left: 4px solid {score_color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h3 style="margin: 0; color: #E2E8F0; font-size: 16px;">{job.get('title', 'N/A')}</h3>
                <span style="background: {score_color}22; color: {score_color}; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                    {score} — {score_label}
                </span>
            </div>
            <p style="margin: 4px 0; color: #94A3B8; font-size: 14px;">
                🏢 {job.get('company', 'N/A')} &nbsp;|&nbsp; 📍 {job.get('location', 'N/A')}
            </p>
            {f'<p style="margin: 4px 0; color: #A78BFA; font-size: 13px;">💰 {job["salary_info"]}</p>' if job.get('salary_info') else ''}
            <a href="{apply_link}" style="display: inline-block; margin-top: 10px; background: #7C3AED; color: white; text-decoration: none; padding: 8px 16px; border-radius: 8px; font-size: 13px;">
                View & Apply →
            </a>
        </div>
        """

    # Summary stats
    summary_html = ""
    if search_summary:
        summary_html = f"""
        <div style="background: #1E1E2E; border-radius: 12px; padding: 16px; margin-bottom: 24px;">
            <p style="margin: 4px 0; color: #94A3B8;">🔍 Queries run: <strong style="color: #E2E8F0;">{search_summary.get('queries_run', 0)}</strong></p>
            <p style="margin: 4px 0; color: #94A3B8;">📋 Total found: <strong style="color: #E2E8F0;">{search_summary.get('total_found', 0)}</strong></p>
            <p style="margin: 4px 0; color: #94A3B8;">✨ New jobs: <strong style="color: #22C55E;">{search_summary.get('total_new', 0)}</strong></p>
            <p style="margin: 4px 0; color: #94A3B8;">🔄 Duplicates: <strong style="color: #94A3B8;">{search_summary.get('total_duplicate', 0)}</strong></p>
        </div>
        """

    body_html = f"""
    <html>
    <body style="background: #0F0F1A; color: #E2E8F0; font-family: 'Segoe UI', Arial, sans-serif; padding: 24px;">
        <div style="max-width: 600px; margin: 0 auto;">
            <h1 style="color: #A78BFA; font-size: 24px; margin-bottom: 4px;">🎯 Yinka Job Bot</h1>
            <p style="color: #64748B; margin-top: 0; margin-bottom: 24px;">{now}</p>
            
            <h2 style="color: #E2E8F0; font-size: 18px; margin-bottom: 16px;">
                {len(jobs)} New Job{'' if len(jobs) == 1 else 's'} Found
            </h2>
            
            {summary_html}
            {job_cards}
            
            <p style="color: #64748B; font-size: 12px; margin-top: 32px; text-align: center;">
                Yinka Job Bot • Automated Job Search for {CANDIDATE_NAME}
            </p>
        </div>
    </body>
    </html>
    """

    subject = f"🎯 {len(jobs)} New Job Match{'es' if len(jobs) != 1 else ''} Found — Yinka Job Bot"
    send_email(subject, body_html)


def send_application_confirmation(job, cover_letter_text=None):
    """Send a confirmation that an application was submitted."""
    now = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # Score display
    score = job.get("relevance_score", 0)
    if score >= 80:
        score_color, score_label = "#22C55E", "Strong Match"
    elif score >= 60:
        score_color, score_label = "#EAB308", "Good Match"
    else:
        score_color, score_label = "#F97316", "Weak Match"

    # Cover letter section
    cl_section = ""
    if cover_letter_text:
        cl_html = cover_letter_text.replace("\n", "<br>")
        cl_section = f"""
        <div style="background: #1E1E2E; border-radius: 12px; padding: 20px; margin-top: 16px;">
            <h3 style="color: #A78BFA; margin-top: 0;">📝 Cover Letter Submitted</h3>
            <div style="color: #CBD5E1; font-size: 14px; line-height: 1.6;">
                {cl_html}
            </div>
        </div>
        """

    apply_link = job.get("apply_url", "#")

    body_html = f"""
    <html>
    <body style="background: #0F0F1A; color: #E2E8F0; font-family: 'Segoe UI', Arial, sans-serif; padding: 24px;">
        <div style="max-width: 600px; margin: 0 auto;">
            <h1 style="color: #22C55E; font-size: 24px;">✅ Application Submitted</h1>
            <p style="color: #64748B;">{now}</p>
            
            <div style="background: #1E1E2E; border-radius: 12px; padding: 20px; margin-top: 16px; border-left: 4px solid {score_color};">
                <h2 style="color: #E2E8F0; margin-top: 0; font-size: 18px;">{job.get('title', 'N/A')}</h2>
                <p style="color: #94A3B8; margin: 4px 0;">🏢 {job.get('company', 'N/A')}</p>
                <p style="color: #94A3B8; margin: 4px 0;">📍 {job.get('location', 'N/A')}</p>
                <p style="margin: 8px 0;">
                    <span style="background: {score_color}22; color: {score_color}; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: bold;">
                        Score: {score} — {score_label}
                    </span>
                </p>
                {f'<p style="color: #A78BFA; margin: 4px 0;">💰 {job["salary_info"]}</p>' if job.get("salary_info") else ""}
                <a href="{apply_link}" style="display: inline-block; margin-top: 12px; color: #A78BFA; font-size: 13px; text-decoration: underline;">
                    View Original Posting →
                </a>
            </div>
            
            {cl_section}
            
            <div style="background: #1E1E2E; border-radius: 12px; padding: 16px; margin-top: 16px;">
                <h3 style="color: #E2E8F0; margin-top: 0; font-size: 14px;">📋 Info Submitted</h3>
                <p style="color: #94A3B8; margin: 2px 0; font-size: 13px;">Name: {CANDIDATE_NAME}</p>
                <p style="color: #94A3B8; margin: 2px 0; font-size: 13px;">Email: olaomi@gmail.com</p>
                <p style="color: #94A3B8; margin: 2px 0; font-size: 13px;">Phone: 410-800-3346</p>
                <p style="color: #94A3B8; margin: 2px 0; font-size: 13px;">Location: Potomac, MD</p>
            </div>
            
            <p style="color: #64748B; font-size: 12px; margin-top: 32px; text-align: center;">
                Yinka Job Bot • Automated Job Search for {CANDIDATE_NAME}
            </p>
        </div>
    </body>
    </html>
    """

    subject = f"✅ Applied: {job.get('title', 'Role')} at {job.get('company', 'Company')}"
    send_email(subject, body_html)
