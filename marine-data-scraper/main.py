"""
Marine Data Scraper – main entry point.

Commands:
  python main.py run-all          # Run every scraper once
  python main.py run <name>       # Run a single named scraper
  python main.py schedule         # Start continuous scheduler
  python main.py search           # Interactive search
  python main.py export <file>    # Export to Excel/CSV
  python main.py stats            # Database statistics
  python main.py dedup            # Run deduplication
  python main.py init-db          # Initialise database only
"""
import sys
import logging
from pathlib import Path

import click
import colorlog

import config
from database.db import init_db, get_session
from scheduler import (
    SCRAPER_REGISTRY, run_scraper, run_all_scrapers, start_continuous,
    run_dedup, run_enrichment, run_intelligence, run_postprocess,
)


def _setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s]%(reset)s %(name)s – %(message)s",
        log_colors={
            "DEBUG":   "cyan",
            "INFO":    "green",
            "WARNING": "yellow",
            "ERROR":   "red",
            "CRITICAL":"bold_red",
        },
    ))
    file_handler = logging.FileHandler(config.LOGS_DIR / "main.log")
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s – %(message)s"
    ))
    logging.basicConfig(level=level, handlers=[handler, file_handler])


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable debug logging")
def cli(verbose):
    """Marine Data Scraper – collect marine company data for ship spares sales."""
    _setup_logging(verbose)


@cli.command("init-db")
def cmd_init_db():
    """Initialise the SQLite database and create all tables."""
    init_db()
    click.echo("Database initialised.")


@cli.command("run-all")
def cmd_run_all():
    """Run every scraper once to seed the database."""
    init_db()
    run_all_scrapers()


@cli.command("run")
@click.argument("scraper_name", type=click.Choice(list(SCRAPER_REGISTRY.keys())))
def cmd_run(scraper_name):
    """Run a single scraper by name."""
    init_db()
    run_scraper(scraper_name)


@cli.command("schedule")
@click.option("--no-initial-run", is_flag=True, help="Skip immediate run on start")
def cmd_schedule(no_initial_run):
    """Start the continuous scheduler (runs indefinitely)."""
    init_db()
    start_continuous(run_now=not no_initial_run)


@cli.command("stats")
def cmd_stats():
    """Print database statistics."""
    from cli.search import stats as stats_cmd
    init_db()
    stats_cmd.main(standalone_mode=False)


@cli.command("search")
@click.option("--query",   "-q", default="")
@click.option("--type",    "-t", default="")
@click.option("--country", "-c", default="")
@click.option("--vessel",  "-v", default="")
@click.option("--has-email", is_flag=True)
@click.option("--limit",   "-l", default=50)
def cmd_search(query, type, country, vessel, has_email, limit):
    """Search the database."""
    from cli.search import search as search_cmd
    init_db()
    ctx = click.Context(search_cmd)
    ctx.invoke(search_cmd, query=query, type=type, country=country,
               vessel=vessel, has_email=has_email, limit=limit, offset=0)


@cli.command("export")
@click.argument("output_path")
@click.option("--format", "-f", "fmt", default="excel",
              type=click.Choice(["excel", "csv", "contacts"]))
@click.option("--type",    "-t", default="")
@click.option("--country", "-c", default="")
@click.option("--has-email", is_flag=True)
def cmd_export(output_path, fmt, type, country, has_email):
    """Export to Excel (.xlsx) or CSV."""
    from cli.search import export as export_cmd
    init_db()
    ctx = click.Context(export_cmd)
    ctx.invoke(export_cmd, output_path=output_path, fmt=fmt,
               query="", type=type, country=country, vessel="",
               has_email=has_email)


@cli.command("dedup")
def cmd_dedup():
    """Run deduplication to merge similar company records."""
    init_db()
    run_dedup()
    click.echo("Deduplication complete.")


@cli.command("enrich")
@click.option("--limit", "-l", default=200, help="Max companies to enrich")
@click.option("--mx-check", is_flag=True, help="Validate email domains via MX lookup")
def cmd_enrich(limit, mx_check):
    """Visit company websites to harvest emails, phones, socials, and people."""
    init_db()
    run_enrichment(limit=limit, do_mx_check=mx_check)
    click.echo("Enrichment complete.")


@cli.command("intelligence")
def cmd_intelligence():
    """Classify contacts, infer email patterns, generate emails, rescore leads."""
    init_db()
    run_intelligence()
    click.echo("Intelligence pass complete.")


@cli.command("rescore")
def cmd_rescore():
    """Recompute lead scores for all companies."""
    init_db()
    from processors.lead_scorer import rescore_all
    with get_session() as session:
        n = rescore_all(session)
    click.echo(f"Rescored {n} companies.")


@cli.command("postprocess")
def cmd_postprocess():
    """Run the full post-scrape pipeline: dedup, enrich, intelligence."""
    init_db()
    run_postprocess()
    click.echo("Post-processing complete.")


@cli.command("serve")
@click.option("--host", default="0.0.0.0")
@click.option("--port", "-p", default=5000, help="Port for the web dashboard")
@click.option("--debug", is_flag=True)
def cmd_serve(host, port, debug):
    """Launch the web dashboard + REST API."""
    init_db()
    from webapp.app import main as serve_main
    serve_main(host=host, port=port, debug=debug)


@cli.command("list-scrapers")
def cmd_list():
    """List all available scrapers."""
    click.echo("\nAvailable scrapers:")
    for name in SCRAPER_REGISTRY:
        interval = config.SCRAPER_INTERVALS.get(name, "?")
        click.echo(f"  {name:<30} every {interval}h")


if __name__ == "__main__":
    cli()
