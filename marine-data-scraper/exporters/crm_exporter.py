"""
CRM / email-platform ready exports.

Produces a flat, one-row-per-contact CSV using column headers that import
cleanly into HubSpot, Salesforce, Pipedrive, Mailchimp, and Lemlist —
ready for mail-merge cold outreach for ship spare parts.
"""
import csv
import logging
from pathlib import Path
from sqlalchemy.orm import Session

from database.models import Company
from processors.lead_scorer import score_grade

logger = logging.getLogger(__name__)

# Headers chosen to map onto common CRM import fields
CRM_FIELDS = [
    "First Name", "Last Name", "Email", "Job Title", "Seniority",
    "Department", "Decision Maker", "Email Status",
    "Company", "Company Type", "Website", "Phone",
    "Country", "City", "Region", "Vessel Types", "Fleet Size",
    "Lead Score", "Lead Grade", "LinkedIn",
    "Source", "Source URL",
]


def export_crm_csv(session: Session, path: Path, companies: list[Company] = None):
    if companies is None:
        companies = session.query(Company).filter_by(is_active=True).all()

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows_written = 0
    with open(path, "w", newline="", encoding="utf-8-sig") as f:  # BOM for Excel
        writer = csv.DictWriter(f, fieldnames=CRM_FIELDS)
        writer.writeheader()

        for c in companies:
            vtypes = "; ".join(vt.name for vt in c.vessel_types)
            grade  = score_grade(c.lead_score or 0)
            base = {
                "Company":      c.name,
                "Company Type": c.company_type or "",
                "Website":      c.website or "",
                "Phone":        c.phone or "",
                "Country":      c.country or "",
                "City":         c.city or "",
                "Region":       c.region or "",
                "Vessel Types": vtypes,
                "Fleet Size":   c.fleet_size or "",
                "Lead Score":   c.lead_score or 0,
                "Lead Grade":   grade,
                "Source":       c.source_name or "",
                "Source URL":   c.source_url or "",
            }

            written_emails = set()

            # One row per named contact
            for co in c.contacts:
                if not (co.name or co.email):
                    continue
                row = base.copy()
                row.update({
                    "First Name":    co.first_name or (co.name or "").split(" ")[0],
                    "Last Name":     co.last_name or " ".join((co.name or "").split(" ")[1:]),
                    "Email":         co.email or "",
                    "Job Title":     co.title or "",
                    "Seniority":     co.seniority or "",
                    "Department":    co.department or "",
                    "Decision Maker":"Yes" if co.is_decision_maker else "No",
                    "Email Status":  co.email_status or "",
                    "LinkedIn":      co.linkedin or c.linkedin or "",
                })
                writer.writerow(row)
                rows_written += 1
                if co.email:
                    written_emails.add(co.email.lower())

            # Remaining company emails with no named contact
            for em in c.emails:
                if em.address in written_emails:
                    continue
                row = base.copy()
                row.update({
                    "First Name":    "",
                    "Last Name":     "",
                    "Email":         em.address,
                    "Job Title":     "",
                    "Seniority":     "",
                    "Department":    em.email_type or "",
                    "Decision Maker":"No",
                    "Email Status":  "role" if em.is_role else "unverified",
                    "LinkedIn":      c.linkedin or "",
                })
                writer.writerow(row)
                rows_written += 1
                written_emails.add(em.address)

    logger.info("CRM export: %d rows -> %s", rows_written, path)
    return path
