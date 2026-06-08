"""
Scraper for ShipServ – marine marketplace / supplier directory.
URL: https://www.shipserv.com
Targets the public supplier listings.
"""
import logging
from scrapers.base_scraper import BaseScraper, ScrapedCompany
from processors.categorizer import classify_company, classify_vessel_types

logger = logging.getLogger(__name__)

BASE_URL     = "https://www.shipserv.com"
SEARCH_PATHS = [
    "/en/search/suppliers?q=marine+spare+parts",
    "/en/search/suppliers?q=ship+spare+parts",
    "/en/search/suppliers?q=engine+spares",
    "/en/search/suppliers?q=marine+equipment",
    "/en/search/suppliers?q=deck+machinery",
    "/en/search/suppliers?q=navigation+equipment",
    "/en/search/suppliers?q=pumps+valves",
    "/en/search/suppliers?q=fire+safety+marine",
    "/en/search/suppliers?q=ship+management",
    "/en/search/suppliers?q=ship+owner",
    "/en/search/suppliers?q=tanker",
    "/en/search/suppliers?q=bulk+carrier",
]


class ShipServScraper(BaseScraper):
    name = "shipserv"

    def scrape(self):
        for path in SEARCH_PATHS:
            yield from self._scrape_search(BASE_URL + path)

    def _scrape_search(self, search_url: str):
        for page in range(1, 21):    # up to 20 result pages
            url = f"{search_url}&page={page}"
            soup = self.soup(url)
            if soup is None:
                break

            cards = soup.select(
                "div.supplier-card, div.company-card, "
                "div[class*='supplier'], li[class*='supplier']"
            )
            if not cards:
                break

            for card in cards:
                sc = self._parse_card(card, search_url)
                if sc:
                    yield sc

            next_btn = soup.select_one("a[rel='next'], button[aria-label='Next']")
            if not next_btn:
                break

    def _parse_card(self, card, source_url: str) -> ScrapedCompany | None:
        name_el = card.select_one("h2, h3, .supplier-name, .company-name, strong")
        if not name_el:
            return None
        name = name_el.get_text(strip=True)
        if not name:
            return None

        country_el = card.select_one(".country, .location, [class*='country']")
        country = country_el.get_text(strip=True) if country_el else ""

        desc_el = card.select_one("p, .description, .summary")
        description = desc_el.get_text(strip=True)[:500] if desc_el else ""

        emails = self.extract_emails(card.get_text())

        # Try to follow supplier detail link
        link_el = card.select_one("a[href]")
        detail_url = ""
        if link_el:
            href = link_el.get("href", "")
            if href and not href.startswith("http"):
                href = BASE_URL + href
            detail_url = href

        sc = ScrapedCompany(
            name=name,
            country=country,
            description=description,
            emails=emails,
            source_name="ShipServ",
            source_url=detail_url or source_url,
        )
        sc.company_type = classify_company(name + " " + description)
        sc.vessel_types = classify_vessel_types(description)

        if detail_url:
            sc = self._enrich_detail(sc, detail_url)

        return sc

    def _enrich_detail(self, sc: ScrapedCompany, url: str) -> ScrapedCompany:
        soup = self.soup(url)
        if soup is None:
            return sc

        # Website external link
        for a in soup.select("a[href^='http']"):
            href = a["href"]
            if "shipserv.com" not in href:
                sc.website = href
                break

        # Bulk email scrape
        for em in self.extract_emails(soup.get_text()):
            if em not in sc.emails:
                sc.emails.append(em)

        # Contact person
        for block in soup.select(".contact-person, .contact-info, [class*='contact']"):
            name_el  = block.select_one("strong, .name, h4")
            email_el = block.select_one("a[href^='mailto:']")
            cname  = name_el.get_text(strip=True)  if name_el  else ""
            cemail = ""
            if email_el:
                cemail = email_el["href"].replace("mailto:", "").strip()
            if cname or cemail:
                sc.contacts.append({"name": cname, "email": cemail, "source_url": url})

        return sc
