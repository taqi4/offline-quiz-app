"""
Scraper for global shipyard and ship repair yard directories.
Shipyards are constant buyers of every type of ship spare part.

Sources:
  - Ship Technology shipyard directory
  - Offshore Technology shipyard directory
  - Global Repair Yards database (public pages)
  - Major known shipyards (direct website scrape, similar to ship_management_groups)
"""
import re
import logging
from scrapers.base_scraper import BaseScraper, ScrapedCompany
from processors.categorizer import classify_vessel_types

logger = logging.getLogger(__name__)

# (name, url, country, vessel_types, speciality_tags)
MAJOR_SHIPYARDS = [
    # South Korea
    ("Hyundai Heavy Industries",    "https://www.hhi.co.kr/en",          "South Korea", ["Tanker","Container Ship","Bulk Carrier","LNG","Offshore"], ["new_build","repair"]),
    ("Samsung Heavy Industries",    "https://www.shi.samsung.co.kr/eng",  "South Korea", ["Tanker","Container Ship","LNG","Offshore"],                ["new_build"]),
    ("Daewoo Shipbuilding (DSME)",  "https://www.dsme.co.kr/engn/",       "South Korea", ["Tanker","Container Ship","LNG","Naval"],                   ["new_build"]),
    ("HD Korea Shipbuilding (KSOE)","https://www.ksoe.co.kr/en",          "South Korea", ["Tanker","Container Ship","Bulk Carrier"],                  ["new_build"]),
    # China
    ("COSCO Shipping Heavy Industry","https://www.cshiship.com.cn/en",    "China",       ["Tanker","Bulk Carrier","Container Ship","Offshore"],        ["repair","conversion"]),
    ("China Merchants Ship Repair",  "https://cmsr.com.cn",               "China",       ["Tanker","Bulk Carrier","Container Ship"],                   ["repair"]),
    ("Huarun Dadong Dockyard",       "https://www.hrdockyard.com",        "China",       ["Tanker","Bulk Carrier"],                                    ["repair"]),
    # Singapore / SE Asia
    ("Sembcorp Marine",              "https://www.sembcorpmarine.com.sg", "Singapore",   ["Offshore","Tanker"],                                        ["repair","conversion","new_build"]),
    ("Keppel Shipyard",              "https://www.keppelshipyard.com",    "Singapore",   ["Offshore","Tanker","Container Ship"],                       ["repair","conversion"]),
    ("Pan-United Marine",            "https://www.pan-unitedmarine.com",  "Singapore",   ["Tanker","Bulk Carrier"],                                    ["repair"]),
    # Middle East
    ("Drydocks World Dubai",         "https://www.drydocks.gov.ae",       "UAE",         ["Tanker","Offshore","Container Ship"],                       ["repair","conversion"]),
    ("Oman Drydock Company",         "https://www.omandock.com",          "Oman",        ["Tanker","Bulk Carrier","Offshore"],                         ["repair"]),
    ("Bahrain Ship Repairing",       "https://www.bsreco.com",            "Bahrain",     ["Tanker","Bulk Carrier"],                                    ["repair"]),
    # Europe
    ("Damen Shipyards",              "https://www.damen.com",             "Netherlands", ["Offshore","Tug","Ferry","Naval"],                           ["new_build","repair"]),
    ("Fincantieri",                  "https://www.fincantieri.com",       "Italy",       ["Cruise","Naval","Offshore"],                                ["new_build"]),
    ("Meyer Werft",                  "https://www.meyerwerft.de/en",      "Germany",     ["Cruise"],                                                   ["new_build"]),
    ("Remontowa Shiprepair Yard",    "https://www.remontowa.com",         "Poland",      ["Tanker","Bulk Carrier","Ferry"],                            ["repair"]),
    ("Palumbo Shipyards",            "https://www.palumboshipyards.com",  "Italy",       ["Cruise","Tanker","Bulk Carrier"],                           ["repair","conversion"]),
    ("Chantiers de l'Atlantique",    "https://www.chantiers-atlantique.com","France",    ["Cruise","LNG"],                                             ["new_build"]),
    # Turkey
    ("Sedef Shipbuilding",           "https://www.sedefshipbuilding.com.tr","Turkey",    ["Tanker","Bulk Carrier","Container Ship"],                   ["new_build"]),
    ("Tersan Shipyard",              "https://www.tersan.com.tr",         "Turkey",      ["Tanker","Bulk Carrier","Offshore"],                         ["new_build","repair"]),
    ("Besiktas Shipyard",            "https://www.besiktasshipyard.com",  "Turkey",      ["Tanker","Bulk Carrier"],                                    ["repair","conversion"]),
    # India
    ("Cochin Shipyard",              "https://www.cochinshipyard.com",    "India",       ["Tanker","Offshore","Naval"],                                ["new_build","repair"]),
    ("Larsen & Toubro Shipbuilding", "https://www.lntecc.com/shipbuilding","India",      ["Naval","Offshore"],                                         ["new_build"]),
]

DIRECTORY_SOURCES = [
    {
        "name":     "Ship Technology Shipyards",
        "url":      "https://www.ship-technology.com/contractors/shipyards/",
        "item_sel": "article, div.company-card, div.contractor-item",
        "name_sel": "h2, h3, .company-name",
        "link_sel": "h2 a, h3 a, a.read-more",
    },
    {
        "name":     "Offshore Technology Yards",
        "url":      "https://www.offshore-technology.com/contractors/docking/",
        "item_sel": "article, div.company-card",
        "name_sel": "h2, h3",
        "link_sel": "h2 a, h3 a",
    },
]


class ShipyardDirectoryScraper(BaseScraper):
    name = "shipyard_directory"

    def scrape(self):
        # 1. Major known shipyards — direct scrape
        for name, url, country, vtypes, tags in MAJOR_SHIPYARDS:
            sc = self._scrape_yard(name, url, country, vtypes, tags)
            if sc:
                yield sc

        # 2. Directory sources
        for src in DIRECTORY_SOURCES:
            yield from self._scrape_directory(src)

    def _scrape_yard(self, name, url, country, vessel_types, tags) -> ScrapedCompany | None:
        sc = ScrapedCompany(
            name=name,
            company_type="shipyard",
            website=url,
            country=country,
            vessel_types=vessel_types,
            source_name="Shipyard Directory",
            source_url=url,
            tags=tags + ["shipyard"],
        )

        # Homepage
        soup = self.soup(url)
        if soup:
            meta = soup.find("meta", {"name": "description"})
            sc.description = (meta.get("content", "") if meta else "")[:400]
            sc.emails = self.extract_emails(soup.get_text())

        # Contact page
        from urllib.parse import urljoin
        for path in ["contact", "contact-us", "contacts"]:
            csoup = self.soup(urljoin(url + "/", path))
            if not csoup:
                continue
            for em in self.extract_emails(csoup.get_text()):
                if em not in sc.emails:
                    sc.emails.append(em)
            phone_m = re.search(
                r"(?:(?:\+|00)\d{1,3}[\s.\-]?)?(?:\(?\d{2,4}\)?[\s.\-]?){2,4}\d{2,4}",
                csoup.get_text()
            )
            if phone_m and not sc.phone:
                digits = re.sub(r"\D", "", phone_m.group(0))
                if 7 <= len(digits) <= 15:
                    sc.phone = phone_m.group(0).strip()
            break

        return sc

    def _scrape_directory(self, src: dict):
        page_url = src["url"]
        for _ in range(5):  # up to 5 pages
            soup = self.soup(page_url)
            if not soup:
                break
            items = soup.select(src["item_sel"])
            if not items:
                break
            for item in items:
                name_el = item.select_one(src["name_sel"])
                if not name_el:
                    continue
                name = name_el.get_text(strip=True)
                if not name:
                    continue
                link_el    = item.select_one(src["link_sel"])
                detail_url = ""
                if link_el and link_el.get("href"):
                    from urllib.parse import urljoin
                    detail_url = urljoin(page_url, link_el["href"])

                emails = self.extract_emails(item.get_text())
                if detail_url:
                    dsoup = self.soup(detail_url)
                    if dsoup:
                        for em in self.extract_emails(dsoup.get_text()):
                            if em not in emails:
                                emails.append(em)

                yield ScrapedCompany(
                    name=name,
                    company_type="shipyard",
                    emails=emails,
                    source_name=src["name"],
                    source_url=detail_url or page_url,
                    tags=["shipyard"],
                )

            next_el = soup.select_one("a[rel='next'], a.next")
            if not next_el or not next_el.get("href"):
                break
            from urllib.parse import urljoin
            page_url = urljoin(page_url, next_el["href"])
