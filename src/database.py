"""
Yinka Job Bot — Database Layer
SQLite database for tracking jobs, scores, applications, and cover letters.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from config import DB_PATH


def get_connection():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            description TEXT,
            source TEXT,
            apply_url TEXT,
            salary_info TEXT,
            job_type TEXT,
            date_posted TEXT,
            date_found TEXT DEFAULT (datetime('now')),
            relevance_score INTEGER DEFAULT 0,
            score_reasoning TEXT,
            status TEXT DEFAULT 'new',
            is_duplicate INTEGER DEFAULT 0,
            raw_data TEXT,
            search_query TEXT,
            UNIQUE(title, company, location)
        );

        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            applied_at TEXT DEFAULT (datetime('now')),
            method TEXT DEFAULT 'manual',
            cover_letter_id INTEGER,
            status TEXT DEFAULT 'applied',
            notes TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs(id),
            FOREIGN KEY (cover_letter_id) REFERENCES cover_letters(id)
        );

        CREATE TABLE IF NOT EXISTS cover_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            tone TEXT DEFAULT 'professional',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        );

        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            location TEXT,
            results_count INTEGER DEFAULT 0,
            searched_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
        CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(relevance_score DESC);
        CREATE INDEX IF NOT EXISTS idx_jobs_date ON jobs(date_found DESC);
        CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
    """)

    conn.commit()
    conn.close()


# ============================================================
# Jobs CRUD
# ============================================================

def insert_job(title, company, location, description, source, apply_url,
               salary_info=None, job_type=None, date_posted=None,
               raw_data=None, search_query=None):
    """Insert a new job listing. Returns job ID or None if duplicate."""
    conn = get_connection()
    try:
        cursor = conn.execute("""
            INSERT OR IGNORE INTO jobs 
            (title, company, location, description, source, apply_url,
             salary_info, job_type, date_posted, raw_data, search_query)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, company, location, description, source, apply_url,
              salary_info, job_type, date_posted,
              json.dumps(raw_data) if raw_data else None, search_query))
        conn.commit()
        if cursor.rowcount > 0:
            return cursor.lastrowid
        return None  # Duplicate
    finally:
        conn.close()


def update_job_score(job_id, score, reasoning):
    """Update the relevance score and reasoning for a job."""
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE jobs SET relevance_score = ?, score_reasoning = ?
            WHERE id = ?
        """, (score, reasoning, job_id))
        conn.commit()
    finally:
        conn.close()


def update_job_status(job_id, status):
    """Update the status of a job (new, reviewed, applied, rejected, interview)."""
    conn = get_connection()
    try:
        conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (status, job_id))
        conn.commit()
    finally:
        conn.close()


def get_all_jobs(status=None, min_score=None, limit=100, offset=0):
    """Get all jobs with optional filtering."""
    conn = get_connection()
    try:
        query = "SELECT * FROM jobs WHERE is_duplicate = 0"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if min_score is not None:
            query += " AND relevance_score >= ?"
            params.append(min_score)

        query += " ORDER BY relevance_score DESC, date_found DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_job_by_id(job_id):
    """Get a single job by ID."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_unscored_jobs():
    """Get jobs that haven't been scored yet."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE relevance_score = 0 AND is_duplicate = 0"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_jobs_count(status=None):
    """Get count of jobs, optionally filtered by status."""
    conn = get_connection()
    try:
        if status:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM jobs WHERE status = ? AND is_duplicate = 0",
                (status,)
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM jobs WHERE is_duplicate = 0"
            ).fetchone()
        return row["cnt"]
    finally:
        conn.close()


def get_job_stats():
    """Get aggregate statistics about jobs."""
    conn = get_connection()
    try:
        stats = {}
        stats["total"] = conn.execute(
            "SELECT COUNT(*) as cnt FROM jobs WHERE is_duplicate = 0"
        ).fetchone()["cnt"]
        stats["new"] = conn.execute(
            "SELECT COUNT(*) as cnt FROM jobs WHERE status = 'new' AND is_duplicate = 0"
        ).fetchone()["cnt"]
        stats["applied"] = conn.execute(
            "SELECT COUNT(*) as cnt FROM jobs WHERE status = 'applied' AND is_duplicate = 0"
        ).fetchone()["cnt"]
        stats["interview"] = conn.execute(
            "SELECT COUNT(*) as cnt FROM jobs WHERE status = 'interview' AND is_duplicate = 0"
        ).fetchone()["cnt"]
        stats["rejected"] = conn.execute(
            "SELECT COUNT(*) as cnt FROM jobs WHERE status = 'rejected' AND is_duplicate = 0"
        ).fetchone()["cnt"]

        avg_row = conn.execute(
            "SELECT AVG(relevance_score) as avg_score FROM jobs WHERE relevance_score > 0 AND is_duplicate = 0"
        ).fetchone()
        stats["avg_score"] = round(avg_row["avg_score"] or 0, 1)

        stats["strong_matches"] = conn.execute(
            "SELECT COUNT(*) as cnt FROM jobs WHERE relevance_score >= 80 AND is_duplicate = 0"
        ).fetchone()["cnt"]

        # Jobs by source
        rows = conn.execute(
            "SELECT source, COUNT(*) as cnt FROM jobs WHERE is_duplicate = 0 GROUP BY source"
        ).fetchall()
        stats["by_source"] = {row["source"]: row["cnt"] for row in rows}

        # Jobs by status
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM jobs WHERE is_duplicate = 0 GROUP BY status"
        ).fetchall()
        stats["by_status"] = {row["status"]: row["cnt"] for row in rows}

        # Top companies
        rows = conn.execute(
            "SELECT company, COUNT(*) as cnt FROM jobs WHERE is_duplicate = 0 GROUP BY company ORDER BY cnt DESC LIMIT 10"
        ).fetchall()
        stats["top_companies"] = {row["company"]: row["cnt"] for row in rows}

        # Jobs found per day (last 30 days)
        rows = conn.execute("""
            SELECT DATE(date_found) as day, COUNT(*) as cnt 
            FROM jobs WHERE is_duplicate = 0
            GROUP BY DATE(date_found) 
            ORDER BY day DESC LIMIT 30
        """).fetchall()
        stats["daily_found"] = {row["day"]: row["cnt"] for row in rows}

        return stats
    finally:
        conn.close()


def search_jobs_db(query_text):
    """Search jobs in the database by title, company, or description."""
    conn = get_connection()
    try:
        search = f"%{query_text}%"
        rows = conn.execute("""
            SELECT * FROM jobs 
            WHERE is_duplicate = 0 
            AND (title LIKE ? OR company LIKE ? OR description LIKE ?)
            ORDER BY relevance_score DESC
        """, (search, search, search)).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# ============================================================
# Applications CRUD
# ============================================================

def insert_application(job_id, method="manual", cover_letter_id=None, notes=None):
    """Record a new application."""
    conn = get_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO applications (job_id, method, cover_letter_id, notes)
            VALUES (?, ?, ?, ?)
        """, (job_id, method, cover_letter_id, notes))
        # Also update job status
        conn.execute("UPDATE jobs SET status = 'applied' WHERE id = ?", (job_id,))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_all_applications():
    """Get all applications with job details."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT a.*, j.title, j.company, j.location, j.apply_url, j.relevance_score
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            ORDER BY a.applied_at DESC
        """).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def update_application_status(app_id, status):
    """Update application status."""
    conn = get_connection()
    try:
        conn.execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))
        conn.commit()
    finally:
        conn.close()


# ============================================================
# Cover Letters CRUD
# ============================================================

def insert_cover_letter(job_id, content, tone="professional"):
    """Save a generated cover letter."""
    conn = get_connection()
    try:
        cursor = conn.execute("""
            INSERT INTO cover_letters (job_id, content, tone)
            VALUES (?, ?, ?)
        """, (job_id, content, tone))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_cover_letter(job_id):
    """Get the latest cover letter for a job."""
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT * FROM cover_letters WHERE job_id = ?
            ORDER BY created_at DESC LIMIT 1
        """, (job_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_cover_letters():
    """Get all cover letters with job details."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT cl.*, j.title, j.company
            FROM cover_letters cl
            JOIN jobs j ON cl.job_id = j.id
            ORDER BY cl.created_at DESC
        """).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def update_cover_letter(cl_id, content):
    """Update a cover letter's content."""
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE cover_letters SET content = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (content, cl_id))
        conn.commit()
    finally:
        conn.close()


# ============================================================
# Search History
# ============================================================

def log_search(query, location, results_count):
    """Log a search execution."""
    conn = get_connection()
    try:
        conn.execute("""
            INSERT INTO search_history (query, location, results_count)
            VALUES (?, ?, ?)
        """, (query, location, results_count))
        conn.commit()
    finally:
        conn.close()


def get_search_history(limit=50):
    """Get recent search history."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT * FROM search_history ORDER BY searched_at DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# Initialize on import
init_db()
