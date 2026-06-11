"""
Scraper for marine industry associations — their member directories are
among the most reliable sources of verified shipowner/operator company data.

Sources:
  INTERTANKO, INTERCARGO, Cruise Lines International Association (CLIA),
  International Chamber of Shipping (ICS), BIMCO, International Association
  of Dry Cargo Shipowners (Intercargo), OCIMF, Baltic Exchange members,
  Greek Shipping Cooperation Committee, Hong Kong Shipowners Association,
  Singapore Shipping Association, Norwegian Shipowners' Association,
  German Shipowners' Association (VDR), Japan Shipowners' Association
"""
import logging
from urllib.parse import urljoin
from scrapers.base_scraper import BaseScraper, ScrapedCompany
from processors.categorizer import classify_company, classify_vessel_types

logger = logging.getLogger(__name__)

ASSOCIATIONS = [
    # Tanker owners
    {
        "name":    "INTERTANKO Members",
        "url":     "https://www.intertanko.com/about/members",
        "type":    "tanker",
        "country": "",
        "tags":    ["intertanko", "tanker_owner"],
    },
    # Bulk carrier owners
    {
        "name":    "INTERCARGO Members",
        "url":     "https://www.intercargo.org/members/",
        "type":    "bulk_carrier",
        "country": "",
        "tags":    ["intercargo", "bulk_owner"],
    },
    # Container / general shipping
    {
        "name":    "World Shipping Council Members",
        "url":     "https://www.worldshipping.org/about/wsc-members",
        "type":    "container",
        "country": "",
        "tags":    ["wsc", "container_line"],
    },
    # Cruise
    {
        "name":    "CLIA Members",
        "url":     "https://cruising.org/en-us/about-clia/members/cruise-line-members",
        "type":    "cruise",
        "country": "",
        "tags":    ["clia", "cruise_operator"],
    },
    # Chemical / product tankers
    {
        "name":    "OCIMF Members",
        "url":     "https://www.ocimf.org/members",
        "type":    "tanker",
        "country": "",
        "tags":    ["ocimf", "oil_company"],
    },
    # General shipping
    {
        "name":    "ICS Member Organisations",
        "url":     "https://www.ics-shipping.org/about-us/member-organisations/",
        "type":    "shipping",
        "country": "",
        "tags":    ["ics_member"],
    },
    # Regional — Greek owners (world's largest fleet)
    {
        "name":    "Union of Greek Shipowners",
        "url":     "https://www.ugs.gr/en/members/",
        "type":    "shipowner",
        "country": "Greece",
        "tags":    ["greek_owner", "ugs"],
    },
    # Regional — Norwegian
    {
        "name":    "Norwegian Shipowners Association",
        "url":     "https://www.rederi.no/en/members/",
        "type":    "shipowner",
        "country": "Norway",
        "tags":    ["norwegian_owner"],
    },
    # Regional — Singapore
    {
        "name":    "Singapore Shipping Association",
        "url":     "https://www.ssa.org.sg/membership/ssa-members/",
        "type":    "shipping",
        "country": "Singapore",
        "tags":    ["singapore_shipping"],
    },
    # Regional — Hong Kong
    {
        "name":    "Hong Kong Shipowners Association",
        "url":     "https://www.hksoa.org/member-list/",
        "type":    "shipowner",
        "country": "Hong Kong",
        "tags":    ["hkoa_member"],
    },
    # Regional — Japan
    {
        "name":    "Japan Shipowners Association",
        "url":     "https://www.jsanet.or.jp/e/index.html",
        "type":    "shipowner",
        "country": "Japan",
        "tags":    ["japanese_owner"],
    },
    # Regional — Germany
    {
        "name":    "German Shipowners Association (VDR)",
        "url":     "https://www.reederverband.de/en/members/",
        "type":    "shipowner",
        "country": "Germany",
        "tags":    ["vdr_member", "german_owner"],
    },
    # Offshore
    {
        "name":    "IMCA Members",
        "url":     "https://www.imca-int.com/member-directory/",
        "type":    "offshore",
        "country": "",
        "tags":    ["imca_member", "offshore"],
    },
    # Shipbuilding / repair
    {
        "name":    "CESA Shipbuilders",
        "url":     "https://www.cesa.eu/members/",
        "type":    "shipyard",
        "country": "",
        "tags":    ["cesa_member", "european_shipyard"],
    },
]

# Generic CSS selectors for member list items across different association sites
ITEM_SELECTORS = [
    "li.member", "div.member", "tr.member",
    "div[class*='member-item']", "li[class*='member']",
    "div.company-item", "li.company", "div.listing",
    "ul.members li", "table.members tr", ".member-list li",
    "div.team-item", "article.member",
]

NAME_SELECTORS  = ["strong", "b", "h3", "h4", ".name", "td:first-child", "a"]
COUNTRY_SELECTORS = [".country", ".location", ".hq", "td:nth-child(2)"]


class IndustryAssociationsScraper(BaseScraper):
    name = "industry_associations"

    def scrape(self):
        for assoc in ASSOCIATIONS:
            yield from self._scrape_association(assoc)

    def _scrape_association(self, assoc: dict):
        soup = self.soup(assoc["url"])
        if soup is None:
            return

        items = []
        for sel in ITEM_SELECTORS:
            items = soup.select(sel)
            if items:
                break

        if not items:
            # Fall back: any <li> or <tr> with >= 3 chars of text
            items = [el for el in soup.select("li, tr")
                     if len(el.get_text(strip=True)) > 3]

        seen = set()
        for item in items:
            name = self._extract_text(item, NAME_SELECTORS)
            if not name or len(name) < 3 or name.lower() in seen:
                continue
            # Filter out nav items and non-company text
            if len(name.split()) > 8 or name.lower() in (
                "home", "about", "contact", "members", "join", "news", "events"
            ):
                continue
            seen.add(name.lower())

            country = self._extract_text(item, COUNTRY_SELECTORS) or assoc["country"]
            emails  = self.extract_emails(item.get_text())

            website = ""
            for a in item.select("a[href^='http']"):
                href = a["href"]
                if assoc["url"].split("/")[2] not in href:
                    website = href
                    break

            sc = ScrapedCompany(
                name=name,
                company_type=classify_company(name) or assoc["type"],
                country=country,
                website=website,
                emails=emails,
                source_name=assoc["name"],
                source_url=assoc["url"],
                tags=assoc.get("tags", []),
            )
            sc.vessel_types = classify_vessel_types(assoc["type"] + " " + name)
            yield sc

    def _extract_text(self, item, selectors: list) -> str:
        for sel in selectors:
            el = item.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text and len(text) > 1:
                    return text
        return ""
