"""Central configuration for the marine data scraper."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Database
DB_PATH = DATA_DIR / "marine_companies.db"
DB_URL = f"sqlite:///{DB_PATH}"

# HTTP settings
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "2.0"))   # seconds between requests
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
MAX_CONCURRENT = int(os.getenv("MAX_CONCURRENT", "3"))

# Rotation headers
DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Scheduler: how often to re-run each scraper (hours)
SCRAPER_INTERVALS = {
    # Core directories
    "maritime_connector":      24,
    "hellenic_shipping":       12,
    "shipserv":                24,
    "maritime_events":         168,    # weekly — exhibitor lists don't change daily
    "port_directory":          48,
    "generic_directory":       24,
    # Open-web
    "web_discovery":           72,     # broad sweep every 3 days
    # High-value direct targets — run less often, data is stable
    "ship_management_groups":  168,    # weekly
    "shipyard_directory":      168,    # weekly
    "industry_associations":   168,    # weekly
    "classification_societies":168,    # weekly
    # Enrichment — run daily, works through backlog incrementally
    "linkedin_public":         48,
}

# Company type keywords for categorisation
COMPANY_TYPE_KEYWORDS = {
    "shipowner":         ["shipowner", "ship owner", "vessel owner", "fleet owner", "tanker owner"],
    "ship_management":   ["ship management", "ship manager", "vessel management", "fleet management", "crewing"],
    "shipyard":          ["shipyard", "ship repair", "drydock", "dry dock", "shipbuilding", "naval yard"],
    "chandler":          ["ship chandler", "chandlery", "marine supply", "ship supply", "provisions"],
    "broker":            ["shipbroker", "ship broker", "chartering", "freight broker", "cargo broker"],
    "agent":             ["shipping agent", "ship agent", "port agent", "freight forwarder", "logistics"],
    "equipment":         ["marine equipment", "ship equipment", "maritime equipment", "deck equipment"],
    "spare_parts":       ["spare parts", "spares", "engine parts", "propulsion", "pumps", "valves", "filters"],
    "classification":    ["classification society", "class society", "survey", "dnv", "bureau veritas", "lr", "bv"],
    "port_authority":    ["port authority", "port terminal", "harbour", "harbor", "port operator"],
    "insurer":           ["marine insurance", "p&i club", "hull insurance", "cargo insurance"],
    "surveyor":          ["marine surveyor", "condition survey", "damage survey", "inspection"],
    "offshore":          ["offshore", "rig", "platform", "fpso", "drillship", "jack-up"],
    "cruise":            ["cruise", "passenger ship", "ferry", "ro-ro"],
    "tanker":            ["tanker", "vlcc", "suezmax", "aframax", "chemical tanker", "lng", "lpg"],
    "bulker":            ["bulk carrier", "bulker", "capesize", "panamax", "handymax", "handysize"],
    "container":         ["container ship", "containership", "feeder", "ultra large container"],
    "naval":             ["naval", "coast guard", "navy", "military vessel", "patrol vessel"],
}

# Vessel type keywords
VESSEL_TYPE_KEYWORDS = {
    "tanker":      ["tanker", "vlcc", "suezmax", "aframax", "chemical tanker", "lng carrier", "lpg carrier"],
    "bulk_carrier":["bulk carrier", "bulker", "capesize", "panamax", "handymax"],
    "container":   ["container ship", "containership", "feeder vessel", "ulcv"],
    "general_cargo":["general cargo", "multipurpose", "cargo vessel"],
    "ro_ro":       ["ro-ro", "roro", "car carrier", "pctc"],
    "offshore":    ["offshore", "ahts", "psv", "osv", "fpso", "drillship", "jack-up", "semisubmersible"],
    "cruise":      ["cruise ship", "cruise liner", "passenger ferry"],
    "ferry":       ["ferry", "ro-pax", "passenger"],
    "tug":         ["tug", "tugboat", "salvage tug"],
    "dredger":     ["dredger", "dredging"],
    "naval":       ["naval", "warship", "frigate", "destroyer", "patrol"],
    "fishing":     ["fishing vessel", "trawler", "fish carrier"],
    "yacht":       ["yacht", "superyacht", "mega yacht", "sailing yacht"],
}

# Sources to scrape (public directories and news sites)
SCRAPE_SOURCES = [
    {
        "name":        "Maritime Connector",
        "url":         "https://maritime-connector.com",
        "type":        "directory",
        "scraper":     "maritime_connector",
        "priority":    1,
    },
    {
        "name":        "Hellenic Shipping News",
        "url":         "https://www.hellenicshippingnews.com",
        "type":        "news",
        "scraper":     "hellenic_shipping",
        "priority":    2,
    },
    {
        "name":        "Ship Management International",
        "url":         "https://www.shipmanagementinternational.com",
        "type":        "directory",
        "scraper":     "ship_management_dir",
        "priority":    1,
    },
    {
        "name":        "TradeWinds",
        "url":         "https://www.tradewindsnews.com",
        "type":        "news",
        "scraper":     "tradewindsnews",
        "priority":    3,
    },
    {
        "name":        "Marine Insight",
        "url":         "https://www.marineinsight.com",
        "type":        "news",
        "scraper":     "marine_insight",
        "priority":    3,
    },
    {
        "name":        "ShipServ",
        "url":         "https://www.shipserv.com",
        "type":        "marketplace",
        "scraper":     "shipserv",
        "priority":    1,
    },
    {
        "name":        "Informa Marine Events",
        "url":         "https://www.informamarkets.com/en/sectors/maritime.html",
        "type":        "events",
        "scraper":     "maritime_events",
        "priority":    2,
    },
    {
        "name":        "World Shipping Council",
        "url":         "https://www.worldshipping.org",
        "type":        "directory",
        "scraper":     "generic_directory",
        "priority":    2,
    },
]
