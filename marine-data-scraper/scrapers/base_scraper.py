"""Base scraper with rate-limiting, retries, and robots.txt respect."""
import logging
import time
import random
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from fake_useragent import UserAgent

import config
from database.db import get_session, upsert_company, upsert_email
from database.models import Contact, ScrapeLog

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

_ua = UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 Chrome/120 Safari/537.36")


@dataclass
class ScrapedCompany:
    name:         str
    company_type: str        = ""
    website:      str        = ""
    description:  str        = ""
    country:      str        = ""
    city:         str        = ""
    address:      str        = ""
    port:         str        = ""
    fleet_size:   int        = 0
    source_name:  str        = ""
    source_url:   str        = ""
    vessel_types: list       = field(default_factory=list)
    tags:         list       = field(default_factory=list)
    contacts:     list       = field(default_factory=list)   # list of dicts
    emails:       list       = field(default_factory=list)   # list of str


class BaseScraper(ABC):
    name = "base"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(config.DEFAULT_HEADERS)
        self._log = logging.getLogger(self.__class__.__name__)
        self._robots_cache: dict[str, bool] = {}

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self) -> tuple[int, int, int]:
        """Execute the scraper and persist results. Returns (companies, contacts, emails)."""
        log_entry = ScrapeLog(scraper_name=self.name, started_at=datetime.utcnow())
        total_c = total_co = total_e = 0

        with get_session() as session:
            session.add(log_entry)
            session.flush()
            log_id = log_entry.id

        try:
            for company_data in self.scrape():
                c, co, e = self._persist(company_data)
                total_c  += c
                total_co += co
                total_e  += e

            with get_session() as session:
                log = session.get(ScrapeLog, log_id)
                log.status          = "success"
                log.finished_at     = datetime.utcnow()
                log.companies_found = total_c
                log.contacts_found  = total_co
                log.emails_found    = total_e

        except Exception as exc:
            self._log.error("Scraper %s failed: %s", self.name, exc)
            with get_session() as session:
                log = session.get(ScrapeLog, log_id)
                log.status        = "error"
                log.finished_at   = datetime.utcnow()
                log.error_message = str(exc)

        self._log.info("%s done: %d companies, %d contacts, %d emails",
                       self.name, total_c, total_co, total_e)
        return total_c, total_co, total_e

    @abstractmethod
    def scrape(self):
        """Yield ScrapedCompany objects."""

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(config.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
        reraise=True,
    )
    def fetch(self, url: str, **kwargs) -> Optional[requests.Response]:
        if not self._allowed(url):
            self._log.debug("robots.txt blocks %s", url)
            return None
        self._polite_delay()
        self.session.headers["User-Agent"] = _ua.random
        try:
            resp = self.session.get(
                url,
                timeout=config.REQUEST_TIMEOUT,
                allow_redirects=True,
                **kwargs,
            )
            resp.raise_for_status()
            return resp
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (403, 429):
                self._log.warning("Rate-limited / blocked at %s – backing off 60 s", url)
                time.sleep(60)
            raise

    def soup(self, url: str, **kwargs) -> Optional[BeautifulSoup]:
        resp = self.fetch(url, **kwargs)
        if resp is None:
            return None
        return BeautifulSoup(resp.text, "lxml")

    def extract_emails(self, text: str) -> list[str]:
        return list({m.lower() for m in EMAIL_RE.findall(text)})

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _persist(self, sc: ScrapedCompany) -> tuple[int, int, int]:
        with get_session() as session:
            data = {
                "name":         sc.name,
                "company_type": sc.company_type,
                "website":      sc.website,
                "description":  sc.description,
                "country":      sc.country,
                "city":         sc.city,
                "address":      sc.address,
                "port":         sc.port,
                "fleet_size":   sc.fleet_size or None,
                "source_name":  sc.source_name,
                "source_url":   sc.source_url,
            }
            company, created = upsert_company(session, data)

            # Vessel types
            from database.models import VesselType
            for vt_name in sc.vessel_types:
                vt = session.query(VesselType).filter_by(name=vt_name).first()
                if vt and vt not in company.vessel_types:
                    company.vessel_types.append(vt)

            # Tags
            from database.models import Tag
            for tag_name in sc.tags:
                tag = session.query(Tag).filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    session.add(tag)
                    session.flush()
                if tag not in company.tags:
                    company.tags.append(tag)

            # Contacts
            new_contacts = 0
            for cd in sc.contacts:
                exists = session.query(Contact).filter_by(
                    company_id=company.id, email=cd.get("email")
                ).first() if cd.get("email") else None
                if not exists:
                    session.add(Contact(company_id=company.id, **cd))
                    new_contacts += 1
                    if cd.get("email"):
                        upsert_email(session, company.id, cd["email"],
                                     "contact", sc.source_url)

            # Emails
            new_emails = 0
            for addr in sc.emails:
                added = upsert_email(session, company.id, addr,
                                     source_url=sc.source_url)
                new_emails += int(added)

        return int(created), new_contacts, new_emails

    # ------------------------------------------------------------------
    # Politeness
    # ------------------------------------------------------------------

    def _polite_delay(self):
        jitter = random.uniform(0.5, 1.5)
        time.sleep(config.REQUEST_DELAY * jitter)

    def _allowed(self, url: str) -> bool:
        """Very lightweight robots.txt check (checks Disallow for /*)."""
        base = "{0.scheme}://{0.netloc}".format(urlparse(url))
        if base in self._robots_cache:
            return self._robots_cache[base]
        try:
            resp = requests.get(f"{base}/robots.txt", timeout=5)
            blocked = "Disallow: /" in resp.text and "User-agent: *" in resp.text
            # Simple heuristic: if '*' agent has a specific Disallow that includes our path
            self._robots_cache[base] = not blocked
            return not blocked
        except Exception:
            self._robots_cache[base] = True
            return True
