"""
Generic configurable directory scraper – can target any list-style marine directory.
Uses CSS selectors from config to extract company name, country, email, website.
"""
import logging
from typing import Optional
from scrapers.base_scraper import BaseScraper, ScrapedCompany
from processors.categorizer import classify_company, classify_vessel_types

logger = logging.getLogger(__name__)

# Additional public marine directories to crawl
DIRECTORIES = [
    {
        "name":         "Marine Insight Companies",
        "start_url":    "https://www.marineinsight.com/maritime-companies/",
        "item_sel":     "article, div.post",
        "name_sel":     "h2, h3, .entry-title",
        "country_sel":  ".country",
        "desc_sel":     "p",
        "link_sel":     "h2 a, h3 a, .entry-title a",
    },
    {
        "name":         "The Maritime Standard Directory",
        "start_url":    "https://www.themaritimestandard.com/company-directory/",
        "item_sel":     "div.company-listing, div.directory-item",
        "name_sel":     "h3, .company-name",
        "country_sel":  ".country, .location",
        "desc_sel":     ".description, p",
        "link_sel":     "a.read-more, h3 a",
    },
    {
        "name":         "Maritime Executive Companies",
        "start_url":    "https://www.maritime-executive.com/company-profiles",
        "item_sel":     "article, div.profile-item",
        "name_sel":     "h2, h3",
        "country_sel":  ".location",
        "desc_sel":     "p",
        "link_sel":     "h2 a, h3 a",
    },
    {
        "name":         "Splash247 Shipping Companies",
        "start_url":    "https://splash247.com/category/sector/",
        "item_sel":     "article",
        "name_sel":     "h2",
        "country_sel":  ".location",
        "desc_sel":     ".entry-summary, p",
        "link_sel":     "h2 a",
    },
]


class GenericDirectoryScraper(BaseScraper):
    name = "generic_directory"

    def scrape(self):
        for dir_config in DIRECTORIES:
            yield from self._scrape_directory(dir_config)

    def _scrape_directory(self, cfg: dict):
        page = 1
        base_url  = cfg["start_url"]
        page_urls = [base_url]

        for url in page_urls:
            soup = self.soup(url)
            if soup is None:
                continue

            items = soup.select(cfg.get("item_sel", "article"))
            for item in items:
                sc = self._parse_item(item, cfg, url)
                if sc:
                    yield sc

            # Look for more pages
            if page <= 5:
                next_el = soup.select_one("a[rel='next'], a.next")
                if next_el and next_el.get("href"):
                    href = next_el["href"]
                    if not href.startswith("http"):
                        from urllib.parse import urljoin
                        href = urljoin(url, href)
                    if href not in page_urls:
                        page_urls.append(href)
                        page += 1

    def _parse_item(self, item, cfg: dict, source_url: str) -> Optional[ScrapedCompany]:
        name_el = item.select_one(cfg.get("name_sel", "h2"))
        if not name_el:
            return None
        name = name_el.get_text(strip=True)
        if not name or len(name) < 3:
            return None

        country_el  = item.select_one(cfg.get("country_sel", ".country"))
        country     = country_el.get_text(strip=True) if country_el else ""

        desc_el     = item.select_one(cfg.get("desc_sel", "p"))
        description = desc_el.get_text(strip=True)[:400] if desc_el else ""

        emails = self.extract_emails(item.get_text())

        link_el    = item.select_one(cfg.get("link_sel", "a"))
        detail_url = ""
        if link_el and link_el.get("href"):
            href = link_el["href"]
            if not href.startswith("http"):
                from urllib.parse import urljoin
                href = urljoin(source_url, href)
            detail_url = href

        sc = ScrapedCompany(
            name=name,
            country=country,
            description=description,
            emails=emails,
            source_name=cfg["name"],
            source_url=detail_url or source_url,
        )
        sc.company_type = classify_company(name + " " + description)
        sc.vessel_types = classify_vessel_types(description)

        if detail_url and detail_url != source_url:
            detail_soup = self.soup(detail_url)
            if detail_soup:
                for em in self.extract_emails(detail_soup.get_text()):
                    if em not in sc.emails:
                        sc.emails.append(em)

        return sc
