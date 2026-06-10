"""Database session management and helper queries."""
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, or_, func, text, event
from sqlalchemy.orm import sessionmaker, Session

from database.models import (
    Base, Company, Contact, Email, Vessel, VesselType, Tag, ScrapeLog
)
import config


engine = create_engine(
    config.DB_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
    echo=False,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_conn, _record):
    """Enable WAL + sane concurrency settings so the dashboard and the
    scheduler can safely share one SQLite file without 'database is locked'."""
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA busy_timeout=30000")     # wait up to 30s for locks
    cur.execute("PRAGMA synchronous=NORMAL")
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db():
    """Create all tables and seed vessel type lookup data."""
    Base.metadata.create_all(engine)
    with get_session() as session:
        _seed_vessel_types(session)
        _create_fts_tables(session)


def _seed_vessel_types(session: Session):
    existing = {vt.name for vt in session.query(VesselType).all()}
    vessel_types = [
        ("Tanker",         "Oil, chemical, LNG and LPG tankers"),
        ("Bulk Carrier",   "Dry bulk vessels – capesize, panamax, handymax, handysize"),
        ("Container Ship", "Full-container and feeder vessels"),
        ("General Cargo",  "Break-bulk and multipurpose cargo vessels"),
        ("Ro-Ro",          "Roll-on/roll-off and car carriers"),
        ("Offshore",       "OSVs, PSVs, AHTS, FPSOs, rigs"),
        ("Cruise",         "Cruise ships and passenger liners"),
        ("Ferry",          "Short-sea ferries and Ro-Pax"),
        ("Tug",            "Harbour tugs and ocean salvage tugs"),
        ("Dredger",        "Hopper and cutter-suction dredgers"),
        ("Naval",          "Naval and coast-guard vessels"),
        ("Fishing",        "Fishing vessels and fish-carriers"),
        ("Yacht",          "Superyachts and sailing yachts"),
        ("Other",          "Miscellaneous / unknown vessel type"),
    ]
    for name, desc in vessel_types:
        if name not in existing:
            session.add(VesselType(name=name, description=desc))
    session.commit()


def _create_fts_tables(session: Session):
    """Create SQLite FTS5 virtual table for full-text company search."""
    session.execute(text("""
        CREATE VIRTUAL TABLE IF NOT EXISTS companies_fts USING fts5(
            name, description, country, city, address,
            content='companies', content_rowid='id'
        )
    """))
    session.execute(text("""
        CREATE TRIGGER IF NOT EXISTS companies_ai AFTER INSERT ON companies BEGIN
            INSERT INTO companies_fts(rowid, name, description, country, city, address)
            VALUES (new.id, new.name, new.description, new.country, new.city, new.address);
        END
    """))
    session.execute(text("""
        CREATE TRIGGER IF NOT EXISTS companies_ad AFTER DELETE ON companies BEGIN
            INSERT INTO companies_fts(companies_fts, rowid, name, description, country, city, address)
            VALUES ('delete', old.id, old.name, old.description, old.country, old.city, old.address);
        END
    """))
    session.execute(text("""
        CREATE TRIGGER IF NOT EXISTS companies_au AFTER UPDATE ON companies BEGIN
            INSERT INTO companies_fts(companies_fts, rowid, name, description, country, city, address)
            VALUES ('delete', old.id, old.name, old.description, old.country, old.city, old.address);
            INSERT INTO companies_fts(rowid, name, description, country, city, address)
            VALUES (new.id, new.name, new.description, new.country, new.city, new.address);
        END
    """))
    session.commit()


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Helper query functions
# ---------------------------------------------------------------------------

def upsert_company(session: Session, data: dict) -> tuple[Company, bool]:
    """Insert or update a company. Returns (company, created)."""
    norm = _normalize_name(data.get("name", ""))
    existing = session.query(Company).filter_by(name_normalized=norm).first()
    if existing:
        for k, v in data.items():
            if v and k not in ("id", "name_normalized"):
                setattr(existing, k, v)
        existing.date_updated = datetime.utcnow()
        return existing, False
    company = Company(name_normalized=norm, **data)
    session.add(company)
    session.flush()
    return company, True


FREE_EMAIL_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "protonmail.com", "icloud.com", "gmx.com", "mail.com", "yandex.com",
    "live.com", "msn.com", "qq.com", "163.com", "126.com",
}
ROLE_EMAIL_LOCALS = {
    "info", "sales", "contact", "admin", "office", "enquiries", "enquiry",
    "support", "hello", "mail", "marketing", "purchasing", "procurement",
    "technical", "service", "accounts", "general", "crewing", "operations",
}


def upsert_email(session: Session, company_id: int, address: str,
                 email_type: str = "general", source_url: str = "",
                 confidence: float = 1.0) -> bool:
    """Add email if not already present. Returns True if newly added."""
    address = address.lower().strip()
    exists = session.query(Email).filter_by(
        company_id=company_id, address=address
    ).first()
    if exists:
        return False

    domain = address.split("@", 1)[1] if "@" in address else ""
    local  = address.split("@", 1)[0] if "@" in address else address
    session.add(Email(
        company_id=company_id, address=address, email_type=email_type,
        source_url=source_url, confidence=confidence,
        domain=domain,
        is_free=domain in FREE_EMAIL_DOMAINS,
        is_role=local in ROLE_EMAIL_LOCALS,
    ))
    return True


def search_companies(
    session: Session,
    query: str = "",
    company_type: str = "",
    country: str = "",
    region: str = "",
    vessel_type: str = "",
    has_email: bool = False,
    has_phone: bool = False,
    has_decision_maker: bool = False,
    min_score: float = 0.0,
    min_fleet: int = 0,
    sort: str = "score",          # score | recent | name | fleet
    limit: int = 100,
    offset: int = 0,
) -> List[Company]:
    q = session.query(Company).filter(Company.is_active == True)

    if query:
        fts_ids = [
            row[0] for row in session.execute(
                text("SELECT rowid FROM companies_fts WHERE companies_fts MATCH :q LIMIT 1000"),
                {"q": query},
            )
        ]
        q = q.filter(Company.id.in_(fts_ids)) if fts_ids else q.filter(
            or_(
                Company.name.ilike(f"%{query}%"),
                Company.description.ilike(f"%{query}%"),
            )
        )

    if company_type:
        q = q.filter(Company.company_type.ilike(f"%{company_type}%"))
    if country:
        q = q.filter(Company.country.ilike(f"%{country}%"))
    if region:
        q = q.filter(Company.region.ilike(f"%{region}%"))
    if vessel_type:
        q = q.join(Company.vessel_types).filter(VesselType.name.ilike(f"%{vessel_type}%"))
    if has_email:
        q = q.filter(Company.emails.any())
    if has_phone:
        q = q.filter(Company.phone.isnot(None))
    if has_decision_maker:
        q = q.filter(Company.contacts.any(Contact.is_decision_maker == True))
    if min_score > 0:
        q = q.filter(Company.lead_score >= min_score)
    if min_fleet > 0:
        q = q.filter(Company.fleet_size >= min_fleet)

    sort_map = {
        "score":  Company.lead_score.desc(),
        "recent": Company.date_scraped.desc(),
        "name":   Company.name.asc(),
        "fleet":  Company.fleet_size.desc(),
    }
    q = q.order_by(sort_map.get(sort, Company.lead_score.desc()))

    return q.offset(offset).limit(limit).all()


def get_stats(session: Session) -> dict:
    return {
        "total_companies":  session.query(func.count(Company.id)).scalar(),
        "total_contacts":   session.query(func.count(Contact.id)).scalar(),
        "total_emails":     session.query(func.count(Email.id)).scalar(),
        "total_vessels":    session.query(func.count(Vessel.id)).scalar(),
        "decision_makers":  session.query(func.count(Contact.id))
                              .filter(Contact.is_decision_maker == True).scalar(),
        "companies_with_email": session.query(func.count(Company.id))
                                 .filter(Company.emails.any()).scalar(),
        "companies_with_phone": session.query(func.count(Company.id))
                                 .filter(Company.phone.isnot(None)).scalar(),
        "hot_leads":        session.query(func.count(Company.id))
                              .filter(Company.lead_score >= 80).scalar(),
        "warm_leads":       session.query(func.count(Company.id))
                              .filter(Company.lead_score >= 65,
                                      Company.lead_score < 80).scalar(),
        "avg_lead_score":   round(session.query(func.avg(Company.lead_score)).scalar() or 0, 1),
        "companies_by_type": dict(
            session.query(Company.company_type, func.count(Company.id))
            .group_by(Company.company_type).all()
        ),
        "companies_by_country": dict(
            session.query(Company.country, func.count(Company.id))
            .group_by(Company.country)
            .order_by(func.count(Company.id).desc())
            .limit(20).all()
        ),
        "companies_by_source": dict(
            session.query(Company.source_name, func.count(Company.id))
            .group_by(Company.source_name)
            .order_by(func.count(Company.id).desc()).all()
        ),
    }


def _normalize_name(name: str) -> str:
    import re
    name = name.lower().strip()
    name = re.sub(r"\s+", " ", name)
    for suffix in [" ltd", " limited", " inc", " corp", " llc", " gmbh",
                   " sa", " as", " ab", " bv", " nv", " co", " company"]:
        name = name.removesuffix(suffix)
    return name.strip()
