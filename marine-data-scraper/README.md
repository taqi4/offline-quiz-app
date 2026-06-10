# Marine Data Scraper — Sales Intelligence Platform

A continuously-running engine that discovers marine companies across the open
web, public directories, news sites, trade-event exhibitor lists, and industry
associations — then **enriches**, **scores**, and **packages** them as
ready-to-sell leads for a ship spare-parts business.

It does far more than scrape: it visits each company's own website to harvest
direct emails, phone numbers and decision-makers; infers corporate email
patterns to fill in missing addresses; classifies every contact by seniority
and buying department; and ranks each company 0–100 by how likely they are to
buy spares — all searchable from a web dashboard and exportable straight into
your CRM.

---

## What it collects

| Data | Examples |
|------|---------|
| Company name & type | Shipowner, Ship Management, Shipyard, Chandler, Agent, Broker … |
| Vessel types operated | Tanker, Bulk Carrier, Container, Offshore, RoRo … |
| Location | Country, city, port, region |
| Website & socials | Corporate URL, LinkedIn, Twitter/X, Facebook |
| Phones | Main line / fax harvested from the company site |
| Emails | Purchasing, Technical, Sales, General — flagged role/free/MX-valid |
| Named contacts | Name, title, **seniority**, **department**, **decision-maker flag**, direct email |
| Firmographics | Fleet size, employees, year founded |
| **Lead score** | 0–100 sales-priority score + A–F grade |
| Source & date | Provenance and freshness of every record |

---

## The Intelligence Pipeline

Every scrape is followed by an automatic four-stage enrichment pipeline:

1. **Deduplicate** — fuzzy-match and merge the same company found on multiple sources.
2. **Enrich** — visit each company's website (contact/about/team/imprint pages) to pull emails, phones, social links, and named team members.
3. **Classify & infer** — tag each contact's seniority (`c_level → staff`) and department (purchasing / technical / management …), flag decision-makers, deduce the company's email pattern (e.g. `{first}.{last}`) and synthesise likely addresses for known names with no email.
4. **Score** — rank every company 0–100 based on buyer fit (shipowners/managers/yards score highest), fleet size, reachability (deliverable departmental emails), and presence of decision-makers.

---

## Lead Scoring

Companies are graded so sales can work the hottest leads first:

| Grade | Score | Meaning |
|-------|-------|---------|
| **A** | 80–100 | Hot — ICP company, reachable decision-maker, strong data |
| **B** | 65–79 | Warm — good fit, solid contact data |
| **C** | 50–64 | Qualified — worth outreach |
| **D** | 35–49 | Cold — thin data or weaker fit |
| **F** | <35 | Low priority |

---

## Data Sources

| Source | Type | What |
|--------|------|------|
| **Web Discovery** (DuckDuckGo dorks) | Open web | Finds *new* marine companies by sector × geography — not limited to a fixed list |
| Maritime Connector | Directory | Company listings + contacts |
| ShipServ | Marketplace | Suppliers across 12 spare-parts queries |
| Hellenic Shipping News | News | Companies & emails from articles |
| Maritime Events | Trade shows | SMM, Europort, Nor-Shipping, Posidonia, METSTRADE, Marintec, Sea Japan, Seawork exhibitor lists |
| FONASBA / BIMCO / ICS / INTERTANKO / Intercargo | Associations | Member directories |
| Marine Insight / Maritime Standard / Maritime Executive / Splash247 | Directories/News | Company profiles |

---

## Quick Start

```bash
cd marine-data-scraper
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt

python main.py init-db          # create the database
python main.py run-all          # scrape + enrich + score (initial seed)
python main.py serve            # open the dashboard at http://localhost:5000
python main.py schedule         # run continuously forever
```

---

## Web Dashboard

`python main.py serve` launches a full dashboard at **http://localhost:5000**:

- Live stat tiles (companies, emails, decision-makers, hot/warm leads, avg score)
- Filter by search, company type, country, vessel type, min lead score, min fleet, has-email/phone/decision-maker
- Sort by lead score, fleet size, recency, or name
- Click any company for a full profile (all emails, contacts, socials, score breakdown)
- One-click **Excel / Contacts / CRM** export of the current filtered view

---

## REST API

| Endpoint | Description |
|----------|-------------|
| `GET /api/stats` | Database statistics |
| `GET /api/companies?...` | Search/filter (same params as dashboard) |
| `GET /api/companies/<id>` | Full company profile with contacts & emails |
| `GET /api/export?format=excel\|csv\|contacts\|crm&...` | Download filtered export |
| `GET /api/segments` / `POST /api/segments` | Saved marketing segments |

Example:
```bash
curl "http://localhost:5000/api/companies?type=shipowner&country=Greece&min_score=70&has_dm=1"
```

---

## CLI Commands

```
python main.py run-all                    # Full pipeline: scrape + postprocess
python main.py run web_discovery          # Run a single scraper
python main.py schedule                   # Continuous mode (scrape + enrich + score)
python main.py serve -p 8080              # Web dashboard + API

python main.py enrich --mx-check          # Re-crawl websites, validate email MX
python main.py intelligence               # Re-classify contacts, infer emails
python main.py rescore                    # Recompute all lead scores
python main.py postprocess                # dedup + enrich + intelligence
python main.py dedup                      # Merge duplicates only

python main.py stats                      # Database statistics
python main.py search -t shipowner -c Greece --has-email
python main.py export leads.xlsx          # Excel (4 sheets)
python main.py export crm.csv -f contacts # Flat contacts CSV
python main.py list-scrapers
```

### Search / export filters

| Flag | Meaning |
|------|---------|
| `-q` | Full-text search (FTS5) |
| `-t` | Company type |
| `-c` | Country |
| `-v` | Vessel type |
| `--has-email` | Only companies with an email |
| `--min-score` *(API/dashboard)* | Minimum lead score |
| `--has-dm` *(API/dashboard)* | Has a decision-maker contact |

---

## Exports

| Format | File | Use |
|--------|------|-----|
| **Excel** | `.xlsx` | 4 sheets: Summary, All Companies, Contacts & Emails, By Country |
| **Contacts CSV** | `.csv` | One row per contact/email |
| **CRM CSV** | `.csv` | HubSpot/Salesforce/Pipedrive/Mailchimp-ready columns (First/Last/Email/Title/Seniority/Decision-Maker/Lead Score …), UTF-8 BOM for Excel |

---

## Deployment

The scraper is **always-on** and keeps a local SQLite database, so it needs a
host that allows background processes and persistent storage. **Vercel/Netlify
will not work** (serverless, no persistence, function timeouts).

### Docker / VPS / Fly.io (recommended)
```bash
docker compose up -d          # dashboard on :5000 + worker, shared volume
```
`docker-compose.yml` runs the dashboard and the continuous scraper as two
containers sharing one named volume. SQLite is configured in **WAL mode** with
a 30 s busy-timeout so both processes can read/write safely.

### Render.com (one-click blueprint)
`render.yaml` deploys a single combined service (`serve_all.py` runs the
dashboard + scheduler thread together) on a 2 GB persistent disk. Push the repo,
"New → Blueprint", point at this folder.

### Railway
Uses the `Procfile` — add a `web` and a `worker` process, attach a volume at `/app/data`.

### Scaling to Postgres
For multiple workers or hosts, swap SQLite for Postgres: set `DB_URL` in
`config.py` to your `postgresql://…` connection string (SQLAlchemy handles the
rest; FTS search falls back to `ILIKE`).

---

## Project Structure

```
marine-data-scraper/
├── main.py                # CLI entry point (run, serve, enrich, score, export…)
├── serve_all.py           # Combined web + scheduler launcher (single-service hosts)
├── scheduler.py           # Continuous scheduler + post-process pipeline
├── config.py              # Settings, intervals, keyword taxonomies
├── Dockerfile / docker-compose.yml / render.yaml / Procfile
├── database/
│   ├── models.py          # Company, Contact, Email, Vessel, Outreach, SavedSegment…
│   └── db.py              # WAL engine, upsert, search, stats
├── scrapers/
│   ├── base_scraper.py    # HTTP, rate-limit, retry, robots, persist
│   ├── web_discovery.py   # Open-web search-engine discovery (find ALL companies)
│   ├── maritime_connector.py / shipserv.py / hellenic_shipping.py
│   ├── maritime_events.py / port_directory.py / generic_directory.py
├── processors/
│   ├── enricher.py        # Website crawl → emails, phones, socials, people
│   ├── contact_classifier.py  # Seniority / department / decision-maker
│   ├── email_pattern.py   # Infer corporate email pattern + generate addresses
│   ├── email_extractor.py # Robust extraction + deobfuscation + MX validation
│   ├── lead_scorer.py     # 0–100 sales-priority scoring
│   ├── categorizer.py     # Company & vessel-type classification
│   └── deduplicator.py    # Fuzzy-match dedup & merge
├── exporters/
│   ├── excel_exporter.py  # Multi-sheet formatted workbook
│   ├── csv_exporter.py    # Company / contact CSV
│   └── crm_exporter.py    # CRM/email-platform-ready CSV
├── webapp/
│   ├── app.py             # Flask dashboard + REST API
│   └── templates/dashboard.html
├── cli/search.py          # Search/export CLI
└── data/                  # SQLite DB + exports (gitignored)
```

---

## Ethics & Compliance

- Scrapes only **publicly accessible** pages; respects `robots.txt`; rate-limited (default 2 s/request).
- Does not bypass logins, paywalls, or `Disallow` rules.
- Data is for **B2B sales outreach** for ship spare parts. Before emailing
  contacts, review **GDPR** (EU), **PECR**, and **CAN-SPAM** (US) rules for
  your jurisdiction — include opt-outs and a legitimate-interest basis.
