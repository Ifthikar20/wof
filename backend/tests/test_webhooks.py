import base64

import pytest
from rest_framework.test import APIClient

from apps.digest.models import Subscription

pytestmark = pytest.mark.django_db
URL = "/api/v1/digest/webhooks/postmark"


@pytest.fixture
def creds(settings):
    settings.EMAIL_WEBHOOK_USER = "postmark"
    settings.EMAIL_WEBHOOK_PASSWORD = "s3cret-webhook-pass"


def post(body, user="postmark", password="s3cret-webhook-pass"):
    c = APIClient()
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return c.post(URL, body, format="json", HTTP_AUTHORIZATION=f"Basic {token}")


def test_disabled_without_credentials():
    assert APIClient().post(URL, {}, format="json").status_code == 404


def test_rejects_wrong_or_missing_credentials(creds):
    assert APIClient().post(URL, {}, format="json").status_code == 401
    assert post({}, password="guess").status_code == 401


@pytest.mark.parametrize(
    "event",
    [
        {"RecordType": "Bounce", "Type": "HardBounce", "Email": "A@Example.org"},
        {"RecordType": "SpamComplaint", "Email": "a@example.org"},
        {"RecordType": "SubscriptionChange", "Recipient": "a@example.org", "SuppressSending": True},
    ],
)
def test_suppressing_events_mark_subscription_bounced(creds, event):
    Subscription.objects.create(email="a@example.org", status="active")
    assert post(event).status_code == 200
    assert Subscription.objects.get().status == "bounced"


def test_soft_bounce_is_ignored(creds):
    Subscription.objects.create(email="a@example.org", status="active")
    post({"RecordType": "Bounce", "Type": "SoftBounce", "Email": "a@example.org"})
    assert Subscription.objects.get().status == "active"


def test_bounced_addresses_are_not_resubscribed(creds, client):
    from django.core import mail

    Subscription.objects.create(email="a@example.org", status="active")
    post({"RecordType": "SpamComplaint", "Email": "a@example.org"})
    client.post("/api/v1/digest/subscribe", {"email": "a@example.org"}, format="json")
    assert Subscription.objects.get().status == "bounced"
    assert len(mail.outbox) == 0
