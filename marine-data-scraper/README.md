# Marine Data Scraper

Continuously scrapes public marine industry directories, news sites, and trade-event exhibitor lists to build a searchable database of companies, contacts, and emails — purpose-built for selling ship spare parts.

---

## What it collects

| Data | Examples |
|------|---------|
| Company name & type | Shipowner, Ship Management, Shipyard, Chandler, Agent, Broker … |
| Vessel types operated | Tanker, Bulk Carrier, Container, Offshore, RoRo … |
| Country / city / port | Greece, Singapore, Norway … |
| Website | Corporate URL |
| Emails | Purchasing, Technical, General, Management |
| Named contacts | Name, Title, Direct email |
| Fleet size | Number of vessels |
| Source & date | Where and when scraped |

---

## Data Sources

| Source | Type | Update interval |
|--------|------|----------------|
| Maritime Connector | Directory | 24 h |
| ShipServ | Marketplace | 24 h |
| Hellenic Shipping News | News | 12 h |
| Maritime Events (SMM, Europort, Nor-Shipping, Posidonia, METSTRADE, Marintec…) | Trade shows | Weekly |
| FONASBA / BIMCO / ICS / INTERTANKO / Intercargo | Associations | 48 h |
| Marine Insight, Maritime Standard, Maritime Executive | Directories/News | 12 h |
| Generic directory scraper | Configurable | 24 h |

---

## Quick Start

```bash
cd marine-data-scraper

# 1. Create virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) copy and edit .env
cp .env.example .env

# 4. Initialise database
python main.py init-db

# 5. Run all scrapers once (initial seed)
python main.py run-all

# 6. Start continuous scheduler (runs forever)
python main.py schedule
```

---

## Commands

```
python main.py run-all                          # Run every scraper once
python main.py run maritime_connector           # Run a single scraper
python main.py schedule                         # Continuous mode
python main.py schedule --no-initial-run        # Skip first immediate run

python main.py stats                            # Database stats
python main.py search -q "tanker" -c Greece     # Search companies
python main.py search -t shipowner --has-email  # Filter to companies with emails

python main.py export marine_leads.xlsx         # Export full Excel workbook
python main.py export contacts.csv -f contacts  # Flat contacts+email CSV
python main.py export companies.csv -f csv      # Company CSV

python main.py dedup                            # Merge duplicate records
python main.py list-scrapers                    # List scrapers and intervals
```

---

## Search & Export Filters

All `search` and `export` commands accept:

| Flag | Description |
|------|-------------|
| `-q TEXT` | Full-text search (FTS5) across name, description, country, city |
| `-t TYPE` | Company type: `shipowner`, `ship_management`, `shipyard`, `chandler`, `agent`, `broker`, `equipment`, `spare_parts`, `offshore`, `tanker`, `bulker`, `container` … |
| `-c COUNTRY` | Country name (partial match) |
| `-v VESSEL` | Vessel type: `Tanker`, `Bulk Carrier`, `Container Ship`, `Offshore` … |
| `--has-email` | Only include companies with at least one email |

---

## Excel Export Structure

The generated `.xlsx` file contains four sheets:

1. **Summary** – totals, breakdown by type and top countries
2. **All Companies** – one row per company
3. **Contacts & Emails** – one row per email/contact (sales-ready mail-merge format)
4. **By Country** – pivot count by country

---

## Project Structure

```
marine-data-scraper/
├── main.py                   # CLI entry point
├── scheduler.py              # Continuous scheduler
├── config.py                 # All settings & keyword lists
├── requirements.txt
├── .env.example
├── database/
│   ├── models.py             # SQLAlchemy ORM (Company, Contact, Email, Vessel …)
│   └── db.py                 # Session helpers, upsert, search, stats
├── scrapers/
│   ├── base_scraper.py       # HTTP, rate-limiting, retry, persist
│   ├── maritime_connector.py # Maritime Connector directory
│   ├── hellenic_shipping.py  # Hellenic Shipping News
│   ├── shipserv.py           # ShipServ marketplace
│   ├── maritime_events.py    # Trade show exhibitor lists
│   ├── port_directory.py     # Association member directories
│   └── generic_directory.py # Configurable generic scraper
├── processors/
│   ├── categorizer.py        # Keyword-based company/vessel classification
│   ├── email_extractor.py    # Advanced email extraction + validation
│   └── deduplicator.py       # Fuzzy-match deduplication
├── exporters/
│   ├── csv_exporter.py       # CSV export (companies + contacts)
│   └── excel_exporter.py     # Multi-sheet formatted Excel export
├── cli/
│   └── search.py             # Search/export CLI commands
└── data/
    └── marine_companies.db   # SQLite database (auto-created)
```

---

## Adding a New Scraper

1. Create `scrapers/my_scraper.py`, subclass `BaseScraper`, implement `scrape()` yielding `ScrapedCompany` objects.
2. Register it in `scheduler.py` → `SCRAPER_REGISTRY`.
3. Add an interval in `config.py` → `SCRAPER_INTERVALS`.
4. Run: `python main.py run my_scraper`.

---

## Ethics & Compliance

- Only scrapes **publicly accessible** pages.
- Respects `robots.txt` (basic check).
- Rate-limited to `REQUEST_DELAY` seconds between requests (default 2 s).
- Does **not** bypass authentication, scrape private data, or ignore explicit `Disallow` rules.
- Data is for **B2B sales outreach** (ship spare parts) — review GDPR/CAN-SPAM requirements for your jurisdiction before emailing contacts.
