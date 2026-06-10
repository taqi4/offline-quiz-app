"""SQLAlchemy ORM models for marine company data."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float,
    Boolean, ForeignKey, Table, Index, create_engine
)
from sqlalchemy.orm import relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


# Many-to-many: company <-> vessel_type
company_vessel_type = Table(
    "company_vessel_type",
    Base.metadata,
    Column("company_id", Integer, ForeignKey("companies.id"), primary_key=True),
    Column("vessel_type_id", Integer, ForeignKey("vessel_types.id"), primary_key=True),
)

# Many-to-many: company <-> tag
company_tag = Table(
    "company_tag",
    Base.metadata,
    Column("company_id", Integer, ForeignKey("companies.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class Company(Base):
    __tablename__ = "companies"

    id             = Column(Integer, primary_key=True)
    name           = Column(String(500), nullable=False, index=True)
    name_normalized= Column(String(500), index=True)        # lowercased/stripped for dedup
    company_type   = Column(String(100), index=True)        # shipowner, shipyard, agent …
    website        = Column(String(500))
    description    = Column(Text)

    # Direct outreach channels
    phone          = Column(String(100))
    fax            = Column(String(100))
    linkedin       = Column(String(500))
    twitter        = Column(String(500))
    facebook       = Column(String(500))

    # Firmographics
    employees      = Column(Integer)                        # headcount if known
    year_founded   = Column(Integer)
    revenue_range  = Column(String(100))                    # e.g. "$10M-$50M"

    # Marketing intelligence
    lead_score     = Column(Float, default=0.0, index=True) # 0-100 sales priority
    email_pattern  = Column(String(100))                    # e.g. "{first}.{last}"
    region         = Column(String(100), index=True)        # Europe, Asia, Middle East …
    country_code   = Column(String(5))                      # ISO-2
    last_enriched  = Column(DateTime)                       # website enrichment timestamp

    # Location
    country        = Column(String(100), index=True)
    city           = Column(String(200))
    address        = Column(Text)
    port           = Column(String(200))                    # home port / base port

    # Fleet info
    fleet_size     = Column(Integer)
    fleet_dwt      = Column(Float)                         # total DWT if known

    # Source metadata
    source_name    = Column(String(200))
    source_url     = Column(String(1000))
    date_scraped   = Column(DateTime, default=datetime.utcnow, index=True)
    date_updated   = Column(DateTime, onupdate=datetime.utcnow)
    is_active      = Column(Boolean, default=True)

    # Relationships
    contacts       = relationship("Contact", back_populates="company",
                                  cascade="all, delete-orphan")
    emails         = relationship("Email", back_populates="company",
                                  cascade="all, delete-orphan")
    vessel_types   = relationship("VesselType", secondary=company_vessel_type,
                                  back_populates="companies")
    tags           = relationship("Tag", secondary=company_tag,
                                  back_populates="companies")
    vessels        = relationship("Vessel", back_populates="company",
                                  cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_company_country_type", "country", "company_type"),
    )

    def __repr__(self):
        return f"<Company {self.name!r} [{self.company_type}] {self.country}>"


class Contact(Base):
    __tablename__ = "contacts"

    id          = Column(Integer, primary_key=True)
    company_id  = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    name        = Column(String(300))
    first_name  = Column(String(150))
    last_name   = Column(String(150))
    title       = Column(String(200))          # "Fleet Manager", "Purchasing Director" …
    department  = Column(String(200))          # purchasing, technical, management …
    seniority   = Column(String(50))           # c_level, vp, director, manager, staff
    is_decision_maker = Column(Boolean, default=False, index=True)
    phone       = Column(String(100))
    mobile      = Column(String(100))
    email       = Column(String(300), index=True)
    email_status= Column(String(50))           # verified, pattern_guess, unverified
    linkedin    = Column(String(500))
    notes       = Column(Text)
    source_url  = Column(String(1000))
    date_scraped= Column(DateTime, default=datetime.utcnow)

    company     = relationship("Company", back_populates="contacts")

    def __repr__(self):
        return f"<Contact {self.name!r} @ {self.company_id}>"


class Email(Base):
    """Standalone email records (may or may not map to a named Contact)."""
    __tablename__ = "emails"

    id          = Column(Integer, primary_key=True)
    company_id  = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    address     = Column(String(300), nullable=False, index=True)
    email_type  = Column(String(50))    # "general", "purchasing", "technical", "sales"
    confidence  = Column(Float, default=1.0)    # 0-1 extraction confidence
    source_url  = Column(String(1000))
    is_valid    = Column(Boolean, default=True)
    mx_valid    = Column(Boolean)               # domain has MX records
    is_role     = Column(Boolean, default=False)# role address (info@, sales@)
    is_free     = Column(Boolean, default=False)# gmail/yahoo etc.
    domain      = Column(String(255), index=True)
    date_scraped= Column(DateTime, default=datetime.utcnow)

    company     = relationship("Company", back_populates="emails")


class VesselType(Base):
    __tablename__ = "vessel_types"

    id          = Column(Integer, primary_key=True)
    name        = Column(String(100), unique=True, nullable=False)
    description = Column(Text)

    companies   = relationship("Company", secondary=company_vessel_type,
                               back_populates="vessel_types")
    vessels     = relationship("Vessel", back_populates="vessel_type")


class Vessel(Base):
    """Individual vessels linked to an owner/manager company."""
    __tablename__ = "vessels"

    id            = Column(Integer, primary_key=True)
    company_id    = Column(Integer, ForeignKey("companies.id"), index=True)
    vessel_type_id= Column(Integer, ForeignKey("vessel_types.id"), index=True)

    name          = Column(String(300), index=True)
    imo           = Column(String(20), unique=True)     # IMO number
    mmsi          = Column(String(20))
    flag          = Column(String(100))
    built         = Column(Integer)                     # year built
    gt            = Column(Float)                       # gross tonnage
    dwt           = Column(Float)
    length        = Column(Float)
    beam          = Column(Float)
    status        = Column(String(50))                  # active, laid-up, scrapped

    source_url    = Column(String(1000))
    date_scraped  = Column(DateTime, default=datetime.utcnow)

    company       = relationship("Company", back_populates="vessels")
    vessel_type   = relationship("VesselType", back_populates="vessels")

    __table_args__ = (
        Index("ix_vessel_name_flag", "name", "flag"),
    )


class Tag(Base):
    """Free-form tags for flexible filtering (e.g. "SMM 2024", "bulk", "Greek owner")."""
    __tablename__ = "tags"

    id   = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)

    companies = relationship("Company", secondary=company_tag,
                             back_populates="tags")


class ScrapeLog(Base):
    """Audit trail of every scraper run."""
    __tablename__ = "scrape_logs"

    id             = Column(Integer, primary_key=True)
    scraper_name   = Column(String(200), index=True)
    source_url     = Column(String(1000))
    started_at     = Column(DateTime, default=datetime.utcnow)
    finished_at    = Column(DateTime)
    companies_found= Column(Integer, default=0)
    contacts_found = Column(Integer, default=0)
    emails_found   = Column(Integer, default=0)
    status         = Column(String(50))     # "success", "error", "partial"
    error_message  = Column(Text)


class Outreach(Base):
    """Tracks sales outreach activity per company/contact for campaign management."""
    __tablename__ = "outreach"

    id           = Column(Integer, primary_key=True)
    company_id   = Column(Integer, ForeignKey("companies.id"), index=True)
    contact_id   = Column(Integer, ForeignKey("contacts.id"), index=True)
    campaign     = Column(String(200), index=True)
    channel      = Column(String(50))       # email, linkedin, phone
    status       = Column(String(50), index=True)  # queued, sent, opened, replied, bounced, converted
    subject      = Column(String(500))
    sent_at      = Column(DateTime)
    opened_at    = Column(DateTime)
    replied_at   = Column(DateTime)
    notes        = Column(Text)
    created_at   = Column(DateTime, default=datetime.utcnow)


class SavedSegment(Base):
    """Reusable saved marketing segments (filters) for repeatable list-building."""
    __tablename__ = "saved_segments"

    id           = Column(Integer, primary_key=True)
    name         = Column(String(200), unique=True, nullable=False)
    description  = Column(Text)
    filters_json = Column(Text)             # serialized search filters
    created_at   = Column(DateTime, default=datetime.utcnow)
    last_run     = Column(DateTime)
    match_count  = Column(Integer, default=0)
