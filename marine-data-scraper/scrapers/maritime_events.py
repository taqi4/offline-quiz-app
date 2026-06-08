"""
Scraper for major maritime trade events – extracts exhibitor lists (public pages).
Sources: SMM Hamburg, Europort, Nor-Shipping, Seawork, SMW, METSTRADE
"""
import logging
from scrapers.base_scraper import BaseScraper, ScrapedCompany
from processors.categorizer import classify_company, classify_vessel_types

logger = logging.getLogger(__name__)

EVENTS = [
    {
        "name":  "SMM Hamburg",
        "url":   "https://www.smm-hamburg.com/en/exhibitors.html",
        "tag":   "SMM",
    },
    {
        "name":  "Europort",
        "url":   "https://www.europort.nl/en/exhibitors/",
        "tag":   "Europort",
    },
    {
        "name":  "Nor-Shipping",
        "url":   "https://www.nor-shipping.com/exhibitors/",
        "tag":   "Nor-Shipping",
    },
    {
        "name":  "Seawork",
        "url":   "https://www.seawork.com/exhibitors",
        "tag":   "Seawork",
    },
    {
        "name":  "METSTRADE",
        "url":   "https://www.metstrade.com/exhibitors",
        "tag":   "METSTRADE",
    },
    {
        "name":  "Posidonia",
        "url":   "https://www.posidonia-events.com/exhibitors/",
        "tag":   "Posidonia",
    },
    {
        "name":  "Marintec China",
        "url":   "https://www.marintec.com/exhibitors",
        "tag":   "Marintec",
    },
    {
        "name":  "Sea Japan",
        "url":   "https://www.seajapan.ne.jp/english/exhibitors/",
        "tag":   "Sea Japan",
    },
]


class MaritimeEventsScraper(BaseScraper):
    name = "maritime_events"

    def scrape(self):
        for event in EVENTS:
            yield from self._scrape_event(event)

    def _scrape_event(self, event: dict):
        url  = event["url"]
        tag  = event["tag"]
        name = event["name"]

        soup = self.soup(url)
        if soup is None:
            return

        # Generic exhibitor list selectors used by most trade-show platforms
        exhibitors = soup.select(
            "div.exhibitor, div.company, li.exhibitor, "
            "article.exhibitor, div[class*='exhibitor'], "
            "div[class*='company-item'], tr.exhibitor"
        )

        if not exhibitors:
            # Fall back: find all links that look like company pages
            exhibitors = soup.select("a[href*='exhibitor'], a[href*='company']")

        for item in exhibitors:
            sc = self._parse_exhibitor(item, url, tag, name)
            if sc:
                yield sc

    def _parse_exhibitor(self, item, source_url: str,
                          tag: str, event_name: str) -> ScrapedCompany | None:
        name_el = item.select_one("h2, h3, h4, strong, .name, .company-name")
        if not name_el and item.name == "a":
            name_el = item
        if not name_el:
            return None

        name = name_el.get_text(strip=True)
        if not name or len(name) < 3:
            return None

        country_el = item.select_one(".country, .location")
        country    = country_el.get_text(strip=True) if country_el else ""

        desc_el    = item.select_one("p, .description")
        description= desc_el.get_text(strip=True)[:400] if desc_el else ""

        emails  = self.extract_emails(item.get_text())

        # Try to visit exhibitor detail page
        link_el    = item.select_one("a[href]") if item.name != "a" else item
        detail_url = ""
        if link_el:
            href = link_el.get("href", "")
            if href and not href.startswith("http"):
                from urllib.parse import urlparse, urljoin
                detail_url = urljoin(source_url, href)
            else:
                detail_url = href

        sc = ScrapedCompany(
            name=name,
            country=country,
            description=description,
            emails=emails,
            source_name=event_name,
            source_url=detail_url or source_url,
            tags=[tag, "trade_event"],
        )
        sc.company_type = classify_company(name + " " + description)
        sc.vessel_types = classify_vessel_types(description)

        if detail_url and detail_url != source_url:
            sc = self._enrich_detail(sc, detail_url)

        return sc

    def _enrich_detail(self, sc: ScrapedCompany, url: str) -> ScrapedCompany:
        soup = self.soup(url)
        if soup is None:
            return sc

        # Grab website
        for a in soup.select("a[href^='http']"):
            href = a["href"]
            if all(x not in href for x in ["smm-hamburg", "europort", "nor-shipping",
                                             "seawork", "metstrade", "posidonia",
                                             "marintec", "seajapan"]):
                sc.website = href
                break

        # Emails
        for em in self.extract_emails(soup.get_text()):
            if em not in sc.emails:
                sc.emails.append(em)

        # Address
        addr_el = soup.select_one("[class*='address'], [itemprop='address']")
        if addr_el and not sc.address:
            sc.address = addr_el.get_text(strip=True)

        return sc
