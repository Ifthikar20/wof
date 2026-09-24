import pytest

from apps.accounts.models import User

from .conftest import PASSWORD, make_user

pytestmark = pytest.mark.django_db


def test_signup_then_me(client):
    res = client.post(
        "/api/v1/auth/signup",
        {"email": "New@Example.org", "password": PASSWORD, "handle": "newbie"},
        format="json",
    )
    assert res.status_code == 201
    assert res.json()["email"] == "new@example.org"
    assert client.get("/api/v1/auth/me").json()["handle"] == "newbie"


def test_signup_rejects_weak_password_and_reserved_handle(client):
    res = client.post(
        "/api/v1/auth/signup",
        {"email": "a@example.org", "password": "password", "handle": "admin"},
        format="json",
    )
    assert res.status_code == 400
    fields = res.json()["error"]["fields"]
    assert "handle" in fields


def test_login_uses_generic_error_and_locks_out(client, reader):
    for _ in range(5):
        res = client.post(
            "/api/v1/auth/login",
            {"email": reader.email, "password": "wrong-password"},
            format="json",
        )
        assert res.status_code == 401
        assert res.json()["error"]["code"] == "invalid_credentials"
    res = client.post(
        "/api/v1/auth/login", {"email": reader.email, "password": PASSWORD}, format="json"
    )
    assert res.status_code == 429  # locked even with the right password
    reader.refresh_from_db()
    assert reader.locked_until is not None


def test_unknown_email_gets_same_error(client, db):
    res = client.post(
        "/api/v1/auth/login", {"email": "nobody@example.org", "password": "x"}, format="json"
    )
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "invalid_credentials"


def test_login_requires_totp_when_enabled(client, db):
    import pyotp

    user = make_user(email="t@example.org", handle="totp_user")
    user.totp_secret = pyotp.random_base32()
    user.totp_enabled = True
    user.save()
    res = client.post(
        "/api/v1/auth/login", {"email": user.email, "password": PASSWORD}, format="json"
    )
    assert res.json()["error"]["code"] == "otp_required"
    code = pyotp.TOTP(user.totp_secret).now()
    res = client.post(
        "/api/v1/auth/login",
        {"email": user.email, "password": PASSWORD, "otp": code},
        format="json",
    )
    assert res.status_code == 200
    # the same code cannot be replayed
    client.post("/api/v1/auth/logout")
    res = client.post(
        "/api/v1/auth/login",
        {"email": user.email, "password": PASSWORD, "otp": code},
        format="json",
    )
    assert res.status_code == 401


def test_csrf_enforced_for_session_clients(db):
    from rest_framework.test import APIClient

    user = make_user(email="c@example.org", handle="csrf_user")
    client = APIClient(enforce_csrf_checks=True)
    client.login(email=user.email, password=PASSWORD)
    res = client.patch("/api/v1/auth/me", {"bio": "hi"}, format="json")
    assert res.status_code == 403


def test_security_headers_and_cookie_flags(client, reader):
    res = client.post(
        "/api/v1/auth/login", {"email": reader.email, "password": PASSWORD}, format="json"
    )
    assert res.status_code == 200
    assert res["X-Frame-Options"] == "DENY"
    assert res["X-Content-Type-Options"] == "nosniff"
    assert "default-src 'none'" in res["Content-Security-Policy"]
    assert res["Cache-Control"] == "private, no-store"
    cookie = res.cookies["wof_session"]
    assert cookie["httponly"]
    assert cookie["samesite"] == "Lax"


def test_passwords_are_hashed(reader):
    assert PASSWORD not in User.objects.get(pk=reader.pk).password
