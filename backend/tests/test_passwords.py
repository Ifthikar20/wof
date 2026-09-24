import re

import pytest
from django.core import mail
from rest_framework.test import APIClient

from apps.audit.models import AuditLog

from .conftest import PASSWORD

pytestmark = pytest.mark.django_db
NEW = "a brand new long passphrase 77"


def reset_link():
    body = mail.outbox[-1].body
    uid, token = re.search(r"uid=([^&\s]+)&token=([^\s]+)", body).groups()
    return uid, token


def test_request_does_not_reveal_accounts(client, reader):
    known = client.post("/api/v1/auth/password/reset", {"email": reader.email}, format="json")
    unknown = client.post(
        "/api/v1/auth/password/reset", {"email": "nobody@example.org"}, format="json"
    )
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert len(mail.outbox) == 1


def test_cooldown_stops_inbox_flooding(client, reader):
    for _ in range(3):
        client.post("/api/v1/auth/password/reset", {"email": reader.email}, format="json")
    assert len(mail.outbox) == 1


def test_reset_flow_is_single_use_and_signs_out_everywhere(reader):
    other_device = APIClient()
    other_device.login(email=reader.email, password=PASSWORD)
    assert other_device.get("/api/v1/auth/me").json()["handle"] == reader.handle

    c = APIClient()
    c.post("/api/v1/auth/password/reset", {"email": reader.email}, format="json")
    uid, token = reset_link()
    res = c.post(
        "/api/v1/auth/password/reset/confirm",
        {"uid": uid, "token": token, "password": NEW},
        format="json",
    )
    assert res.status_code == 200
    # the same link can't be used twice
    again = c.post(
        "/api/v1/auth/password/reset/confirm",
        {"uid": uid, "token": token, "password": NEW + "x"},
        format="json",
    )
    assert again.status_code == 400
    # the other device's session no longer works
    assert other_device.get("/api/v1/auth/me").json() is None
    # new password works; notification email sent; audited
    assert (
        c.post(
            "/api/v1/auth/login", {"email": reader.email, "password": NEW}, format="json"
        ).status_code
        == 200
    )
    assert "password was changed" in mail.outbox[-1].subject
    assert AuditLog.objects.filter(action="auth.password_reset").exists()


def test_reset_rejects_forged_token_and_weak_password(client, reader):
    client.post("/api/v1/auth/password/reset", {"email": reader.email}, format="json")
    uid, token = reset_link()
    assert (
        client.post(
            "/api/v1/auth/password/reset/confirm",
            {"uid": uid, "token": "forged-token", "password": NEW},
            format="json",
        ).status_code
        == 400
    )
    weak = client.post(
        "/api/v1/auth/password/reset/confirm",
        {"uid": uid, "token": token, "password": "short"},
        format="json",
    )
    assert weak.status_code == 400 and "password" in weak.json()["error"]["fields"]


def test_reset_clears_lockout(client, reader):
    for _ in range(6):
        client.post(
            "/api/v1/auth/login", {"email": reader.email, "password": "wrong"}, format="json"
        )
    client.post("/api/v1/auth/password/reset", {"email": reader.email}, format="json")
    uid, token = reset_link()
    client.post(
        "/api/v1/auth/password/reset/confirm",
        {"uid": uid, "token": token, "password": NEW},
        format="json",
    )
    assert (
        client.post(
            "/api/v1/auth/login", {"email": reader.email, "password": NEW}, format="json"
        ).status_code
        == 200
    )


def test_change_password_keeps_this_session_only(reader):
    here, elsewhere = APIClient(), APIClient()
    for c in (here, elsewhere):
        c.login(email=reader.email, password=PASSWORD)
    bad = here.post(
        "/api/v1/auth/password", {"current_password": "nope", "new_password": NEW}, format="json"
    )
    assert bad.status_code == 400 and "current_password" in bad.json()["error"]["fields"]
    ok = here.post(
        "/api/v1/auth/password", {"current_password": PASSWORD, "new_password": NEW}, format="json"
    )
    assert ok.status_code == 200
    assert here.get("/api/v1/auth/me").json()["handle"] == reader.handle
    assert elsewhere.get("/api/v1/auth/me").json() is None
