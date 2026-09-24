"""Cloudflare Turnstile (privacy-friendly CAPTCHA) server-side verification."""

import json
import logging
import urllib.parse
import urllib.request

from django.conf import settings
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)
VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def verify_turnstile(token: str | None, ip: str) -> bool:
    secret = settings.TURNSTILE_SECRET_KEY
    if not secret:
        return True  # disabled in dev/test; prod settings refuse to start without it
    if not token:
        return False
    data = urllib.parse.urlencode({"secret": secret, "response": token, "remoteip": ip}).encode()
    try:
        with urllib.request.urlopen(VERIFY_URL, data=data, timeout=5) as resp:  # noqa: S310
            return bool(json.load(resp).get("success"))
    except Exception:  # fail closed: a bot check that cannot run must not pass
        logger.warning("turnstile verification unavailable")
        return False


def require_turnstile(request) -> None:
    from .net import client_ip

    if not verify_turnstile(request.data.get("turnstile_token"), client_ip(request)):
        raise ValidationError({"turnstile_token": "Bot check failed. Please retry."})
