"""
Yinka Job Bot — Job Search Engine
Uses SerpAPI Google Jobs to search across LinkedIn, Indeed, Glassdoor, ZipRecruiter, etc.
Includes location filtering for Remote + DC/MD/VA metro area (30-40 mi from Potomac, MD).
"""

import re
import time
from serpapi import GoogleSearch
from config import SERPAPI_KEY, SEARCH_QUERIES, SEARCH_LOCATION
from src.database import insert_job, log_search


# Cities/areas within 30-40 miles of Potomac, MD (ZIP 20854)
ALLOWED_LOCATIONS = [
    # Maryland
    "potomac", "rockville", "bethesda", "gaithersburg", "germantown",
    "silver spring", "columbia", "laurel", "bowie", "college park",
    "greenbelt", "hyattsville", "takoma park", "chevy chase",
    "north bethesda", "olney", "clarksburg", "damascus",
    "ellicott city", "catonsville", "annapolis", "glen burnie",
    "baltimore", "frederick", "hagerstown",
    # Washington DC
    "washington", "washington, dc", "washington dc", "dc metro",
    # Virginia
    "arlington", "alexandria", "mclean", "tysons", "reston",
    "herndon", "ashburn", "leesburg", "fairfax", "vienna",
    "falls church", "manassas", "centreville", "chantilly",
    "sterling", "dulles", "woodbridge", "springfield",
    "annandale", "burke",
    # State abbreviations
    "md", "va", "dc",
]

# Keywords that indicate remote work
REMOTE_KEYWORDS = [
    "remote", "anywhere", "work from home", "wfh",
    "telecommute", "virtual", "nationwide", "united states",
    "usa", "us-based", "u.s.",
]


def is_location_valid(location):
    """
    Check if a job location is valid (remote or within DC/MD/VA metro area).

    Args:
        location: Job location string

    Returns:
        True if the job is remote or within the target area
    """
    if not location:
        return False

    loc_lower = location.lower().strip()

    # Check if it's remote
    for keyword in REMOTE_KEYWORDS:
        if keyword in loc_lower:
            return True

    # Check if it's in the allowed area
    for area in ALLOWED_LOCATIONS:
        if area in loc_lower:
            return True

    return False


def search_jobs(query, location=None, num_results=30):
    """
    Search for jobs using SerpAPI Google Jobs engine.

    Args:
        query: Job search query string
        location: Location to search in
        num_results: Max number of results to fetch (across pages)

    Returns:
        List of job dictionaries (location-filtered)
    """
    if not SERPAPI_KEY:
        raise ValueError("SERPAPI_KEY not set. Add it to your .env file.")

    location = location or SEARCH_LOCATION
    all_jobs = []
    start = 0

    while len(all_jobs) < num_results:
        params = {
            "engine": "google_jobs",
            "q": query,
            "location": location,
            "api_key": SERPAPI_KEY,
            "start": start,
            "chips": "date_posted:week",  # Only jobs posted in the last week
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()
        except Exception as e:
            print(f"SerpAPI error for query '{query}': {e}")
            break

        jobs = results.get("jobs_results", [])
        if not jobs:
            break

        for job in jobs:
            parsed = _parse_job(job, query)
            if parsed and is_location_valid(parsed["location"]):
                all_jobs.append(parsed)

        # Check if there are more pages
        if not results.get("serpapi_pagination", {}).get("next"):
            break

        start += 10
        time.sleep(1)  # Rate limiting

    return all_jobs


def _parse_job(raw_job, search_query):
    """Parse a raw SerpAPI job result into our standard format."""
    # Extract the apply link
    apply_options = raw_job.get("apply_options", [])
    apply_url = None
    source = "Google Jobs"

    if apply_options:
        # Prefer direct apply links
        for option in apply_options:
            link = option.get("link", "")
            title = option.get("title", "").lower()
            if any(site in title for site in ["linkedin", "indeed", "glassdoor", "ziprecruiter"]):
                apply_url = link
                source = option.get("title", "Unknown")
                break
        if not apply_url and apply_options:
            apply_url = apply_options[0].get("link", "")
            source = apply_options[0].get("title", "Unknown")

    # Extract salary info
    salary = None
    detected_extensions = raw_job.get("detected_extensions", {})
    if detected_extensions.get("salary"):
        salary = detected_extensions["salary"]

    # Extract job type
    job_type = detected_extensions.get("schedule_type", "")

    return {
        "title": raw_job.get("title", "Unknown"),
        "company": raw_job.get("company_name", "Unknown"),
        "location": raw_job.get("location", "Unknown"),
        "description": raw_job.get("description", ""),
        "source": source,
        "apply_url": apply_url,
        "salary_info": salary,
        "job_type": job_type,
        "date_posted": detected_extensions.get("posted_at", ""),
        "raw_data": raw_job,
        "search_query": search_query,
    }


def run_all_searches(queries=None, location=None):
    """
    Run all configured search queries and save results to the database.
    Only saves jobs that are Remote or within 30-40 miles of Potomac, MD.

    Args:
        queries: List of search queries (uses config defaults if None)
        location: Location override

    Returns:
        Dictionary with search results summary
    """
    queries = queries or SEARCH_QUERIES
    location = location or SEARCH_LOCATION

    total_found = 0
    total_new = 0
    total_duplicate = 0
    total_filtered = 0
    errors = []

    for query in queries:
        print(f"Searching: '{query}' in '{location}'...")
        try:
            jobs = search_jobs(query, location)
            found = len(jobs)
            new = 0

            for job in jobs:
                job_id = insert_job(
                    title=job["title"],
                    company=job["company"],
                    location=job["location"],
                    description=job["description"],
                    source=job["source"],
                    apply_url=job["apply_url"],
                    salary_info=job["salary_info"],
                    job_type=job["job_type"],
                    date_posted=job["date_posted"],
                    raw_data=job["raw_data"],
                    search_query=job["search_query"],
                )
                if job_id:
                    new += 1

            total_found += found
            total_new += new
            total_duplicate += (found - new)

            log_search(query, location, found)
            print(f"   Found {found} local/remote jobs ({new} new, {found - new} duplicates)")

        except Exception as e:
            error_msg = f"Error searching '{query}': {str(e)}"
            print(f"   ERROR: {error_msg}")
            errors.append(error_msg)

        time.sleep(2)  # Be nice to the API

    summary = {
        "total_found": total_found,
        "total_new": total_new,
        "total_duplicate": total_duplicate,
        "queries_run": len(queries),
        "errors": errors,
    }

    print(f"\nSearch complete: {total_found} found, {total_new} new, {total_duplicate} duplicates")
    if errors:
        print(f"WARNING: {len(errors)} errors occurred")

    return summary
