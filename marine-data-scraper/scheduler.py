"""
Continuous scraper scheduler.
Runs each scraper on its configured interval and keeps the database fresh.
"""
import logging
import sys
import time
import signal
import threading
from datetime import datetime
from pathlib import Path

import schedule

import config
from database.db import init_db, get_session
from processors.deduplicator import run_deduplication

logger = logging.getLogger(__name__)

# Registry of all available scrapers
SCRAPER_REGISTRY = {
    "maritime_connector": "scrapers.maritime_connector.MaritimeConnectorScraper",
    "hellenic_shipping":  "scrapers.hellenic_shipping.HellenicShippingNewsScraper",
    "shipserv":           "scrapers.shipserv.ShipServScraper",
    "maritime_events":    "scrapers.maritime_events.MaritimeEventsScraper",
    "port_directory":     "scrapers.port_directory.PortDirectoryScraper",
    "generic_directory":  "scrapers.generic_directory.GenericDirectoryScraper",
    "web_discovery":      "scrapers.web_discovery.WebDiscoveryScraper",
}

# ---------------------------------------------------------------------------
# Scheduler state — readable and writable from the web UI
# ---------------------------------------------------------------------------

_state_lock   = threading.Lock()
_running      = True       # False → scheduler loop exits completely
_paused       = False      # True → loop ticks but skips all jobs
_current_job  = ""         # name of the scraper currently running (or "")
_last_run     = {}         # {scraper_name: datetime}
_stats        = {          # live counters reset each run-all
    "companies_found": 0,
    "contacts_found":  0,
    "emails_found":    0,
}


def get_scheduler_status() -> dict:
    with _state_lock:
        return {
            "running":       _running,
            "paused":        _paused,
            "current_job":   _current_job,
            "last_run":      {k: v.isoformat() for k, v in _last_run.items()},
            "scrapers":      list(SCRAPER_REGISTRY.keys()),
            "stats":         dict(_stats),
        }


def pause_scheduler():
    global _paused
    with _state_lock:
        _paused = True
    logger.info("Scheduler paused via UI")


def resume_scheduler():
    global _paused
    with _state_lock:
        _paused = False
    logger.info("Scheduler resumed via UI")


def stop_scheduler():
    global _running
    with _state_lock:
        _running = False
    logger.info("Scheduler stopped via UI")


def _load_scraper(dotted_path: str):
    module_path, class_name = dotted_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def run_scraper(name: str):
    global _current_job
    if _paused:
        logger.info("Scheduler paused — skipping %s", name)
        return
    with _state_lock:
        _current_job = name
        _last_run[name] = datetime.utcnow()
    logger.info("=== Starting scraper: %s ===", name)
    scraper_class = _load_scraper(SCRAPER_REGISTRY[name])
    scraper = scraper_class()
    try:
        companies, contacts, emails = scraper.run()
        with _state_lock:
            _stats["companies_found"] += companies
            _stats["contacts_found"]  += contacts
            _stats["emails_found"]    += emails
        logger.info("=== %s complete: %d companies, %d contacts, %d emails ===",
                    name, companies, contacts, emails)
    except Exception as e:
        logger.error("Scraper %s raised an exception: %s", name, e, exc_info=True)
    finally:
        with _state_lock:
            _current_job = ""


def run_dedup():
    logger.info("Running deduplication…")
    with get_session() as session:
        run_deduplication(session)


def run_enrichment(limit: int = 200, do_mx_check: bool = False):
    """Visit company websites to harvest emails, phones, socials, people."""
    logger.info("Running website enrichment (limit=%d)…", limit)
    from processors.enricher import enrich_pending
    with get_session() as session:
        n = enrich_pending(session, limit=limit, do_mx_check=do_mx_check)
    logger.info("Enriched %d companies", n)


def run_intelligence():
    """Classify contacts, infer email patterns, generate emails, rescore leads."""
    logger.info("Running marketing-intelligence pass…")
    from processors.contact_classifier import enrich_contact
    from processors.email_pattern import infer_company_pattern, generate_contact_emails
    from processors.lead_scorer import score_company
    from database.models import Company

    with get_session() as session:
        companies = session.query(Company).all()
        for c in companies:
            for contact in c.contacts:
                enrich_contact(contact)
            infer_company_pattern(session, c)
            generate_contact_emails(session, c)
            c.lead_score = score_company(c)
        session.commit()
    logger.info("Intelligence pass complete for %d companies", len(companies))


def run_postprocess():
    """Full post-scrape pipeline: dedup -> enrich -> intelligence."""
    run_dedup()
    run_enrichment()
    run_intelligence()


def run_all_scrapers():
    """Run every scraper once – useful for initial seed."""
    for name in SCRAPER_REGISTRY:
        run_scraper(name)
    run_postprocess()


def start_continuous(run_now: bool = True):
    """Schedule all scrapers and run indefinitely."""
    global _running

    def _sig_handler(sig, frame):
        global _running
        logger.info("Received signal %s – stopping scheduler", sig)
        _running = False

    signal.signal(signal.SIGINT,  _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    if run_now:
        run_all_scrapers()

    # Schedule each scraper at its configured interval
    for name, interval_hours in config.SCRAPER_INTERVALS.items():
        if name in SCRAPER_REGISTRY:
            schedule.every(interval_hours).hours.do(run_scraper, name)
            logger.info("Scheduled %s every %d hours", name, interval_hours)

    # Post-processing pipeline
    schedule.every(24).hours.do(run_dedup)
    schedule.every(6).hours.do(run_enrichment)
    schedule.every(12).hours.do(run_intelligence)

    logger.info("Scheduler started. Press Ctrl+C to stop.")
    while _running:
        if not _paused:
            schedule.run_pending()
        time.sleep(30)

    logger.info("Scheduler stopped.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config.LOGS_DIR / "scheduler.log"),
        ],
    )
    init_db()
    start_continuous(run_now=True)
