"""
Marine Data Scraper — Web Dashboard + REST API.

A single-file Flask app that exposes:
  - A searchable, filterable dashboard UI (templates/dashboard.html)
  - A JSON REST API for programmatic access / integrations
  - CSV / Excel / CRM export endpoints
  - Live database statistics

Run:  python -m webapp.app      (or: python main.py serve)
"""
import io
import sys
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import (
    Flask, request, jsonify, render_template, send_file, Response
)

from database.db import init_db, get_session, search_companies, get_stats
from database.models import Company, Contact, Email, VesselType
from processors.lead_scorer import score_grade
from exporters.csv_exporter import export_companies_csv, export_contacts_csv
from exporters.excel_exporter import export_excel

logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder="templates")


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def company_to_dict(c: Company, full: bool = False) -> dict:
    d = {
        "id":           c.id,
        "name":         c.name,
        "company_type": c.company_type,
        "country":      c.country,
        "city":         c.city,
        "region":       c.region,
        "website":      c.website,
        "phone":        c.phone,
        "linkedin":     c.linkedin,
        "fleet_size":   c.fleet_size,
        "lead_score":   c.lead_score,
        "grade":        score_grade(c.lead_score or 0),
        "vessel_types": [vt.name for vt in c.vessel_types],
        "email_count":  len(c.emails),
        "contact_count":len(c.contacts),
        "source_name":  c.source_name,
    }
    if full:
        d.update({
            "description": c.description,
            "address":     c.address,
            "port":        c.port,
            "twitter":     c.twitter,
            "facebook":    c.facebook,
            "employees":   c.employees,
            "year_founded":c.year_founded,
            "email_pattern": c.email_pattern,
            "source_url":  c.source_url,
            "date_scraped":c.date_scraped.isoformat() if c.date_scraped else None,
            "emails": [
                {"address": e.address, "type": e.email_type,
                 "is_role": e.is_role, "is_free": e.is_free,
                 "mx_valid": e.mx_valid, "confidence": e.confidence}
                for e in c.emails
            ],
            "contacts": [
                {"name": co.name, "title": co.title, "email": co.email,
                 "department": co.department, "seniority": co.seniority,
                 "is_decision_maker": co.is_decision_maker,
                 "email_status": co.email_status, "linkedin": co.linkedin}
                for co in c.contacts
            ],
        })
    return d


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    with get_session() as session:
        stats = get_stats(session)
        vessel_types = [vt.name for vt in session.query(VesselType).all()]
        types = sorted([t for t in stats["companies_by_type"].keys() if t])
        countries = sorted([c for c in stats["companies_by_country"].keys() if c])
    return render_template("dashboard.html", stats=stats,
                           vessel_types=vessel_types,
                           company_types=types, countries=countries)


# ---------------------------------------------------------------------------
# REST API
# ---------------------------------------------------------------------------

@app.route("/api/stats")
def api_stats():
    with get_session() as session:
        return jsonify(get_stats(session))


@app.route("/api/companies")
def api_companies():
    args = request.args
    with get_session() as session:
        results = search_companies(
            session,
            query=args.get("q", ""),
            company_type=args.get("type", ""),
            country=args.get("country", ""),
            region=args.get("region", ""),
            vessel_type=args.get("vessel", ""),
            has_email=args.get("has_email") == "1",
            has_phone=args.get("has_phone") == "1",
            has_decision_maker=args.get("has_dm") == "1",
            min_score=float(args.get("min_score", 0) or 0),
            min_fleet=int(args.get("min_fleet", 0) or 0),
            sort=args.get("sort", "score"),
            limit=int(args.get("limit", 50) or 50),
            offset=int(args.get("offset", 0) or 0),
        )
        return jsonify({
            "count": len(results),
            "results": [company_to_dict(c) for c in results],
        })


@app.route("/api/companies/<int:company_id>")
def api_company(company_id):
    with get_session() as session:
        c = session.get(Company, company_id)
        if not c:
            return jsonify({"error": "not found"}), 404
        return jsonify(company_to_dict(c, full=True))


@app.route("/api/export")
def api_export():
    """Export filtered results. ?format=excel|csv|contacts|crm"""
    args = request.args
    fmt = args.get("format", "excel")
    with get_session() as session:
        companies = search_companies(
            session,
            query=args.get("q", ""),
            company_type=args.get("type", ""),
            country=args.get("country", ""),
            region=args.get("region", ""),
            vessel_type=args.get("vessel", ""),
            has_email=args.get("has_email") == "1",
            has_phone=args.get("has_phone") == "1",
            has_decision_maker=args.get("has_dm") == "1",
            min_score=float(args.get("min_score", 0) or 0),
            min_fleet=int(args.get("min_fleet", 0) or 0),
            sort=args.get("sort", "score"),
            limit=100_000,
        )
        if not companies:
            return jsonify({"error": "no data"}), 404

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        tmp_dir = Path(__file__).parent.parent / "data" / "exports"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        if fmt == "excel":
            path = tmp_dir / f"marine_leads_{ts}.xlsx"
            export_excel(session, path, companies)
        elif fmt == "contacts":
            path = tmp_dir / f"marine_contacts_{ts}.csv"
            export_contacts_csv(session, path, companies)
        elif fmt == "crm":
            from exporters.crm_exporter import export_crm_csv
            path = tmp_dir / f"marine_crm_{ts}.csv"
            export_crm_csv(session, path, companies)
        else:
            path = tmp_dir / f"marine_companies_{ts}.csv"
            export_companies_csv(session, path, companies)

    return send_file(str(path), as_attachment=True, download_name=path.name)


@app.route("/api/segments", methods=["GET", "POST"])
def api_segments():
    import json
    from database.models import SavedSegment
    with get_session() as session:
        if request.method == "POST":
            data = request.get_json(force=True)
            seg = SavedSegment(
                name=data["name"],
                description=data.get("description", ""),
                filters_json=json.dumps(data.get("filters", {})),
            )
            session.add(seg)
            session.flush()
            return jsonify({"id": seg.id, "name": seg.name})
        segs = session.query(SavedSegment).all()
        return jsonify([
            {"id": s.id, "name": s.name, "description": s.description,
             "filters": json.loads(s.filters_json or "{}"),
             "match_count": s.match_count}
            for s in segs
        ])


def main(host="0.0.0.0", port=5000, debug=False):
    logging.basicConfig(level=logging.INFO)
    init_db()
    logger.info("Dashboard running at http://%s:%d", host, port)
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main(debug=True)
