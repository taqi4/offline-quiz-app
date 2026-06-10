"""
Email pattern intelligence.

Given known emails at a company domain plus named contacts, infer the
corporate email naming convention and synthesise likely addresses for
decision-makers we have a name for but no direct email.

Patterns supported:
    {first}              -> john@acme.com
    {last}               -> smith@acme.com
    {first}.{last}       -> john.smith@acme.com
    {f}{last}            -> jsmith@acme.com
    {first}{last}        -> johnsmith@acme.com
    {f}.{last}           -> j.smith@acme.com
    {first}_{last}       -> john_smith@acme.com
    {last}.{first}       -> smith.john@acme.com
"""
import re
import logging

logger = logging.getLogger(__name__)

ROLE_PREFIXES = {
    "info", "sales", "contact", "admin", "office", "enquiries", "enquiry",
    "support", "hello", "mail", "marketing", "hr", "careers", "purchasing",
    "procurement", "technical", "service", "accounts", "finance", "general",
}


def _split_name(full_name: str) -> tuple[str, str]:
    parts = re.sub(r"[^a-zA-Z\s\-]", "", full_name or "").strip().split()
    if len(parts) >= 2:
        return parts[0].lower(), parts[-1].lower()
    if len(parts) == 1:
        return parts[0].lower(), ""
    return "", ""


def detect_pattern(known_email: str, full_name: str) -> str | None:
    """Infer the pattern template from one known personal email + its owner's name."""
    if "@" not in known_email:
        return None
    local = known_email.split("@", 1)[0].lower()
    if local in ROLE_PREFIXES:
        return None

    first, last = _split_name(full_name)
    if not first or not last:
        return None

    f, l = first[0], last[0]
    candidates = {
        f"{first}.{last}":  "{first}.{last}",
        f"{first}{last}":   "{first}{last}",
        f"{f}{last}":       "{f}{last}",
        f"{f}.{last}":      "{f}.{last}",
        f"{first}_{last}":  "{first}_{last}",
        f"{last}.{first}":  "{last}.{first}",
        f"{last}{first}":   "{last}{first}",
        f"{first}":         "{first}",
        f"{last}":          "{last}",
    }
    return candidates.get(local)


def apply_pattern(pattern: str, full_name: str, domain: str) -> str | None:
    """Generate an email address from a pattern template + name + domain."""
    first, last = _split_name(full_name)
    if not first:
        return None
    f = first[0] if first else ""
    l = last[0] if last else ""
    local = (pattern
             .replace("{first}", first)
             .replace("{last}", last)
             .replace("{f}", f)
             .replace("{l}", l))
    if "{" in local or not local.strip("._"):
        return None
    return f"{local}@{domain}"


def infer_company_pattern(session, company) -> str | None:
    """
    Look at a company's known personal emails + contacts to deduce its
    email pattern, store it on the company, and return it.
    """
    from database.models import Contact

    # Build name lookup by email
    name_by_email = {}
    for c in company.contacts:
        if c.email and c.name:
            name_by_email[c.email.lower()] = c.name

    for email in company.emails:
        owner = name_by_email.get(email.address.lower())
        if owner:
            pattern = detect_pattern(email.address, owner)
            if pattern:
                company.email_pattern = pattern
                logger.debug("Company %s pattern: %s", company.name, pattern)
                return pattern
    return None


def generate_contact_emails(session, company) -> int:
    """
    For contacts that have a name but no email, synthesise a pattern-based
    guess if we know the company's email pattern and domain. Marks them
    email_status='pattern_guess'. Returns number generated.
    """
    if not company.email_pattern:
        return 0

    # Determine corporate domain
    domain = _company_domain(company)
    if not domain:
        return 0

    generated = 0
    for contact in company.contacts:
        if contact.email or not contact.name:
            continue
        guess = apply_pattern(company.email_pattern, contact.name, domain)
        if guess:
            contact.email = guess
            contact.email_status = "pattern_guess"
            generated += 1
    if generated:
        session.commit()
    return generated


def _company_domain(company) -> str | None:
    # Prefer website domain
    if company.website:
        m = re.search(r"https?://(?:www\.)?([^/]+)", company.website)
        if m:
            return m.group(1).lower()
    # Fall back to the most common domain among non-free emails
    domains = {}
    for e in company.emails:
        if e.domain and not e.is_free:
            domains[e.domain] = domains.get(e.domain, 0) + 1
    if domains:
        return max(domains, key=domains.get)
    return None
