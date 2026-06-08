"""
Deduplication utilities for merging duplicate company records.
Uses fuzzy name matching + country/website as tiebreakers.
"""
import logging
from fuzzywuzzy import fuzz
from sqlalchemy.orm import Session

from database.models import Company
from database.db import _normalize_name

logger = logging.getLogger(__name__)

FUZZY_THRESHOLD = 88   # 0-100; higher = stricter


def find_duplicates(session: Session, threshold: int = FUZZY_THRESHOLD) -> list[list[int]]:
    """
    Return groups of company IDs that are likely duplicates.
    WARNING: O(n²) – only run on smaller result sets or batch.
    """
    companies = session.query(Company.id, Company.name_normalized,
                               Company.country, Company.website).all()
    groups: list[list[int]] = []
    used: set[int] = set()

    for i, a in enumerate(companies):
        if a.id in used:
            continue
        group = [a.id]
        for b in companies[i + 1:]:
            if b.id in used:
                continue
            if _is_duplicate(a, b, threshold):
                group.append(b.id)
                used.add(b.id)
        if len(group) > 1:
            used.add(a.id)
            groups.append(group)

    return groups


def merge_duplicates(session: Session, group: list[int]) -> int:
    """
    Merge all companies in group into the first (canonical) one.
    Reassigns contacts/emails/vessels to canonical, deletes the rest.
    Returns canonical company ID.
    """
    canonical_id = group[0]
    canonical = session.get(Company, canonical_id)
    if not canonical:
        return canonical_id

    for dup_id in group[1:]:
        dup = session.get(Company, dup_id)
        if not dup:
            continue

        # Fill in missing fields on canonical
        for attr in ("website", "country", "city", "address", "description",
                     "fleet_size", "port"):
            if not getattr(canonical, attr) and getattr(dup, attr):
                setattr(canonical, attr, getattr(dup, attr))

        # Reassign related records
        from database.models import Contact, Email, Vessel
        session.query(Contact).filter_by(company_id=dup_id).update(
            {"company_id": canonical_id}
        )
        session.query(Email).filter_by(company_id=dup_id).update(
            {"company_id": canonical_id}
        )
        session.query(Vessel).filter_by(company_id=dup_id).update(
            {"company_id": canonical_id}
        )

        # Vessel types
        for vt in dup.vessel_types:
            if vt not in canonical.vessel_types:
                canonical.vessel_types.append(vt)

        # Tags
        for tag in dup.tags:
            if tag not in canonical.tags:
                canonical.tags.append(tag)

        session.delete(dup)
        logger.info("Merged duplicate company %d into %d", dup_id, canonical_id)

    session.commit()
    return canonical_id


def _is_duplicate(a, b, threshold: int) -> bool:
    name_score = fuzz.token_sort_ratio(a.name_normalized or "", b.name_normalized or "")
    if name_score < threshold:
        return False

    # If country known and different, probably not the same company
    if a.country and b.country and a.country.lower() != b.country.lower():
        return False

    # If websites known and match, very high confidence
    if a.website and b.website:
        a_domain = _domain(a.website)
        b_domain = _domain(b.website)
        if a_domain and b_domain:
            return a_domain == b_domain

    return name_score >= threshold


def _domain(url: str) -> str:
    from urllib.parse import urlparse
    try:
        return urlparse(url).netloc.lower().lstrip("www.")
    except Exception:
        return ""


def run_deduplication(session: Session):
    """Find and merge all duplicate company records."""
    groups = find_duplicates(session)
    logger.info("Found %d duplicate groups", len(groups))
    for group in groups:
        merge_duplicates(session, group)
    logger.info("Deduplication complete")
