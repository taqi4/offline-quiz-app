"""Export company + contact + email data to CSV files."""
import csv
import logging
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session

from database.models import Company

logger = logging.getLogger(__name__)


def export_companies_csv(session: Session, path: Path, companies: list[Company] = None):
    """Export companies with their emails to a flat CSV."""
    if companies is None:
        companies = session.query(Company).filter_by(is_active=True).all()

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "id", "company_name", "company_type", "country", "city",
        "address", "port", "website", "fleet_size", "description",
        "vessel_types", "emails", "contacts",
        "source_name", "source_url", "date_scraped",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in companies:
            emails_str   = "; ".join(e.address for e in c.emails)
            vtypes_str   = "; ".join(vt.name for vt in c.vessel_types)
            contacts_str = "; ".join(
                f"{co.name} <{co.email}>" if co.email else co.name
                for co in c.contacts if co.name
            )
            writer.writerow({
                "id":           c.id,
                "company_name": c.name,
                "company_type": c.company_type or "",
                "country":      c.country or "",
                "city":         c.city or "",
                "address":      (c.address or "").replace("\n", " "),
                "port":         c.port or "",
                "website":      c.website or "",
                "fleet_size":   c.fleet_size or "",
                "description":  (c.description or "")[:300].replace("\n", " "),
                "vessel_types": vtypes_str,
                "emails":       emails_str,
                "contacts":     contacts_str,
                "source_name":  c.source_name or "",
                "source_url":   c.source_url or "",
                "date_scraped": c.date_scraped.isoformat() if c.date_scraped else "",
            })

    logger.info("Exported %d companies to %s", len(companies), path)
    return path


def export_contacts_csv(session: Session, path: Path, companies: list[Company] = None):
    """Export flat contact list (one row per contact+email combination)."""
    if companies is None:
        companies = session.query(Company).filter_by(is_active=True).all()

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "company_name", "company_type", "country", "city",
        "contact_name", "contact_title", "contact_email",
        "company_website", "vessel_types", "source_name",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for c in companies:
            vtypes = "; ".join(vt.name for vt in c.vessel_types)
            base = {
                "company_name": c.name,
                "company_type": c.company_type or "",
                "country":      c.country or "",
                "city":         c.city or "",
                "company_website": c.website or "",
                "vessel_types": vtypes,
                "source_name":  c.source_name or "",
            }

            # Named contacts first
            written_emails: set[str] = set()
            for co in c.contacts:
                if co.name or co.email:
                    row = base.copy()
                    row["contact_name"]  = co.name or ""
                    row["contact_title"] = co.title or ""
                    row["contact_email"] = co.email or ""
                    writer.writerow(row)
                    if co.email:
                        written_emails.add(co.email.lower())

            # Remaining emails not already in contacts
            for em in c.emails:
                if em.address not in written_emails:
                    row = base.copy()
                    row["contact_name"]  = ""
                    row["contact_title"] = em.email_type or ""
                    row["contact_email"] = em.address
                    writer.writerow(row)
                    written_emails.add(em.address)

    logger.info("Exported contacts/emails to %s", path)
    return path
