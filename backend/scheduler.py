"""
scheduler.py — APScheduler wrapper.
Runs the AQI ingestion pipeline every 15 minutes.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import pytz

logger = logging.getLogger(__name__)

INDIAN_CITIES = [
    "Delhi", "Mumbai", "Bangalore", "Hyderabad", "Chennai",
    "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
    "Kanpur", "Nagpur", "Indore", "Thane", "Bhopal",
    "Visakhapatnam", "Vadodara", "Patna", "Ludhiana", "Agra",
    "Nashik", "Faridabad", "Meerut", "Rajkot", "Varanasi",
    "Srinagar", "Aurangabad", "Dhanbad", "Amritsar", "Allahabad",
    "Ranchi", "Coimbatore", "Vijayawada", "Jodhpur", "Madurai",
    "Raipur", "Kota", "Chandigarh", "Guwahati", "Solapur",
]

_scheduler: BackgroundScheduler | None = None


def run_pipeline():
    """Top-level job called by APScheduler every 15 min."""
    from services.pipeline import ingest_all_cities
    logger.info("⏰ Scheduler triggered — starting AQI ingestion")
    try:
        ingest_all_cities(INDIAN_CITIES)
    except Exception as exc:
        logger.error(f"Pipeline error: {exc}", exc_info=True)


def init_scheduler(app):
    """Attach scheduler to Flask app context and start it."""
    global _scheduler
    if _scheduler is not None:
        return  # already running (Werkzeug reloader guard)

    _scheduler = BackgroundScheduler(timezone=pytz.utc)
    _scheduler.add_job(
        func=run_pipeline,
        trigger=IntervalTrigger(minutes=15),
        id="aqi_ingestion",
        name="AQI ingestion every 15 minutes",
        replace_existing=True,
        misfire_grace_time=120,
    )
    _scheduler.start()
    logger.info("✅ APScheduler started — AQI pipeline runs every 15 minutes")

    # Ensure clean shutdown when the app exits
    import atexit
    atexit.register(lambda: _scheduler.shutdown(wait=False))
