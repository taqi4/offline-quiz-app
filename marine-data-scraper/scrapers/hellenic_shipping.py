"""
Scraper for Hellenic Shipping News – extracts company mentions and emails.
URL: https://www.hellenicshippingnews.com
"""
import re
import logging
from scrapers.base_scraper import BaseScraper, ScrapedCompany
from processors.categorizer import classify_company, classify_vessel_types

logger = logging.getLogger(__name__)

BASE_URL = "https://www.hellenicshippingnews.com"
NEWS_SECTIONS = [
    "/category/shipping-news/",
    "/category/maritime-news/",
    "/category/port-news/",
    "/category/shipbuilding/",
    "/category/offshore/",
    "/category/tanker-news/",
    "/category/dry-bulk-news/",
    "/category/container-news/",
]

# Patterns for entity extraction from news articles
COMPANY_SUFFIXES = re.compile(
    r"\b([A-Z][A-Za-z\s&,\.''\-]{2,60}(?:Shipping|Marine|Maritime|Ship|Tankers?|"
    r"Bulkers?|Lines?|Carriers?|Management|Services?|Group|Corp|Ltd|Limited|Inc|"
    r"S\.A\.|A\.S\.|B\.V\.|GmbH|Pte|Holdings?))\b",
    re.MULTILINE,
)


class HellenicShippingNewsScraper(BaseScraper):
    name = "hellenic_shipping"

    def scrape(self):
        for section_path in NEWS_SECTIONS:
            yield from self._scrape_section(BASE_URL + section_path)

    def _scrape_section(self, section_url: str):
        page = 1
        while page <= 10:  # recent 10 pages per section
            url = f"{section_url}page/{page}/" if page > 1 else section_url
            soup = self.soup(url)
            if soup is None:
                break

            articles = soup.select("article, div.post, div.news-item")
            if not articles:
                break

            for article in articles:
                link_el = article.select_one("a[href*='hellenicshippingnews.com'],"
                                             "h2 > a, h3 > a, .entry-title > a")
                if not link_el:
                    continue
                article_url = link_el.get("href", "")
                if not article_url:
                    continue

                companies = self._extract_from_article(article_url)
                yield from companies

            next_page = soup.select_one("a.next, a[rel='next']")
            if not next_page:
                break
            page += 1

    def _extract_from_article(self, article_url: str):
        soup = self.soup(article_url)
        if soup is None:
            return

        content_el = soup.select_one("div.entry-content, div.post-content, article")
        if not content_el:
            return

        text = content_el.get_text(separator=" ")
        emails = self.extract_emails(text)

        # Extract company names from article body
        seen = set()
        for match in COMPANY_SUFFIXES.finditer(text):
            name = match.group(1).strip().rstrip(",.")
            norm = name.lower()
            if norm in seen or len(name) < 5:
                continue
            seen.add(norm)

            sc = ScrapedCompany(
                name=name,
                description=text[:300],
                source_name="Hellenic Shipping News",
                source_url=article_url,
                emails=emails,      # associate all emails in article to first matched company
            )
            sc.company_type  = classify_company(name)
            sc.vessel_types  = classify_vessel_types(text)
            emails = []            # only attach emails to the first company
            yield sc
