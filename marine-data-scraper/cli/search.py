"""
CLI search interface for the marine company database.
Usage:
    python -m cli.search --query "tanker Greece" --type shipowner --has-email
    python -m cli.search --stats
    python -m cli.search --export companies.xlsx
"""
import sys
import logging
from pathlib import Path
from datetime import datetime

import click
from tabulate import tabulate

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import init_db, get_session, search_companies, get_stats
from database.models import Company
from exporters.csv_exporter import export_companies_csv, export_contacts_csv
from exporters.excel_exporter import export_excel

logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Marine Company Database CLI"""
    pass


@cli.command()
@click.option("--query",   "-q", default="", help="Full-text search query")
@click.option("--type",    "-t", default="", help="Company type filter (e.g. shipowner, shipyard)")
@click.option("--country", "-c", default="", help="Country filter")
@click.option("--vessel",  "-v", default="", help="Vessel type filter (e.g. Tanker, Bulk Carrier)")
@click.option("--has-email", is_flag=True,   help="Only show companies with at least one email")
@click.option("--limit",   "-l", default=50, help="Max results (default 50)")
@click.option("--offset",  "-o", default=0,  help="Results offset for pagination")
def search(query, type, country, vessel, has_email, limit, offset):
    """Search the marine company database."""
    init_db()
    with get_session() as session:
        results = search_companies(
            session,
            query=query,
            company_type=type,
            country=country,
            vessel_type=vessel,
            has_email=has_email,
            limit=limit,
            offset=offset,
        )

        if not results:
            click.echo("No results found.")
            return

        rows = []
        for c in results:
            emails = "; ".join(e.address for e in c.emails[:3])
            if len(c.emails) > 3:
                emails += f" (+{len(c.emails)-3} more)"
            rows.append([
                c.id,
                c.name[:50],
                c.company_type or "",
                c.country or "",
                c.city or "",
                emails or "(none)",
            ])

        click.echo(tabulate(
            rows,
            headers=["ID", "Company", "Type", "Country", "City", "Emails"],
            tablefmt="rounded_outline",
        ))
        click.echo(f"\n{len(results)} results (offset={offset}, limit={limit})")


@cli.command()
def stats():
    """Show database statistics."""
    init_db()
    with get_session() as session:
        s = get_stats(session)

    click.echo("\n=== Marine Database Statistics ===\n")
    click.echo(f"  Total Companies : {s['total_companies']:,}")
    click.echo(f"  Total Contacts  : {s['total_contacts']:,}")
    click.echo(f"  Total Emails    : {s['total_emails']:,}")
    click.echo(f"  Total Vessels   : {s['total_vessels']:,}")

    click.echo("\n  By Company Type:")
    for ctype, cnt in sorted(s["companies_by_type"].items(), key=lambda x: -x[1]):
        click.echo(f"    {(ctype or 'Unknown'):<25} {cnt:>6,}")

    click.echo("\n  Top Countries:")
    for country, cnt in list(s["companies_by_country"].items())[:10]:
        click.echo(f"    {(country or 'Unknown'):<25} {cnt:>6,}")


@cli.command()
@click.argument("output_path")
@click.option("--format",  "-f", "fmt", default="excel",
              type=click.Choice(["excel", "csv", "contacts"]),
              help="Export format: excel | csv | contacts")
@click.option("--query",   "-q", default="", help="Filter by search query before export")
@click.option("--type",    "-t", default="", help="Filter by company type")
@click.option("--country", "-c", default="", help="Filter by country")
@click.option("--vessel",  "-v", default="", help="Filter by vessel type")
@click.option("--has-email", is_flag=True,   help="Only export companies with emails")
def export(output_path, fmt, query, type, country, vessel, has_email):
    """Export data to Excel or CSV. OUTPUT_PATH is the destination file."""
    init_db()
    with get_session() as session:
        companies = search_companies(
            session,
            query=query,
            company_type=type,
            country=country,
            vessel_type=vessel,
            has_email=has_email,
            limit=100_000,
        )

        if not companies:
            click.echo("No data to export.")
            return

        path = Path(output_path)
        if fmt == "excel":
            result = export_excel(session, path, companies)
        elif fmt == "contacts":
            result = export_contacts_csv(session, path, companies)
        else:
            result = export_companies_csv(session, path, companies)

    if result:
        click.echo(f"Exported {len(companies)} companies to {result}")
    else:
        click.echo("Export failed – check logs.")


@cli.command()
@click.argument("company_id", type=int)
def show(company_id):
    """Show full details for a company by ID."""
    init_db()
    with get_session() as session:
        company = session.get(Company, company_id)
        if not company:
            click.echo(f"Company {company_id} not found.")
            return

        click.echo(f"\n{'='*60}")
        click.echo(f"  {company.name}")
        click.echo(f"{'='*60}")
        click.echo(f"  Type        : {company.company_type or 'Unknown'}")
        click.echo(f"  Country     : {company.country or ''}")
        click.echo(f"  City        : {company.city or ''}")
        click.echo(f"  Port        : {company.port or ''}")
        click.echo(f"  Website     : {company.website or ''}")
        click.echo(f"  Fleet Size  : {company.fleet_size or 'N/A'}")
        click.echo(f"  Vessel Types: {', '.join(vt.name for vt in company.vessel_types)}")
        click.echo(f"  Source      : {company.source_name or ''}")

        if company.description:
            click.echo(f"\n  Description:\n    {company.description[:400]}")

        if company.contacts:
            click.echo(f"\n  Contacts ({len(company.contacts)}):")
            for co in company.contacts:
                line = f"    - {co.name or 'Unknown'}"
                if co.title:
                    line += f" [{co.title}]"
                if co.email:
                    line += f"  <{co.email}>"
                click.echo(line)

        if company.emails:
            click.echo(f"\n  Emails ({len(company.emails)}):")
            for em in company.emails:
                click.echo(f"    - {em.address}  [{em.email_type}]  conf={em.confidence}")

        click.echo("")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    cli()
