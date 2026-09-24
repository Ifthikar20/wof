import hashlib
import logging
import urllib.request

from django.conf import settings
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class PwnedPasswordValidator:
    """
    Reject passwords that appear in known breaches using the HaveIBeenPwned range API.
    Only the first 5 hex chars of the SHA-1 leave the server (k-anonymity).
    Fails open on network errors so an outage cannot block every signup.
    """

    def validate(self, password, user=None):
        if not settings.PWNED_PASSWORDS_CHECK:
            return
        digest = hashlib.sha1(password.encode(), usedforsecurity=False).hexdigest().upper()
        prefix, suffix = digest[:5], digest[5:]
        req = urllib.request.Request(
            f"https://api.pwnedpasswords.com/range/{prefix}",
            headers={"Add-Padding": "true", "User-Agent": "wall-of-founders"},
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:  # noqa: S310
                body = resp.read().decode()
        except Exception:
            logger.warning("pwned-passwords check unavailable")
            return
        for line in body.splitlines():
            candidate, _, count = line.partition(":")
            if candidate == suffix and int(count or 0) > 0:
                raise ValidationError(
                    "This password has appeared in a data breach. Please choose another.",
                    code="password_pwned",
                )

    def get_help_text(self):
        return "Your password must not appear in known data breaches."
