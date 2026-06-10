"""
Classify contacts by department, seniority, and decision-maker status from
their job title — so sales can target the right person for spare-parts buying.
"""
import re

# Seniority detection (ordered: highest first).
# Short acronyms are matched with word boundaries to avoid substring traps
# (e.g. "cto" inside "direCTOr"). "chief engineer" is a shipboard manager
# role, not C-suite, so it is handled before the generic "chief" rule.
SENIORITY_RULES = [
    ("manager", [r"chief engineer", r"chief officer", r"chief mate"]),
    ("c_level", [r"\bceo\b", r"\bcfo\b", r"\bcoo\b", r"\bcto\b", r"chief",
                 r"managing director", r"founder", r"owner", r"president",
                 r"\bpartner\b", r"proprietor", r"\bmd\b"]),
    ("vp",      [r"vice president", r"\bvp\b", r"\bsvp\b", r"\bevp\b",
                 r"deputy director"]),
    ("director",[r"director", r"head of", r"general manager", r"\bgm\b"]),
    ("manager", [r"manager", r"\blead\b", r"supervisor", r"superintendent"]),
    ("staff",   [r"officer", r"executive", r"coordinator", r"assistant",
                 r"engineer", r"specialist", r"\bagent\b", r"clerk", r"buyer"]),
]

# Department detection by keyword
DEPARTMENT_RULES = {
    "purchasing": ["purchas", "procurement", "supply chain", "buyer", "sourcing",
                   "materials", "spare"],
    "technical":  ["technical", "fleet", "engineer", "superintendent", "maintenance",
                   "marine operations", "dpa", "machinery", "newbuild", "drydock"],
    "management": ["ceo", "coo", "cfo", "managing", "director", "president", "owner",
                   "founder", "general manager", "head"],
    "commercial": ["commercial", "chartering", "sales", "business development",
                   "marketing"],
    "operations": ["operations", "port captain", "logistics", "crewing", "hse"],
    "finance":    ["finance", "accounts", "controller", "treasury"],
}

# Titles that BUY or influence spare-parts purchases = decision makers
DECISION_MAKER_KEYWORDS = [
    "purchas", "procurement", "technical director", "technical manager",
    "fleet manager", "superintendent", "chief engineer", "managing director",
    "ceo", "coo", "owner", "general manager", "head of technical",
    "head of purchasing", "supply chain", "materials manager", "buyer",
]


def classify_seniority(title: str) -> str:
    t = (title or "").lower()
    for level, patterns in SENIORITY_RULES:
        if any(re.search(p, t) for p in patterns):
            return level
    return "unknown"


def classify_department(title: str) -> str:
    t = (title or "").lower()
    scores = {}
    for dept, keywords in DEPARTMENT_RULES.items():
        hits = sum(1 for k in keywords if k in t)
        if hits:
            scores[dept] = hits
    return max(scores, key=scores.get) if scores else ""


def is_decision_maker(title: str) -> bool:
    t = (title or "").lower()
    return any(k in t for k in DECISION_MAKER_KEYWORDS)


def split_name(full_name: str) -> tuple[str, str]:
    parts = re.sub(r"[^a-zA-Z\s\-']", "", full_name or "").strip().split()
    if len(parts) >= 2:
        return parts[0], parts[-1]
    if len(parts) == 1:
        return parts[0], ""
    return "", ""


def enrich_contact(contact) -> None:
    """Populate seniority/department/decision-maker/name fields on a Contact."""
    if contact.name and not contact.first_name:
        contact.first_name, contact.last_name = split_name(contact.name)
    contact.seniority = classify_seniority(contact.title)
    dept = classify_department(contact.title)
    if dept:
        contact.department = dept
    contact.is_decision_maker = is_decision_maker(contact.title)
