"""
Targeted scrapers for the world's largest ship management company websites.
These companies manage thousands of vessels and are prime buyers of ship spares.

Top groups covered:
  V.Group, Bernhard Schulte, Columbia Shipmanagement, Anglo-Eastern,
  Wallem Group, Thome Group, OSM Maritime, Fleet Management,
  Seaspan, Stena, Euronav, Frontline, BW Group, Pacific Basin,
  Scorpio Group, Tsakos Group, Star Bulk
"""
import re
import logging
from scrapers.base_scraper import BaseScraper, ScrapedCompany
from processors.categorizer import classify_vessel_types
from processors.contact_classifier import enrich_contact

logger = logging.getLogger(__name__)

# (name, url, vessel_types, fleet_size_approx, hq_country)
MAJOR_MANAGERS = [
    ("V.Group",                "https://www.vgroup.com",                ["Tanker","Bulk Carrier","Container Ship","Offshore"], 1000, "United Kingdom"),
    ("Bernhard Schulte Shipmanagement", "https://www.bs-shipmanagement.com", ["Tanker","Bulk Carrier","Container Ship","LNG"], 650, "Germany"),
    ("Columbia Shipmanagement","https://www.columbia-shipmanagement.com",["Tanker","Bulk Carrier","Container Ship"],           600, "Cyprus"),
    ("Anglo-Eastern Group",    "https://www.angloeastern.com",          ["Tanker","Bulk Carrier","Container Ship"],           700, "Hong Kong"),
    ("Wallem Group",           "https://www.wallem.com",                ["Tanker","Bulk Carrier","Container Ship"],           400, "Hong Kong"),
    ("Thome Group",            "https://www.thomegroup.com",            ["Tanker","Bulk Carrier","Container Ship","Offshore"],350, "Singapore"),
    ("OSM Maritime Group",     "https://osm.no",                        ["Tanker","Bulk Carrier","Offshore"],                 400, "Norway"),
    ("Fleet Management Ltd",   "https://www.fleetship.com",             ["Tanker","Bulk Carrier","Container Ship"],           500, "Hong Kong"),
    ("Stena Teknik",           "https://www.stena.com",                 ["Tanker","Ro-Ro","Ferry"],                           150, "Sweden"),
    ("BW Group",               "https://www.bw-group.com",              ["Tanker","LNG","Offshore"],                         200, "Singapore"),
    ("Scorpio Ship Management","https://www.scorpioshipmanagement.com",  ["Tanker","Bulk Carrier"],                           200, "Monaco"),
    ("Tsakos Group",           "https://www.tenn.gr",                   ["Tanker","LNG"],                                    100, "Greece"),
    ("Star Bulk Carriers",     "https://www.starbulk.com",              ["Bulk Carrier"],                                    120, "Greece"),
    ("Euronav",                "https://www.euronav.com",               ["Tanker"],                                          70, "Belgium"),
    ("Frontline",              "https://www.frontline.bm",              ["Tanker"],                                          80, "Bermuda"),
    ("Pacific Basin Shipping", "https://www.pacificbasin.com",          ["Bulk Carrier"],                                    200, "Hong Kong"),
    ("Seaspan Corporation",    "https://www.seaspancorp.com",           ["Container Ship"],                                  130, "Canada"),
    ("MISC Berhad",            "https://www.misc.com.my",               ["Tanker","LNG","Offshore"],                         80, "Malaysia"),
    ("Teekay Corporation",     "https://www.teekay.com",               ["Tanker","LNG","Offshore"],                         150, "Bermuda"),
    ("Hafnia",                 "https://www.hafnia.com",                ["Tanker"],                                          200, "Denmark"),
    ("Odfjell SE",             "https://www.odfjell.com",               ["Tanker"],                                          90, "Norway"),
    ("Klaveness",              "https://klaveness.com",                 ["Bulk Carrier","Tanker"],                           50, "Norway"),
    ("Grieg Maritime",         "https://griegmaritimegroup.com",        ["Bulk Carrier","Offshore"],                         60, "Norway"),
    ("Dorian LPG",             "https://www.dorianlpg.com",             ["Tanker"],                                          25, "USA"),
    ("Ultranav",               "https://www.ultranav.com",              ["Tanker","Bulk Carrier"],                           80, "Chile"),
    ("Zodiac Maritime",        "https://www.zodiacmaritime.com",        ["Tanker","Bulk Carrier","Container Ship"],          200, "United Kingdom"),
    ("Dynacom Tankers",        "https://www.dynacomtm.com",             ["Tanker"],                                          60, "Greece"),
    ("Maran Tankers",          "https://www.marantankers.com",          ["Tanker"],                                          50, "Greece"),
    ("Thenamaris",             "https://www.thenamaris.com",            ["Tanker","Bulk Carrier"],                           60, "Greece"),
    ("Diana Shipping",         "https://www.dianashipping.gr",          ["Bulk Carrier"],                                    40, "Greece"),
]

# Pages most likely to have procurement/technical contacts
CONTACT_PAGES = ["contact", "contact-us", "about", "management", "team", "our-team",
                 "procurement", "technical", "fleet", "departments"]


class ShipManagementGroupsScraper(BaseScraper):
    name = "ship_management_groups"

    def scrape(self):
        for name, url, vessel_types, fleet_size, country in MAJOR_MANAGERS:
            sc = self._scrape_company(name, url, vessel_types, fleet_size, country)
            if sc:
                yield sc

    def _scrape_company(self, name: str, base_url: str,
                         vessel_types: list, fleet_size: int,
                         country: str) -> ScrapedCompany | None:
        sc = ScrapedCompany(
            name=name,
            company_type="ship_management",
            website=base_url,
            country=country,
            fleet_size=fleet_size,
            vessel_types=vessel_types,
            source_name="Ship Management Groups",
            source_url=base_url,
            tags=["major_manager", "direct_target"],
        )

        # Try homepage first
        soup = self.soup(base_url)
        if soup:
            sc.description = (soup.find("meta", {"name": "description"}) or {}).get("content", "")[:400]
            sc.emails = self.extract_emails(soup.get_text())
            sc = self._grab_socials(sc, str(soup))

        # Contact/team sub-pages
        for path in CONTACT_PAGES:
            from urllib.parse import urljoin
            sub_url = urljoin(base_url + "/", path)
            sub = self.soup(sub_url)
            if not sub:
                continue
            text = sub.get_text()
            for em in self.extract_emails(text):
                if em not in sc.emails:
                    sc.emails.append(em)
            # Phone
            if not sc.phone:
                sc.phone = self._extract_phone(text)
            # People blocks
            for block in sub.select(".team-member,.person,.management,.contact-person,"
                                    "[class*='team'],[class*='person'],[class*='contact']"):
                name_el  = block.select_one("h2,h3,h4,.name,strong")
                title_el = block.select_one(".title,.position,.role,em")
                email_el = block.select_one("a[href^='mailto:']")
                cname  = name_el.get_text(strip=True)  if name_el  else ""
                ctitle = title_el.get_text(strip=True) if title_el else ""
                cemail = email_el["href"].replace("mailto:", "").strip() if email_el else ""
                if cname and len(cname.split()) <= 5:
                    sc.contacts.append({"name": cname, "title": ctitle,
                                        "email": cemail, "source_url": sub_url})

        return sc

    def _extract_phone(self, text: str) -> str:
        m = re.search(r"(?:(?:\+|00)\d{1,3}[\s.\-]?)?(?:\(?\d{2,4}\)?[\s.\-]?){2,4}\d{2,4}", text)
        if m:
            digits = re.sub(r"\D", "", m.group(0))
            if 7 <= len(digits) <= 15:
                return m.group(0).strip()
        return ""

    def _grab_socials(self, sc: ScrapedCompany, html: str) -> ScrapedCompany:
        import re as _re
        patterns = {
            "linkedin": _re.compile(r"https?://(?:[a-z]{2,3}\.)?linkedin\.com/company/[^\s\"'<>]+", _re.I),
            "twitter":  _re.compile(r"https?://(?:www\.)?(?:twitter|x)\.com/[^\s\"'<>]+", _re.I),
        }
        for key, pat in patterns.items():
            m = pat.search(html)
            if m:
                setattr(sc, key if hasattr(sc, key) else "_", m.group(0).rstrip('/"\''))
        return sc
