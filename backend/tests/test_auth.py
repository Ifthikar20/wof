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


def test_me_is_null_for_anonymous_and_patch_requires_login(client, db):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 200 and res.json() is None
    assert client.patch("/api/v1/auth/me", {"bio": "x"}, format="json").status_code == 403


def test_no_api_route_ends_with_a_slash():
    """The Next.js /api proxy strips trailing slashes; a slash-terminated Django route
    would 301 back to itself through the proxy forever."""
    from django.urls import get_resolver
    from django.urls.resolvers import URLResolver

    def walk(patterns, prefix=""):
        for p in patterns:
            route = prefix + str(p.pattern)
            if isinstance(p, URLResolver):
                yield from walk(p.url_patterns, route)
            else:
                yield route

    api_routes = [r for r in walk(get_resolver().url_patterns) if r.startswith("api/")]
    assert api_routes
    assert [r for r in api_routes if r.endswith("/")] == []


def test_me_reports_whether_the_server_lets_the_founder_publish(client, founder, settings):
    from .conftest import auth

    auth(client, founder)
    settings.REQUIRE_2FA_FOR_FOUNDERS = False
    me = client.get("/api/v1/auth/me").json()
    assert me["can_publish"] is True and me["needs_2fa"] is False
    settings.REQUIRE_2FA_FOR_FOUNDERS = True
    me = client.get("/api/v1/auth/me").json()
    assert me["can_publish"] is False and me["needs_2fa"] is True
    assert (
        client.post(
            "/api/v1/stories", {"title": "x", "body_markdown": "y"}, format="json"
        ).status_code
        == 403
    )
