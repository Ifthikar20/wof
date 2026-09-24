from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import dns.exception
import dns.resolver
from django.conf import settings

_DATA = Path(__file__).parent / "data" / "free_email_domains.txt"


@lru_cache(maxsize=1)
def free_email_domains() -> frozenset[str]:
    lines = _DATA.read_text().splitlines()
    return frozenset(line.strip().lower() for line in lines if line and not line.startswith("#"))


def email_domain(email: str) -> str:
    return email.rsplit("@", 1)[-1].strip().lower().rstrip(".")


def registrable_suffix_match(email_dom: str, company_dom: str) -> bool:
    """work email must be on the company domain or a subdomain of it."""
    return email_dom == company_dom or email_dom.endswith("." + company_dom)


def is_free_email_domain(domain: str) -> bool:
    domain = domain.lower()
    blocked = free_email_domains()
    parts = domain.split(".")
    # Also block subdomains of blocked providers (e.g. x.mailinator.com).
    return any(".".join(parts[i:]) in blocked for i in range(len(parts) - 1))


def has_mx_record(domain: str) -> bool:
    if not settings.VERIFICATION_CHECK_MX:
        return True
    try:
        return len(dns.resolver.resolve(domain, "MX", lifetime=3)) > 0
    except (dns.exception.DNSException, OSError):
        return False


ALLOWED_EVIDENCE_HOSTS = {
    "linkedin_url": {"linkedin.com", "www.linkedin.com"},
    "crunchbase_url": {"crunchbase.com", "www.crunchbase.com"},
}


def valid_evidence_url(field: str, url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname in ALLOWED_EVIDENCE_HOSTS[field]
