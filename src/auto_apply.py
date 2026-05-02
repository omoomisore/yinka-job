"""
Yinka Job Bot — Auto-Apply Engine
Uses Playwright browser automation to FULLY apply to jobs autonomously.
Works both locally (visible browser) and in the cloud (headless with screenshots).
"""

import sys
import os
import time
import re
import json
import subprocess
from datetime import datetime
from pathlib import Path
from config import (
    CANDIDATE_NAME, CANDIDATE_EMAIL, CANDIDATE_PHONE, CANDIDATE_LOCATION,
    RESUME_PDF_PATH, MAX_APPLICATIONS_PER_DAY, IS_CLOUD, DATA_DIR,
)
from src.database import insert_application, update_job_status, get_all_applications, get_cover_letter
from src.notifier import send_application_confirmation


# Directory for screenshots
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Candidate info for form filling
CANDIDATE_INFO = {
    "name": CANDIDATE_NAME,
    "first_name": CANDIDATE_NAME.split()[0] if CANDIDATE_NAME else "",
    "last_name": CANDIDATE_NAME.split()[-1] if CANDIDATE_NAME else "",
    "email": CANDIDATE_EMAIL,
    "phone": CANDIDATE_PHONE,
    "location": CANDIDATE_LOCATION,
    "city": "Potomac",
    "state": "MD",
    "zip": "20854",
    "country": "United States",
}

# Common field patterns for auto-detection
FIELD_PATTERNS = {
    "first_name": ["first.?name", "given.?name", "fname", "first"],
    "last_name": ["last.?name", "family.?name", "lname", "surname", "last"],
    "name": ["full.?name", "your.?name", "applicant.?name", "^name$"],
    "email": ["e?.?mail", "email.?address"],
    "phone": ["phone", "mobile", "telephone", "cell", "contact.?number"],
    "location": ["location", "city.?state", "address"],
    "city": ["^city$"],
    "state": ["^state$", "province"],
    "zip": ["zip", "postal"],
    "cover_letter": ["cover.?letter", "letter", "message", "why.?apply", "additional.?info"],
}

# Selectors to find the "Apply" button on job listing pages
APPLY_BUTTON_SELECTORS = [
    "a:has-text('APPLY for this job')",
    "a:has-text('Apply Now')",
    "a:has-text('Apply for this job')",
    "a:has-text('Easy Apply')",
    "a:has-text('Apply on company site')",
    "button:has-text('APPLY for this job')",
    "button:has-text('Apply Now')",
    "button:has-text('Apply for this job')",
    "button:has-text('Apply')",
    "button:has-text('Easy Apply')",
    "a.apply-button",
    "a[class*='apply']",
    "button[class*='apply']",
    "[data-testid='apply-button']",
    "a:has-text('Submit Application')",
    "a:has-text('Start Application')",
]

# Selectors to find the final Submit button on application forms
SUBMIT_BUTTON_SELECTORS = [
    "button[type='submit']",
    "input[type='submit']",
    "button:has-text('Submit Application')",
    "button:has-text('Submit')",
    "button:has-text('Send Application')",
    "button:has-text('Apply Now')",
    "button:has-text('Complete Application')",
    "button:has-text('Send')",
    "a:has-text('Submit Application')",
    "input[value='Submit']",
    "input[value='Apply']",
]


def _ensure_playwright_installed():
    """Install Playwright browsers if not already installed (needed for cloud)."""
    if IS_CLOUD:
        browser_path = Path.home() / ".cache" / "ms-playwright"
        if not browser_path.exists():
            print("📦 Installing Playwright Chromium (first run)...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "playwright", "install", "chromium"],
                    check=True,
                    capture_output=True,
                    timeout=120,
                )
                print("✅ Playwright Chromium installed!")
            except Exception as e:
                print(f"⚠️ Could not install Playwright: {e}")
                return False
    return True


def check_daily_limit():
    """Check if we've hit the daily application limit."""
    today = datetime.now().strftime("%Y-%m-%d")
    apps = get_all_applications()
    today_count = sum(1 for a in apps if a.get("applied_at", "").startswith(today))
    return today_count < MAX_APPLICATIONS_PER_DAY, today_count


def _match_field(element_text, field_type):
    """Check if an element's text/attributes match a field type."""
    text = element_text.lower().strip()
    for pattern in FIELD_PATTERNS.get(field_type, []):
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _take_screenshot(page, stage, job):
    """Take a timestamped screenshot."""
    company = "".join(c for c in job.get("company", "Co")[:20] if c.isalnum() or c in " -_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{company}_{stage}.png"
    filepath = SCREENSHOTS_DIR / filename
    try:
        page.screenshot(path=str(filepath), full_page=False)
        print(f"  📸 Screenshot: {filename}")
        return str(filepath)
    except Exception as e:
        print(f"  ⚠️ Screenshot failed: {e}")
        return None


def launch_browser_and_apply(job, cover_letter_text=None):
    """
    Launch a browser and FULLY apply to the job autonomously.
    - Local: visible browser, user can watch
    - Cloud: headless browser, screenshots shown in UI

    Args:
        job: Job dictionary
        cover_letter_text: Pre-generated cover letter text

    Returns:
        Dictionary with results including screenshots
    """
    # Ensure Playwright is installed
    if not _ensure_playwright_installed():
        return {
            "success": False, "submitted": False,
            "message": "Playwright not available. Use the Apply URL directly.",
            "fields_filled": 0, "screenshots": [],
        }

    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

    apply_url = job.get("apply_url")
    if not apply_url:
        return {"success": False, "submitted": False, "message": "No application URL.",
                "fields_filled": 0, "screenshots": []}

    result = {
        "success": False,
        "submitted": False,
        "message": "",
        "fields_filled": 0,
        "screenshots": [],
    }

    # Cloud = headless, Local = visible
    headless = IS_CLOUD

    try:
        with sync_playwright() as p:
            print(f"\n{'='*60}")
            print(f"🚀 AUTO-APPLY: {job.get('title')}")
            print(f"   Company: {job.get('company')}")
            print(f"   Mode: {'☁️ Cloud (headless)' if headless else '🖥️ Local (visible)'}")
            print(f"   URL: {apply_url}")
            print(f"{'='*60}")

            browser = p.chromium.launch(
                headless=headless,
                slow_mo=200 if not headless else 50,
            )

            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            )

            page = context.new_page()

            try:
                # ── STEP 1: Open the job listing page ──
                print("\n📄 Step 1: Opening job listing page...")
                page.goto(apply_url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(3)

                ss = _take_screenshot(page, "1_listing", job)
                if ss:
                    result["screenshots"].append(ss)

                # ── STEP 2: Find and click the Apply button on the site ──
                print("\n🔍 Step 2: Looking for Apply button on the page...")
                apply_clicked = _click_apply_button(page)

                if apply_clicked:
                    print("  ✅ Clicked Apply button — waiting for form to load...")
                    time.sleep(4)

                    ss = _take_screenshot(page, "2_form_loaded", job)
                    if ss:
                        result["screenshots"].append(ss)
                else:
                    print("  ℹ️ No Apply button found — page may already be the form")

                # ── STEP 3: Fill in all form fields ──
                print("\n📝 Step 3: Filling in application form...")
                fields_filled = _auto_fill_form(page, cover_letter_text)
                result["fields_filled"] = fields_filled

                if fields_filled > 0:
                    print(f"\n  ✅ Filled {fields_filled} fields!")
                    time.sleep(1)

                    ss = _take_screenshot(page, "3_filled", job)
                    if ss:
                        result["screenshots"].append(ss)

                    # ── STEP 4: Click Submit ──
                    print("\n🚀 Step 4: Submitting application...")
                    submitted = _click_submit_button(page)

                    if submitted:
                        time.sleep(4)
                        ss = _take_screenshot(page, "4_submitted", job)
                        if ss:
                            result["screenshots"].append(ss)
                        result["submitted"] = True
                        result["success"] = True
                        result["message"] = f"✅ Application SUBMITTED! {fields_filled} fields filled."
                        print(f"\n  🎉 APPLICATION SUBMITTED!")
                    else:
                        result["success"] = True
                        result["submitted"] = False
                        result["message"] = (
                            f"Form filled ({fields_filled} fields) but Submit button not found. "
                            f"{'Check the browser window.' if not headless else 'See screenshots below.'}"
                        )
                        print(f"\n  ⚠️ Filled form but couldn't find Submit.")
                else:
                    result["success"] = True
                    result["submitted"] = False
                    result["message"] = (
                        "Page opened but no form fields detected. "
                        "The site may require login first."
                    )
                    print(f"\n  ⚠️ No form fields found.")

                # Keep browser open for user to verify (local only)
                if not headless:
                    print(f"\n  👀 Browser staying open for 30 seconds...")
                    try:
                        page.wait_for_event("close", timeout=30000)
                    except Exception:
                        pass

            except PlaywrightTimeout:
                result["success"] = True
                result["message"] = "Page loaded slowly. Check screenshots."

            except Exception as e:
                result["message"] = f"Error: {str(e)}"
                print(f"\n  ❌ Error: {e}")

            finally:
                try:
                    context.close()
                    browser.close()
                except Exception:
                    pass

            print(f"\n{'='*60}")
            print(f"RESULT: {'SUBMITTED ✅' if result['submitted'] else 'NEEDS REVIEW ⚠️'}")
            print(f"Fields filled: {result['fields_filled']}")
            print(f"Screenshots: {len(result['screenshots'])}")
            print(f"{'='*60}\n")

    except Exception as e:
        result["message"] = f"Could not launch browser: {str(e)}"
        print(f"❌ Failed to launch: {e}")

    return result


def _click_apply_button(page):
    """Find and click the Apply button on a job listing page."""
    for selector in APPLY_BUTTON_SELECTORS:
        try:
            button = page.query_selector(selector)
            if button and button.is_visible():
                print(f"  🔘 Found: {selector}")
                button.click()
                return True
        except Exception:
            continue

    # Fallback: find by text content
    try:
        links = page.query_selector_all("a, button")
        for link in links:
            try:
                text = (link.inner_text() or "").strip().lower()
                if any(kw in text for kw in ["apply", "submit your", "start application"]):
                    if link.is_visible():
                        print(f"  🔘 Found by text: '{text[:40]}'")
                        link.click()
                        return True
            except Exception:
                continue
    except Exception:
        pass

    return False


def _auto_fill_form(page, cover_letter_text=None):
    """Detect and fill form fields on the page."""
    fields_filled = 0

    inputs = page.query_selector_all("input:visible, textarea:visible, select:visible")
    print(f"  🔍 Found {len(inputs)} form elements")

    for element in inputs:
        try:
            field_name = (element.get_attribute("name") or "").lower()
            field_id = (element.get_attribute("id") or "").lower()
            field_placeholder = (element.get_attribute("placeholder") or "").lower()
            field_type = (element.get_attribute("type") or "text").lower()
            field_label = ""
            field_aria = (element.get_attribute("aria-label") or "").lower()

            elem_id = element.get_attribute("id")
            if elem_id:
                label_el = page.query_selector(f"label[for='{elem_id}']")
                if label_el:
                    field_label = (label_el.inner_text() or "").lower()

            if not field_label:
                try:
                    parent = element.evaluate("el => el.closest('label')?.innerText || ''")
                    field_label = parent.lower() if parent else ""
                except Exception:
                    pass

            combined = f"{field_name} {field_id} {field_placeholder} {field_label} {field_aria}"

            if field_type in ["hidden", "submit", "button", "checkbox", "radio", "image"]:
                continue

            if field_type == "file":
                if RESUME_PDF_PATH.exists():
                    try:
                        element.set_input_files(str(RESUME_PDF_PATH))
                        fields_filled += 1
                        print(f"  ✅ Uploaded: resume")
                    except Exception:
                        pass
                continue

            try:
                current_val = element.input_value()
                if current_val and len(current_val.strip()) > 2:
                    continue
            except Exception:
                continue

            value_to_fill = None
            field_display = ""

            if _match_field(combined, "email"):
                value_to_fill = CANDIDATE_INFO["email"]
                field_display = "Email"
            elif _match_field(combined, "phone"):
                value_to_fill = CANDIDATE_INFO["phone"]
                field_display = "Phone"
            elif _match_field(combined, "first_name"):
                value_to_fill = CANDIDATE_INFO["first_name"]
                field_display = "First Name"
            elif _match_field(combined, "last_name"):
                value_to_fill = CANDIDATE_INFO["last_name"]
                field_display = "Last Name"
            elif _match_field(combined, "name"):
                value_to_fill = CANDIDATE_INFO["name"]
                field_display = "Full Name"
            elif _match_field(combined, "city"):
                value_to_fill = CANDIDATE_INFO["city"]
                field_display = "City"
            elif _match_field(combined, "state"):
                value_to_fill = CANDIDATE_INFO["state"]
                field_display = "State"
            elif _match_field(combined, "zip"):
                value_to_fill = CANDIDATE_INFO["zip"]
                field_display = "ZIP Code"
            elif _match_field(combined, "location"):
                value_to_fill = CANDIDATE_INFO["location"]
                field_display = "Location"
            elif _match_field(combined, "cover_letter") and cover_letter_text:
                value_to_fill = cover_letter_text
                field_display = "Cover Letter"

            if value_to_fill:
                try:
                    element.click()
                    time.sleep(0.2)
                    element.fill(value_to_fill)
                    fields_filled += 1
                    preview = value_to_fill[:50] + "..." if len(value_to_fill) > 50 else value_to_fill
                    print(f"  ✅ Filled: {field_display} → {preview}")
                except Exception:
                    pass

        except Exception:
            continue

    return fields_filled


def _click_submit_button(page):
    """Find and click the Submit/Apply button on the application form."""
    for selector in SUBMIT_BUTTON_SELECTORS:
        try:
            button = page.query_selector(selector)
            if button and button.is_visible():
                button_text = (button.inner_text() or "").strip()
                print(f"  🔘 Clicking submit: '{button_text}'")
                button.scroll_into_view_if_needed()
                time.sleep(0.5)
                button.click()
                return True
        except Exception:
            continue

    try:
        buttons = page.query_selector_all("button:visible, input[type='submit']:visible")
        for btn in buttons:
            try:
                text = (btn.inner_text() or btn.get_attribute("value") or "").strip().lower()
                if any(kw in text for kw in ["submit", "apply", "send", "complete"]):
                    print(f"  🔘 Clicking (fallback): '{text[:30]}'")
                    btn.scroll_into_view_if_needed()
                    time.sleep(0.5)
                    btn.click()
                    return True
            except Exception:
                continue
    except Exception:
        pass

    return False


def record_application(job, method="auto-apply", cover_letter_text=None, screenshot_path=None):
    """Record a successful application in the database and send notification."""
    cl = get_cover_letter(job["id"])
    cl_id = cl["id"] if cl else None

    notes = f"Applied via {method}"
    if screenshot_path:
        notes += f" | Screenshot: {screenshot_path}"

    app_id = insert_application(
        job_id=job["id"],
        method=method,
        cover_letter_id=cl_id,
        notes=notes,
    )

    try:
        send_application_confirmation(job, cover_letter_text)
    except Exception as e:
        print(f"Warning: Could not send email confirmation: {e}")

    return app_id


# ============================================================
# Subprocess entry point
# ============================================================
if __name__ == "__main__":
    if len(sys.argv) >= 2:
        job_data = json.loads(sys.argv[1])
        cl_text = sys.argv[2] if len(sys.argv) >= 3 else None
        result = launch_browser_and_apply(job_data, cl_text)
        print(f"\n__RESULT__{json.dumps(result)}__END_RESULT__")
