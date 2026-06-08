"""
Classify companies and vessels from free text using keyword matching.
Returns the most specific matching category.
"""
import re
from config import COMPANY_TYPE_KEYWORDS, VESSEL_TYPE_KEYWORDS


def classify_company(text: str) -> str:
    """Return the best-matching company type from COMPANY_TYPE_KEYWORDS."""
    if not text:
        return "other"
    text_lower = text.lower()
    scores: dict[str, int] = {}
    for cat, keywords in COMPANY_TYPE_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text_lower)
        if hits:
            scores[cat] = hits
    if not scores:
        return "other"
    return max(scores, key=scores.get)


def classify_vessel_types(text: str) -> list[str]:
    """Return all matching vessel type names from VESSEL_TYPE_KEYWORDS."""
    if not text:
        return []
    text_lower = text.lower()
    found = []
    type_map = {
        "tanker":        "Tanker",
        "bulk_carrier":  "Bulk Carrier",
        "container":     "Container Ship",
        "general_cargo": "General Cargo",
        "ro_ro":         "Ro-Ro",
        "offshore":      "Offshore",
        "cruise":        "Cruise",
        "ferry":         "Ferry",
        "tug":           "Tug",
        "dredger":       "Dredger",
        "naval":         "Naval",
        "fishing":       "Fishing",
        "yacht":         "Yacht",
    }
    for key, keywords in VESSEL_TYPE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            found.append(type_map.get(key, key))
    return found


def infer_country(text: str) -> str:
    """Attempt to infer country from text using common country name patterns."""
    countries = [
        "Greece", "Norway", "Germany", "Singapore", "Japan", "China", "Denmark",
        "Netherlands", "United Kingdom", "UK", "USA", "United States", "Cyprus",
        "Malta", "Marshall Islands", "Bahamas", "Panama", "Liberia",
        "Italy", "France", "Spain", "South Korea", "India", "Turkey",
        "UAE", "United Arab Emirates", "Sweden", "Finland", "Belgium",
        "Hong Kong", "Taiwan", "Philippines", "Indonesia", "Australia",
        "Canada", "Brazil", "Russia", "Poland", "Croatia",
    ]
    text_lower = text.lower()
    for country in countries:
        if country.lower() in text_lower:
            # Normalise aliases
            if country in ("UK",):
                return "United Kingdom"
            if country in ("USA", "United States"):
                return "USA"
            if country == "UAE":
                return "United Arab Emirates"
            return country
    return ""
