"""
Open-web discovery scraper.

Uses public search engines (DuckDuckGo HTML endpoint — no API key needed) to
discover marine company websites across the entire web using targeted dorks,
then hands each discovered domain to the website enricher for deep extraction.

This is the "find ALL possible data" engine — it is not limited to a fixed
directory list; it actively searches for new marine companies by sector,
vessel type, and geography.
"""
import re
import logging
import time
from urllib.parse import quote_plus, urlparse

from scrapers.base_scraper import BaseScraper, ScrapedCompany
from processors.categorizer import classify_company, classify_vessel_types, infer_country

logger = logging.getLogger(__name__)

DDG_HTML = "https://html.duckduckgo.com/html/?q="

# Sectors x geographies x intent — generates a broad discovery matrix.
SECTORS = [
    "ship owner", "ship management company", "ship repair yard", "shipyard",
    "ship chandler", "marine spare parts supplier", "marine equipment supplier",
    "tanker operator", "bulk carrier operator", "container shipping line",
    "offshore vessel operator", "tug operator", "marine engine spare parts",
    "ship superintendent services", "vessel technical management",
    "marine diesel engine parts", "ship deck machinery supplier",
]

GEOGRAPHIES = [
    "", "Greece", "Singapore", "Germany", "Norway", "Netherlands", "UAE Dubai",
    "Cyprus", "Japan", "South Korea", "China", "Denmark", "Italy", "Turkey",
    "India", "United Kingdom", "Hong Kong", "USA",
]

# Domains to ignore (aggregators / social / generic)
SKIP_DOMAINS = {
    "duckduckgo.com", "google.com", "bing.com", "youtube.com", "facebook.com",
    "linkedin.com", "twitter.com", "x.com", "instagram.com", "wikipedia.org",
    "amazon.com", "alibaba.com", "indeed.com", "glassdoor.com", "yelp.com",
    "marinetraffic.com", "vesselfinder.com",
}


class WebDiscoveryScraper(BaseScraper):
    name = "web_discovery"

    def __init__(self, max_queries: int = 60, results_per_query: int = 15):
        super().__init__()
        self.max_queries = max_queries
        self.results_per_query = results_per_query
        self._seen_domains: set[str] = set()

    def scrape(self):
        queries = self._build_queries()[: self.max_queries]
        for sector, geo, query in queries:
            for url in self._search(query):
                sc = self._domain_to_company(url, sector, geo)
                if sc:
                    yield sc

    def _build_queries(self):
        out = []
        for sector in SECTORS:
            for geo in GEOGRAPHIES:
                q = f"{sector} {geo}".strip()
                out.append((sector, geo, q))
        return out

    def _search(self, query: str):
        """Return discovered result URLs from DuckDuckGo HTML."""
        soup = self.soup(DDG_HTML + quote_plus(query))
        if soup is None:
            return
        count = 0
        for a in soup.select("a.result__a, a.result__url, .result__title a"):
            href = a.get("href", "")
            real = self._unwrap_ddg(href)
            if not real:
                continue
            domain = self._root_domain(real)
            if not domain or domain in SKIP_DOMAINS or domain in self._seen_domains:
                continue
            self._seen_domains.add(domain)
            count += 1
            yield real
            if count >= self.results_per_query:
                break

    def _domain_to_company(self, url, sector, geo) -> ScrapedCompany | None:
        domain = self._root_domain(url)
        if not domain:
            return None
        # Derive a provisional name from the domain
        name = self._name_from_domain(domain)
        text = f"{name} {sector}"
        sc = ScrapedCompany(
            name=name,
            website=f"https://{domain}",
            country=geo if geo and len(geo) < 20 else infer_country(geo),
            description=f"Discovered via web search for '{sector}'.",
            source_name="Web Discovery",
            source_url=url,
            tags=["web_discovery", sector.replace(" ", "_")],
        )
        sc.company_type = classify_company(text)
        sc.vessel_types = classify_vessel_types(text)
        return sc

    # ---- helpers ----------------------------------------------------

    @staticmethod
    def _unwrap_ddg(href: str) -> str | None:
        if not href:
            return None
        if href.startswith("//duckduckgo.com/l/?uddg="):
            from urllib.parse import unquote, parse_qs
            qs = parse_qs(urlparse("https:" + href).query)
            return unquote(qs.get("uddg", [""])[0]) or None
        if href.startswith("http"):
            return href
        return None

    @staticmethod
    def _root_domain(url: str) -> str:
        try:
            net = urlparse(url).netloc.lower()
            return net.replace("www.", "")
        except Exception:
            return ""

    @staticmethod
    def _name_from_domain(domain: str) -> str:
        base = domain.split(".")[0]
        base = re.sub(r"[-_]", " ", base)
        return base.title()
