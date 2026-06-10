"""
Combined launcher: runs the web dashboard AND the continuous scraper
scheduler in a single process (scheduler on a daemon thread).

Use this on single-service PaaS hosts (e.g. Render free/starter) where the
web app and the scraper must share one SQLite file on one disk.

For multi-process / multi-host setups, run `main.py serve` and
`main.py schedule` separately and back them with Postgres instead of SQLite.

Run:  python serve_all.py        (binds to $PORT or 5000)
"""
import os
import threading
import logging

from database.db import init_db
from scheduler import start_continuous
from webapp.app import app

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s")
logger = logging.getLogger("serve_all")


def _start_scheduler():
    # Skip the immediate full run so the web app comes up fast;
    # the first scheduled sweep will populate data shortly after.
    try:
        start_continuous(run_now=os.getenv("RUN_NOW", "0") == "1")
    except Exception as e:
        logger.error("Scheduler thread crashed: %s", e, exc_info=True)


# Initialise DB and launch the scheduler thread at import time so it runs
# under gunicorn as well as the Flask dev server.
init_db()
threading.Thread(target=_start_scheduler, daemon=True, name="scheduler").start()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
