from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from apps.verification.models import FounderProfile, VerificationRequest

from .conftest import auth

pytestmark = pytest.mark.django_db

VALID = {
    "company_name": "Rocket Labs",
    "company_domain": "rocketlabs.dev",
    "work_email": "jane@rocketlabs.dev",
    "role_title": "Co-founder & CTO",
    "linkedin_url": "https://www.linkedin.com/in/jane",
}


def submit(client, **overrides):
    return client.post("/api/v1/verification", {**VALID, **overrides}, format="json")


def token_from_mail() -> str:
    body = mail.outbox[-1].body
    return body.split("token=")[1].split()[0]


def test_free_email_rejected(client, reader):
    res = submit(auth(client, reader), work_email="jane@gmail.com", company_domain="gmail.com")
    assert res.status_code == 400


def test_email_must_match_company_domain(client, reader):
    res = submit(auth(client, reader), work_email="jane@other.dev")
    assert res.status_code == 400


def test_evidence_required_and_host_checked(client, reader):
    auth(client, reader)
    assert submit(client, linkedin_url="").status_code == 400
    assert submit(client, linkedin_url="https://evil.com/in/jane").status_code == 400
    assert submit(client, linkedin_url="http://www.linkedin.com/in/jane").status_code == 400


def test_full_flow_single_use_token_and_approval(client, reader, moderator):
    auth(client, reader)
    res = submit(client)
    assert res.status_code == 201
    assert res.json()["status"] == "email_pending"
    token = token_from_mail()
    req = VerificationRequest.objects.get()
    assert req.email_token_hash and token not in req.email_token_hash  # only hash stored

    assert (
        client.post(
            "/api/v1/verification/confirm-email", {"token": token}, format="json"
        ).status_code
        == 200
    )
    # single use
    assert (
        client.post(
            "/api/v1/verification/confirm-email", {"token": token}, format="json"
        ).status_code
        == 400
    )

    mod_client = auth(type(client)(), moderator)
    queue = mod_client.get("/api/v1/moderation/verifications").json()["results"]
    assert [r["work_email"] for r in queue] == ["jane@rocketlabs.dev"]
    res = mod_client.post(
        f"/api/v1/moderation/verifications/{req.id}/decision",
        {"decision": "approve", "reason": "LinkedIn matches"},
        format="json",
    )
    assert res.status_code == 200
    reader.refresh_from_db()
    assert reader.is_verified_founder
    assert FounderProfile.objects.get(user=reader).company.domain == "rocketlabs.dev"
    req.refresh_from_db()
    assert req.notes == ""  # evidence purged after decision


def test_expired_token_rejected(client, reader):
    auth(client, reader)
    submit(client)
    token = token_from_mail()
    VerificationRequest.objects.update(email_token_expires_at=timezone.now() - timedelta(seconds=1))
    res = client.post("/api/v1/verification/confirm-email", {"token": token}, format="json")
    assert res.status_code == 400


def test_other_users_token_does_not_work(client, reader, founder):
    auth(client, reader)
    submit(client)
    token = token_from_mail()
    other = auth(type(client)(), founder)
    assert (
        other.post(
            "/api/v1/verification/confirm-email", {"token": token}, format="json"
        ).status_code
        == 400
    )


def test_readers_cannot_access_moderation(client, reader):
    assert auth(client, reader).get("/api/v1/moderation/verifications").status_code == 403


def test_expiry_removes_founder_rights(founder):
    from apps.verification.services import expire_due

    FounderProfile.objects.update(expires_at=timezone.now() - timedelta(days=1))
    assert expire_due() == 1
    founder.refresh_from_db()
    assert not founder.is_verified_founder
