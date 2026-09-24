"""
Email-provider webhook (Postmark): hard bounces, spam complaints and list-unsubscribes
mark the subscription as bounced so we never mail that address again. Keeping complaint
rates low is required by Gmail/Yahoo bulk-sender rules.

Postmark authenticates webhooks with HTTP Basic credentials embedded in the webhook URL
(https://user:pass@api.example.com/api/v1/digest/webhooks/postmark). The endpoint is
disabled (404) until EMAIL_WEBHOOK_USER and EMAIL_WEBHOOK_PASSWORD are configured.
"""

import base64
import hmac
import logging

from django.conf import settings
from django.http import Http404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.common.throttles import ScopedThrottle

from .models import Subscription

logger = logging.getLogger(__name__)

SUPPRESS_BOUNCE_TYPES = {
    "HardBounce",
    "SpamNotification",
    "BadEmailAddress",
    "ManuallyDeactivated",
    "Blocked",
    "SpamComplaint",
}


def _authorized(request) -> bool:
    user, password = settings.EMAIL_WEBHOOK_USER, settings.EMAIL_WEBHOOK_PASSWORD
    header = request.META.get("HTTP_AUTHORIZATION", "")
    if not header.startswith("Basic "):
        return False
    try:
        given = base64.b64decode(header[6:]).decode()
    except (ValueError, UnicodeDecodeError):
        return False
    return hmac.compare_digest(given.encode(), f"{user}:{password}".encode())


def _suppress(email: str, reason: str) -> int:
    email = (email or "").strip().lower()
    if not email:
        return 0
    n = (
        Subscription.objects.filter(email=email)
        .exclude(status=Subscription.Status.BOUNCED)
        .update(status=Subscription.Status.BOUNCED, unsubscribed_at=timezone.now())
    )
    if n:
        logger.info("digest subscription suppressed (%s)", reason)  # no address in logs
    return n


class _WebhookThrottle(ScopedThrottle):
    scope = "webhook"

    def get_rate(self):
        return settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["webhook"]


@csrf_exempt
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([_WebhookThrottle])
def postmark_webhook(request):
    if not (settings.EMAIL_WEBHOOK_USER and settings.EMAIL_WEBHOOK_PASSWORD):
        raise Http404
    if not _authorized(request):
        return Response(status=401, headers={"WWW-Authenticate": 'Basic realm="webhooks"'})

    event = request.data if isinstance(request.data, dict) else {}
    record = event.get("RecordType")
    if record == "Bounce" and event.get("Type") in SUPPRESS_BOUNCE_TYPES:
        _suppress(event.get("Email", ""), f"bounce:{event.get('Type')}")
    elif record == "SpamComplaint":
        _suppress(event.get("Email", ""), "complaint")
    elif record == "SubscriptionChange" and event.get("SuppressSending"):
        _suppress(event.get("Recipient", ""), "unsubscribe")
    # Everything else (deliveries, soft bounces, opens we never track) is acknowledged and ignored.
    return Response({"ok": True})
