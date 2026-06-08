"""
Scraper for public port and shipping agent directories.
Sources: World Port Index, Port Authority websites, BIMCO member directory (public pages).
"""
import logging
from scrapers.base_scraper import BaseScraper, ScrapedCompany
from processors.categorizer import classify_company

logger = logging.getLogger(__name__)

SOURCES = [
    {
        "name":    "FONASBA Directory",
        "url":     "https://www.fonasba.com/members/",
        "type":    "agent",
        "country": "",
    },
    {
        "name":    "BIMCO Members",
        "url":     "https://www.bimco.org/about-bimco/members",
        "type":    "shipping",
        "country": "",
    },
    {
        "name":    "ICS Member Organisations",
        "url":     "https://www.ics-shipping.org/about-us/member-organisations/",
        "type":    "association",
        "country": "",
    },
    {
        "name":    "Intercargo Members",
        "url":     "https://www.intercargo.org/members/",
        "type":    "bulk_carrier",
        "country": "",
    },
    {
        "name":    "INTERTANKO Members",
        "url":     "https://www.intertanko.com/about/members",
        "type":    "tanker",
        "country": "",
    },
]


class PortDirectoryScraper(BaseScraper):
    name = "port_directory"

    def scrape(self):
        for source in SOURCES:
            yield from self._scrape_source(source)

    def _scrape_source(self, source: dict):
        url  = source["url"]
        soup = self.soup(url)
        if soup is None:
            return

        # Generic member/listing selectors
        items = soup.select(
            "li.member, div.member, tr.member, "
            "div[class*='member-item'], li[class*='member'], "
            "div.company, li.company, div.listing-item"
        )

        if not items:
            # Fall back to any list items with company-like text
            items = soup.select("ul.members li, ol.members li, table.members tr")

        for item in items:
            name_el = item.select_one("strong, b, h3, h4, .name, td:first-child")
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name or len(name) < 3:
                continue

            country_el = item.select_one(".country, .location, td:nth-child(2)")
            country    = country_el.get_text(strip=True) if country_el else ""

            emails = self.extract_emails(item.get_text())

            # Website link
            website = ""
            for a in item.select("a[href^='http']"):
                href = a["href"]
                if source["url"].split("/")[2] not in href:
                    website = href
                    break

            sc = ScrapedCompany(
                name=name,
                country=country,
                website=website,
                emails=emails,
                company_type=source.get("type", ""),
                source_name=source["name"],
                source_url=url,
                tags=[source["name"].replace(" ", "_").lower()],
            )
            sc.company_type = classify_company(name) or source.get("type", "")
            yield sc
