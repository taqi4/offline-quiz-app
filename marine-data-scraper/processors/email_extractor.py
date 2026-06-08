"""
Advanced email extraction and validation utilities.
- Regex extraction from raw HTML/text
- MX record validation (optional, requires dnspython)
- Email type inference (general, purchasing, technical, management)
"""
import re
import logging

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(
    r"(?<![a-zA-Z0-9._%+\-])"         # no preceding valid chars
    r"([a-zA-Z0-9._%+\-]{1,64})"      # local part
    r"@"
    r"([a-zA-Z0-9.\-]{1,253})"        # domain
    r"\.([a-zA-Z]{2,10})"             # TLD
    r"(?![a-zA-Z0-9.])",              # no trailing valid chars
)

# Obfuscation patterns commonly used on websites
_OBFUSCATION = [
    (r"\[at\]",     "@"),
    (r"\s+at\s+",   "@"),
    (r"\(at\)",     "@"),
    (r"\[dot\]",    "."),
    (r"\s+dot\s+",  "."),
    (r"\(dot\)",    "."),
]

# Email type inference keywords in the local part
_TYPE_HINTS = {
    "purchasing": ["purchas", "procurement", "supply", "spare", "order", "buy"],
    "technical":  ["tech", "engineer", "maintenance", "repair", "fleet"],
    "management": ["ceo", "coo", "cfo", "director", "manager", "head", "president",
                   "vp", "md", "gm", "info", "admin"],
    "sales":      ["sales", "commercial", "charter", "trade"],
    "general":    ["info", "contact", "office", "mail", "hello", "enquir"],
}

# Common throwaway / spam domains to skip
_SKIP_DOMAINS = {
    "example.com", "test.com", "foo.com", "bar.com", "domain.com",
    "email.com", "mail.com", "noreply.com", "no-reply.com",
    "sentry.io", "sendgrid.net", "mailchimp.com",
}


def extract_emails(text: str) -> list[dict]:
    """
    Extract all emails from text. Returns list of dicts with keys:
    address, email_type, confidence.
    """
    # Deobfuscate first
    for pattern, replacement in _OBFUSCATION:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    found = {}
    for m in _EMAIL_RE.finditer(text):
        local  = m.group(1)
        domain = m.group(2)
        tld    = m.group(3)
        address = f"{local}@{domain}.{tld}".lower()

        if domain + "." + tld in _SKIP_DOMAINS:
            continue
        if len(local) < 1 or len(domain) < 2:
            continue
        # Skip image file extensions confused as TLDs
        if tld in ("png", "jpg", "gif", "svg", "css", "js", "xml"):
            continue

        if address not in found:
            found[address] = {
                "address":    address,
                "email_type": _infer_type(local),
                "confidence": _score_confidence(local, domain),
            }

    return list(found.values())


def _infer_type(local_part: str) -> str:
    local_lower = local_part.lower()
    for etype, hints in _TYPE_HINTS.items():
        if any(hint in local_lower for hint in hints):
            return etype
    return "general"


def _score_confidence(local: str, domain: str) -> float:
    score = 1.0
    # Penalise very short locals
    if len(local) <= 2:
        score -= 0.3
    # Penalise if looks like a hash
    if re.match(r"^[a-f0-9]{8,}$", local):
        score -= 0.5
    # Penalise generic free email providers (lower value for B2B)
    if domain in ("gmail", "yahoo", "hotmail", "outlook", "protonmail"):
        score -= 0.2
    return max(0.0, round(score, 2))


def validate_mx(domain: str) -> bool:
    """Check if domain has MX records (requires dnspython). Returns True if valid."""
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, "MX", lifetime=5)
        return len(answers) > 0
    except Exception:
        return False
