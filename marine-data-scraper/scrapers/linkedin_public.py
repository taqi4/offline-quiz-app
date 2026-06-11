"""
LinkedIn public company page scraper.

LinkedIn heavily blocks automated access so we use two approaches:
  1. DuckDuckGo to find LinkedIn company page URLs for known company names
  2. Fetch the public (non-logged-in) LinkedIn company page for:
       - About description
       - Headcount
       - Industry / specialties
       - HQ location
       - Follower count (proxy for company size)

This does NOT log in, does NOT scrape individual profiles, and respects
LinkedIn's public pages only. Rate-limited to 1 request per 10 seconds.

Usage: enriches existing companies in the DB that already have a name
       but no LinkedIn URL.
"""
import re
import time
import logging
from urllib.parse import quote_plus
from scrapers.base_scraper import BaseScraper, ScrapedCompany

logger = logging.getLogger(__name__)

LI_BASE  = "https://www.linkedin.com/company/"
DDG_HTML = "https://html.duckduckgo.com/html/?q="

EMPLOYEE_RE = re.compile(r"([\d,]+)\s+(?:employees?|followers?)", re.I)
FOUNDED_RE  = re.compile(r"founded\s+(?:in\s+)?(\d{4})", re.I)


class LinkedInPublicScraper(BaseScraper):
    name = "linkedin_public"

    def __init__(self, limit: int = 100):
        super().__init__()
        self.limit = limit

    def scrape(self):
        """Enrich existing companies that have no LinkedIn URL."""
        from database.db import get_session
        from database.models import Company
        with get_session() as session:
            companies = (session.query(Company)
                         .filter(Company.linkedin.is_(None))
                         .filter(Company.website.isnot(None))
                         .order_by(Company.lead_score.desc())
                         .limit(self.limit)
                         .all())
            names = [(c.id, c.name, c.country or "") for c in companies]

        for company_id, name, country in names:
            li_url = self._find_linkedin_url(name, country)
            if not li_url:
                continue
            time.sleep(10)   # very conservative — LinkedIn rate-limits hard
            info = self._scrape_li_page(li_url)
            if info:
                self._update_company(company_id, li_url, info)
                # Yield a minimal ScrapedCompany so the base persist() runs
                sc = ScrapedCompany(
                    name=name,
                    linkedin=li_url,
                    source_name="LinkedIn Public",
                    source_url=li_url,
                )
                if info.get("employees"):
                    sc.employees = info["employees"]
                if info.get("description"):
                    sc.description = info["description"]
                yield sc

    def _find_linkedin_url(self, company_name: str, country: str) -> str | None:
        query = f'site:linkedin.com/company "{company_name}" {country} shipping'
        soup = self.soup(DDG_HTML + quote_plus(query))
        if not soup:
            return None
        for a in soup.select("a.result__a, a.result__url"):
            href = a.get("href", "")
            if "linkedin.com/company/" in href:
                m = re.search(r"linkedin\.com/company/([^/?&\"]+)", href)
                if m:
                    return f"{LI_BASE}{m.group(1)}/"
        return None

    def _scrape_li_page(self, url: str) -> dict | None:
        soup = self.soup(url, headers={
            "Accept-Language": "en-US,en;q=0.9",
        })
        if not soup:
            return None

        info = {}
        text = soup.get_text(" ")

        # Description from meta or about section
        meta = soup.find("meta", {"name": "description"})
        if meta and meta.get("content"):
            info["description"] = meta["content"][:500]

        # Employee count
        m = EMPLOYEE_RE.search(text)
        if m:
            try:
                info["employees"] = int(m.group(1).replace(",", ""))
            except ValueError:
                pass

        # Founded year
        m = FOUNDED_RE.search(text)
        if m:
            try:
                info["year_founded"] = int(m.group(1))
            except ValueError:
                pass

        # HQ location
        hq_el = soup.select_one("[class*='headquarters'], [data-field='hq']")
        if hq_el:
            info["city"] = hq_el.get_text(strip=True)

        return info if info else None

    def _update_company(self, company_id: int, li_url: str, info: dict):
        from database.db import get_session
        from database.models import Company
        with get_session() as session:
            c = session.get(Company, company_id)
            if not c:
                return
            c.linkedin = li_url
            if info.get("employees") and not c.employees:
                c.employees = info["employees"]
            if info.get("year_founded") and not c.year_founded:
                c.year_founded = info["year_founded"]
            if info.get("description") and not c.description:
                c.description = info["description"]
            if info.get("city") and not c.city:
                c.city = info["city"]
