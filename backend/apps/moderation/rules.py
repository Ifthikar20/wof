"""
Deterministic, explainable spam/abuse heuristics (no ML, per product decision).
Each rule returns a flag name; any flag holds the content for human review.
"""

import re
from datetime import timedelta

from django.utils import timezone

URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)
REPEAT_RE = re.compile(r"(.)\1{9,}")
BLOCKED_TERMS = {
    "crypto giveaway",
    "guaranteed returns",
    "work from home and earn",
    "whatsapp me",
    "telegram me",
    "dm for promo",
    "buy followers",
    "casino bonus",
}
NEW_ACCOUNT_AGE = timedelta(hours=24)


def check_text(text: str, author) -> list[str]:
    flags: list[str] = []
    lowered = text.lower()
    links = len(URL_RE.findall(text))
    if links > 2:
        flags.append("too_many_links")
    if links and timezone.now() - author.date_joined < NEW_ACCOUNT_AGE:
        flags.append("new_account_link")
    if REPEAT_RE.search(text):
        flags.append("repeated_characters")
    if any(term in lowered for term in BLOCKED_TERMS):
        flags.append("blocked_term")
    letters = [c for c in text if c.isalpha()]
    if len(letters) > 20 and sum(c.isupper() for c in letters) / len(letters) > 0.7:
        flags.append("shouting")
    return flags
