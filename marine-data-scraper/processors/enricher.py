"""
Website enrichment — visits a company's own website to harvest deeper data:
contact/about/team pages, phones, social links, additional emails.

This turns a thin directory listing into a rich, marketing-ready profile.
"""
import re
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

import config
from processors.email_extractor import extract_emails, validate_mx
from processors.contact_classifier import enrich_contact

logger = logging.getLogger(__name__)

_ua = UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 Chrome/120 Safari/537.36")

# Sub-pages most likely to contain contact data
CONTACT_PATHS = [
    "", "contact", "contact-us", "contacts", "about", "about-us",
    "team", "our-team", "management", "people", "company", "imprint",
    "legal-notice", "impressum", "get-in-touch",
]

PHONE_RE = re.compile(
    r"(?:(?:\+|00)\d{1,3}[\s.\-]?)?(?:\(?\d{2,4}\)?[\s.\-]?){2,4}\d{2,4}"
)

SOCIAL_PATTERNS = {
    "linkedin": re.compile(r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/[^\s\"'<>]+", re.I),
    "twitter":  re.compile(r"https?://(?:www\.)?(?:twitter|x)\.com/[^\s\"'<>]+", re.I),
    "facebook": re.compile(r"https?://(?:www\.)?facebook\.com/[^\s\"'<>]+", re.I),
}

# Free email providers (low B2B value)
FREE_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
    "protonmail.com", "icloud.com", "gmx.com", "mail.com", "yandex.com",
    "live.com", "msn.com", "qq.com", "163.com", "126.com",
}

ROLE_LOCALS = {
    "info", "sales", "contact", "admin", "office", "enquiries", "support",
    "hello", "mail", "marketing", "purchasing", "procurement", "technical",
    "service", "accounts", "general", "crewing", "operations",
}


class WebsiteEnricher:
    def __init__(self, do_mx_check: bool = False):
        self.session = requests.Session()
        self.session.headers.update(config.DEFAULT_HEADERS)
        self.do_mx_check = do_mx_check
        self._mx_cache: dict[str, bool] = {}

    def enrich(self, session, company) -> dict:
        """
        Crawl a company's website and update the ORM company in place.
        Returns a summary dict of what was found.
        """
        if not company.website:
            return {"skipped": "no website"}

        base = self._normalize_url(company.website)
        if not base:
            return {"skipped": "bad url"}

        found_emails: dict[str, dict] = {}
        found_phones: set[str] = set()
        socials: dict[str, str] = {}
        contacts_added = 0

        domain = urlparse(base).netloc.replace("www.", "")

        for path in CONTACT_PATHS:
            url = urljoin(base + "/", path)
            html = self._get(url)
            if not html:
                continue
            soup = BeautifulSoup(html, "lxml")
            text = soup.get_text(" ")

            # Emails
            for em in extract_emails(text):
                addr = em["address"]
                if addr not in found_emails:
                    found_emails[addr] = em

            # mailto links (high confidence)
            for a in soup.select("a[href^='mailto:']"):
                addr = a["href"].replace("mailto:", "").split("?")[0].strip().lower()
                if addr and "@" in addr and addr not in found_emails:
                    found_emails[addr] = {"address": addr, "email_type": "general",
                                          "confidence": 1.0}

            # Phones
            for m in PHONE_RE.findall(text):
                cleaned = re.sub(r"\s+", " ", m).strip()
                digits = re.sub(r"\D", "", cleaned)
                if 7 <= len(digits) <= 15:
                    found_phones.add(cleaned)

            # Socials
            for name, pat in SOCIAL_PATTERNS.items():
                if name not in socials:
                    m = pat.search(html)
                    if m:
                        socials[name] = m.group(0).rstrip("/\"'")

            # Team/contact people blocks
            contacts_added += self._extract_people(session, company, soup, url)

        # ---- Persist findings -------------------------------------------
        from database.db import upsert_email

        for addr, meta in found_emails.items():
            edomain = addr.split("@", 1)[1] if "@" in addr else ""
            is_free = edomain in FREE_DOMAINS
            local = addr.split("@", 1)[0]
            is_role = local in ROLE_LOCALS
            mx = self._check_mx(edomain) if self.do_mx_check else None

            added = upsert_email(
                session, company.id, addr,
                email_type=meta.get("email_type", "general"),
                source_url=base, confidence=meta.get("confidence", 0.8),
            )
            if added:
                # update the just-added Email row with enrichment flags
                from database.models import Email
                row = (session.query(Email)
                       .filter_by(company_id=company.id, address=addr)
                       .first())
                if row:
                    row.domain = edomain
                    row.is_free = is_free
                    row.is_role = is_role
                    row.mx_valid = mx

        if found_phones and not company.phone:
            company.phone = sorted(found_phones, key=len, reverse=True)[0]
        company.linkedin = company.linkedin or socials.get("linkedin")
        company.twitter  = company.twitter  or socials.get("twitter")
        company.facebook = company.facebook or socials.get("facebook")
        company.last_enriched = datetime.utcnow()

        session.commit()

        return {
            "emails":   len(found_emails),
            "phones":   len(found_phones),
            "socials":  list(socials.keys()),
            "contacts": contacts_added,
        }

    # ------------------------------------------------------------------

    def _extract_people(self, session, company, soup, url) -> int:
        from database.models import Contact
        added = 0
        blocks = soup.select(
            ".team-member, .member, .person, .staff, .employee, "
            "[class*='team'], [class*='person'], [class*='contact-card']"
        )
        for b in blocks:
            name_el = b.select_one("h2, h3, h4, .name, strong, b")
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name or len(name) < 4 or len(name.split()) > 5:
                continue
            title_el = b.select_one(".title, .position, .role, em, .job")
            title = title_el.get_text(strip=True) if title_el else ""
            email_el = b.select_one("a[href^='mailto:']")
            email = ""
            if email_el:
                email = email_el["href"].replace("mailto:", "").split("?")[0].strip()

            exists = (session.query(Contact)
                      .filter_by(company_id=company.id, name=name).first())
            if exists:
                continue
            contact = Contact(company_id=company.id, name=name, title=title,
                              email=email or None, source_url=url,
                              email_status="verified" if email else None)
            enrich_contact(contact)
            session.add(contact)
            added += 1
        return added

    def _get(self, url: str) -> str | None:
        try:
            self.session.headers["User-Agent"] = _ua.random
            r = self.session.get(url, timeout=config.REQUEST_TIMEOUT,
                                 allow_redirects=True)
            if r.status_code == 200 and "text/html" in r.headers.get("content-type", ""):
                return r.text
        except Exception as e:
            logger.debug("enrich GET failed %s: %s", url, e)
        return None

    def _check_mx(self, domain: str) -> bool:
        if domain in self._mx_cache:
            return self._mx_cache[domain]
        ok = validate_mx(domain)
        self._mx_cache[domain] = ok
        return ok

    @staticmethod
    def _normalize_url(url: str) -> str | None:
        url = url.strip()
        if not url:
            return None
        if not url.startswith("http"):
            url = "https://" + url
        p = urlparse(url)
        if not p.netloc:
            return None
        return f"{p.scheme}://{p.netloc}"


def enrich_pending(session, limit: int = 100, do_mx_check: bool = False) -> int:
    """Enrich companies that have a website but were never enriched."""
    from database.models import Company
    enricher = WebsiteEnricher(do_mx_check=do_mx_check)
    companies = (session.query(Company)
                 .filter(Company.website.isnot(None))
                 .filter(Company.last_enriched.is_(None))
                 .limit(limit).all())
    count = 0
    for c in companies:
        try:
            result = enricher.enrich(session, c)
            logger.info("Enriched %s: %s", c.name, result)
            count += 1
        except Exception as e:
            logger.warning("Enrich failed for %s: %s", c.name, e)
    return count
