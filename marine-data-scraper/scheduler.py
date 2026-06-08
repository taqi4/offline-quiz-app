"""
Continuous scraper scheduler.
Runs each scraper on its configured interval and keeps the database fresh.
"""
import logging
import sys
import time
import signal
from datetime import datetime, timedelta
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
}

_running = True


def _load_scraper(dotted_path: str):
    module_path, class_name = dotted_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def run_scraper(name: str):
    logger.info("=== Starting scraper: %s ===", name)
    scraper_class = _load_scraper(SCRAPER_REGISTRY[name])
    scraper = scraper_class()
    try:
        companies, contacts, emails = scraper.run()
        logger.info("=== %s complete: %d companies, %d contacts, %d emails ===",
                    name, companies, contacts, emails)
    except Exception as e:
        logger.error("Scraper %s raised an exception: %s", name, e, exc_info=True)


def run_dedup():
    logger.info("Running deduplication…")
    with get_session() as session:
        run_deduplication(session)


def run_all_scrapers():
    """Run every scraper once – useful for initial seed."""
    for name in SCRAPER_REGISTRY:
        run_scraper(name)
    run_dedup()


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

    # Dedup daily
    schedule.every(24).hours.do(run_dedup)

    logger.info("Scheduler started. Press Ctrl+C to stop.")
    while _running:
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
