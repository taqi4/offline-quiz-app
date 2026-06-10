"""
Lead scoring engine — ranks companies 0-100 for ship-spares sales priority.

Scoring is built around how valuable and reachable a company is as a buyer
of marine spare parts. Higher score = hotter lead.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Company types most likely to BUY ship spare parts (our ICP — ideal customer profile)
HIGH_VALUE_TYPES = {
    "shipowner":       30,
    "ship_management": 30,   # they procure spares for managed fleets
    "shipyard":        25,   # repair yards buy parts constantly
    "tanker":          22,
    "bulker":          22,
    "container":       22,
    "offshore":        20,
    "chandler":        18,   # resellers — could be partner or competitor
    "surveyor":        8,
    "broker":          6,
    "agent":           10,
    "classification":  4,
    "insurer":         3,
}

# Decision-making departments for spares procurement
BUYING_SIGNAL_DEPARTMENTS = {"purchasing", "technical", "management"}

# Large fleet = more spare parts demand
FLEET_TIERS = [
    (100, 20),
    (50, 16),
    (20, 12),
    (10, 8),
    (5, 5),
    (1, 2),
]


def score_company(company) -> float:
    """Compute a 0-100 lead score for a Company ORM object."""
    score = 0.0

    # 1. Company type fit (max 30)
    score += HIGH_VALUE_TYPES.get((company.company_type or "").lower(), 5)

    # 2. Fleet size (max 20)
    if company.fleet_size:
        for threshold, pts in FLEET_TIERS:
            if company.fleet_size >= threshold:
                score += pts
                break

    # 3. Reachability — emails (max 20)
    emails = list(company.emails)
    if emails:
        score += 8
        # Bonus for non-free, deliverable, departmental emails
        if any(not e.is_free for e in emails):
            score += 4
        if any(e.mx_valid for e in emails):
            score += 4
        if any((e.email_type or "") in ("purchasing", "technical") for e in emails):
            score += 4

    # 4. Decision-maker contacts (max 18)
    contacts = list(company.contacts)
    if contacts:
        score += 4
        if any(c.is_decision_maker for c in contacts):
            score += 8
        if any((c.department or "") in BUYING_SIGNAL_DEPARTMENTS for c in contacts):
            score += 6

    # 5. Data completeness / professionalism (max 12)
    if company.website:
        score += 4
    if company.phone:
        score += 3
    if company.address:
        score += 2
    if company.linkedin:
        score += 3

    return round(min(score, 100.0), 1)


def score_grade(score: float) -> str:
    """Map a numeric score to an A-F grade for quick triage."""
    if score >= 80:
        return "A"   # hot
    if score >= 65:
        return "B"   # warm
    if score >= 50:
        return "C"   # qualified
    if score >= 35:
        return "D"   # cold
    return "F"        # low priority


def rescore_all(session) -> int:
    """Recompute lead scores for every company. Returns count updated."""
    from database.models import Company
    companies = session.query(Company).all()
    for c in companies:
        c.lead_score = score_company(c)
    session.commit()
    logger.info("Rescored %d companies", len(companies))
    return len(companies)
