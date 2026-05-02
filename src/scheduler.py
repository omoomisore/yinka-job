"""
Yinka Job Bot — Scheduler
Background job scheduling for automated searches.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config import SEARCH_INTERVAL_HOURS


_scheduler = None


def get_scheduler():
    """Get or create the background scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler()
    return _scheduler


def start_scheduled_search(search_fn, score_fn=None, notify_fn=None):
    """
    Start automated job searching on a schedule.
    
    Args:
        search_fn: Function to call for searching (e.g., run_all_searches)
        score_fn: Function to call for scoring (e.g., score_all_unscored)
        notify_fn: Function to call for notifications
    """
    scheduler = get_scheduler()

    def _run_pipeline():
        """Run the full search → score → notify pipeline."""
        print(f"\n{'='*50}")
        print(f"🤖 Automated search pipeline starting...")
        print(f"{'='*50}\n")
        
        # Search
        summary = search_fn()
        
        # Score new results
        if score_fn and summary.get("total_new", 0) > 0:
            score_fn()
        
        # Notify
        if notify_fn and summary.get("total_new", 0) > 0:
            from src.database import get_all_jobs
            new_good_jobs = get_all_jobs(min_score=60, limit=20)
            if new_good_jobs:
                notify_fn(new_good_jobs, summary)

    # Add job to scheduler
    scheduler.add_job(
        _run_pipeline,
        trigger=IntervalTrigger(hours=SEARCH_INTERVAL_HOURS),
        id="job_search_pipeline",
        replace_existing=True,
        name="Automated Job Search Pipeline",
    )

    if not scheduler.running:
        scheduler.start()
        print(f"⏰ Scheduler started — searching every {SEARCH_INTERVAL_HOURS} hours")

    return scheduler


def stop_scheduler():
    """Stop the background scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        print("⏹️ Scheduler stopped")
    _scheduler = None


def is_scheduler_running():
    """Check if the scheduler is currently running."""
    return _scheduler is not None and _scheduler.running
