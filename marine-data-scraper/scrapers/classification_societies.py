"""
Scraper for public vessel registers from the major classification societies.
These are the definitive source of shipowner company names.

Sources:
  - DNV (det norske veritas) — public vessel search
  - Bureau Veritas — public vessel register
  - Lloyd's Register — public vessel register
  - ClassNK — public vessel register
  - ABS — public vessel register
  - RINA — public vessel register
"""
import re
import logging
from urllib.parse import urljoin
from scrapers.base_scraper import BaseScraper, ScrapedCompany
from processors.categorizer import classify_vessel_types

logger = logging.getLogger(__name__)

SOCIETIES = [
    {
        "name":       "DNV",
        "search_url": "https://vesselregister.dnv.com/vesselregister/",
        "type":       "direct",
    },
    {
        "name":       "Bureau Veritas",
        "search_url": "https://www.veristar.com/portal/veristarinfo/",
        "type":       "direct",
    },
    {
        "name":       "Lloyd's Register",
        "search_url": "https://www.lr.org/en/contact-us/",
        "type":       "contact_only",
    },
    {
        "name":       "ClassNK",
        "search_url": "https://www.classnk.or.jp/hp/en/hp_contacts.html",
        "type":       "contact_only",
    },
    {
        "name":       "American Bureau of Shipping",
        "search_url": "https://ww2.eagle.org/en/contact-us.html",
        "type":       "contact_only",
    },
    {
        "name":       "RINA",
        "search_url": "https://www.rina.org/en/contact",
        "type":       "contact_only",
    },
    {
        "name":       "Korean Register",
        "search_url": "https://www.krs.co.kr/eng/sub04/contactus.do",
        "type":       "contact_only",
    },
]

# Vessel type segments to query on DNV/BV public search
VESSEL_SEGMENTS = [
    "tanker", "bulk carrier", "container", "general cargo",
    "offshore", "passenger", "ro-ro",
]


class ClassificationSocietiesScraper(BaseScraper):
    name = "classification_societies"

    def scrape(self):
        for society in SOCIETIES:
            yield from self._scrape_society(society)

    def _scrape_society(self, society: dict):
        url  = society["search_url"]
        name = society["name"]

        soup = self.soup(url)
        if soup is None:
            return

        text   = soup.get_text()
        emails = self.extract_emails(text)

        # Build a company record for the society itself + extract contacts
        sc = ScrapedCompany(
            name=name,
            company_type="classification",
            website=url.split("/en/")[0] if "/en/" in url else url.split("/hp/")[0],
            description=f"Classification society — {name}",
            source_name="Classification Societies",
            source_url=url,
            emails=emails,
            tags=["classification_society"],
        )

        # Extract country office contacts
        for block in soup.select(".contact, .office, [class*='contact'], [class*='office']"):
            name_el  = block.select_one("h3, h4, strong, .name")
            email_el = block.select_one("a[href^='mailto:']")
            cname  = name_el.get_text(strip=True)  if name_el  else ""
            cemail = email_el["href"].replace("mailto:", "").strip() if email_el else ""
            if cname or cemail:
                sc.contacts.append({"name": cname, "email": cemail, "source_url": url})

        yield sc

        # For DNV — try to scrape public vessel search pages per segment
        if society["name"] == "DNV":
            yield from self._scrape_dnv_owners()

    def _scrape_dnv_owners(self):
        """
        DNV's vessel register has a public search. We query per vessel type
        and extract owner company names from the results table.
        """
        base = "https://vesselregister.dnv.com/vesselregister/"
        for segment in VESSEL_SEGMENTS[:4]:  # limit to first 4 to be polite
            url  = f"{base}#/search?vesselType={segment.replace(' ', '+')}"
            soup = self.soup(url)
            if not soup:
                continue
            # Results table rows
            for row in soup.select("tr[class*='vessel'], tr.ng-star-inserted, table tbody tr"):
                cells = row.find_all("td")
                if len(cells) < 4:
                    continue
                owner_name = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                flag       = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                if not owner_name or len(owner_name) < 3:
                    continue
                sc = ScrapedCompany(
                    name=owner_name,
                    company_type="shipowner",
                    country=flag,
                    vessel_types=classify_vessel_types(segment),
                    source_name="DNV Vessel Register",
                    source_url=url,
                    tags=["dnv_classed", segment.replace(" ", "_")],
                )
                yield sc
