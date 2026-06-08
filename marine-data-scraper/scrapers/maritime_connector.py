"""
Scraper for Maritime Connector – a public marine industry directory.
URL: https://maritime-connector.com
Scrapes company listings, contact details, and emails.
"""
import logging
from scrapers.base_scraper import BaseScraper, ScrapedCompany
from processors.categorizer import classify_company, classify_vessel_types

logger = logging.getLogger(__name__)

BASE_URL = "https://maritime-connector.com"
COMPANY_CATEGORIES = [
    "/companies/ship-management/",
    "/companies/shipowners/",
    "/companies/shipyards/",
    "/companies/ship-chandlers/",
    "/companies/shipping-agents/",
    "/companies/maritime-equipment/",
    "/companies/port-authorities/",
    "/companies/insurance/",
    "/companies/classification-societies/",
    "/companies/maritime-law/",
    "/companies/surveyors/",
    "/companies/brokers/",
]


class MaritimeConnectorScraper(BaseScraper):
    name = "maritime_connector"

    def scrape(self):
        for category_path in COMPANY_CATEGORIES:
            yield from self._scrape_category(BASE_URL + category_path)

    def _scrape_category(self, category_url: str):
        page = 1
        while True:
            url = f"{category_url}?page={page}" if page > 1 else category_url
            soup = self.soup(url)
            if soup is None:
                break

            listings = soup.select("div.company-listing, div.company-card, article.company")
            if not listings:
                # Try alternate selectors
                listings = soup.select("div.list-item, div.directory-item")

            if not listings:
                logger.debug("No listings found at %s", url)
                break

            for item in listings:
                company = self._parse_listing(item, category_url)
                if company:
                    # Visit company detail page for more info
                    link = item.select_one("a[href*='/company/'], a[href*='/companies/']")
                    if link and link.get("href"):
                        detail_url = link["href"]
                        if not detail_url.startswith("http"):
                            detail_url = BASE_URL + detail_url
                        company = self._enrich_from_detail(company, detail_url)
                    yield company

            # Pagination
            next_btn = soup.select_one("a.next, a[rel='next'], li.next > a")
            if not next_btn:
                break
            page += 1
            if page > 50:    # safety cap
                break

    def _parse_listing(self, item, source_url: str) -> ScrapedCompany | None:
        name_el = item.select_one("h2, h3, .company-name, .name")
        if not name_el:
            return None
        name = name_el.get_text(strip=True)
        if not name:
            return None

        country = ""
        country_el = item.select_one(".country, .location, [class*='country']")
        if country_el:
            country = country_el.get_text(strip=True)

        description = ""
        desc_el = item.select_one(".description, .summary, p")
        if desc_el:
            description = desc_el.get_text(strip=True)[:500]

        emails = self.extract_emails(item.get_text())

        company = ScrapedCompany(
            name=name,
            country=country,
            description=description,
            emails=emails,
            source_name="Maritime Connector",
            source_url=source_url,
        )
        company.company_type = classify_company(name + " " + description)
        company.vessel_types = classify_vessel_types(name + " " + description)
        return company

    def _enrich_from_detail(self, company: ScrapedCompany, url: str) -> ScrapedCompany:
        soup = self.soup(url)
        if soup is None:
            return company

        company.source_url = url

        # Website
        for a in soup.select("a[href]"):
            href = a["href"]
            if "maritime-connector" not in href and href.startswith("http") and "." in href:
                if any(w in a.get_text().lower() for w in ["website", "www", "visit"]):
                    company.website = href
                    break

        # Address / location
        addr_el = soup.select_one(".address, [class*='address'], [itemprop='address']")
        if addr_el:
            company.address = addr_el.get_text(strip=True)

        city_el = soup.select_one("[class*='city'], [itemprop='addressLocality']")
        if city_el:
            company.city = city_el.get_text(strip=True)

        # Contacts
        for contact_block in soup.select(".contact, .person, [class*='contact-person']"):
            name_el  = contact_block.select_one(".name, strong, b")
            title_el = contact_block.select_one(".title, .position, em")
            email_el = contact_block.select_one("a[href^='mailto:']")

            cname  = name_el.get_text(strip=True)  if name_el  else ""
            ctitle = title_el.get_text(strip=True) if title_el else ""
            cemail = ""
            if email_el:
                cemail = email_el["href"].replace("mailto:", "").strip()

            if cname or cemail:
                company.contacts.append({
                    "name":  cname,
                    "title": ctitle,
                    "email": cemail,
                    "source_url": url,
                })

        # Bulk email extraction from full page text
        page_text = soup.get_text()
        for em in self.extract_emails(page_text):
            if em not in company.emails:
                company.emails.append(em)

        return company
