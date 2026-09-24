from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.verification.models import Company, FounderProfile

PASSWORD = "correct horse battery staple 42"


@pytest.fixture(autouse=True)
def _clear_cache():
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def client():
    return APIClient()


def make_user(email="reader@example.org", handle="reader", **extra):
    return User.objects.create_user(email=email, password=PASSWORD, handle=handle, **extra)


def make_founder(email="ada@acme.io", handle="ada", company="Acme", domain="acme.io"):
    user = make_user(email=email, handle=handle, display_name=handle.title())
    co, _ = Company.objects.get_or_create(domain=domain, defaults={"name": company})
    now = timezone.now()
    FounderProfile.objects.create(
        user=user, company=co, title="CEO", verified_at=now, expires_at=now + timedelta(days=365)
    )
    return user


@pytest.fixture
def reader(db):
    return make_user()


@pytest.fixture
def founder(db):
    return make_founder()


@pytest.fixture
def moderator(db):
    return make_user(email="mod@wof.test", handle="mod", role=User.Role.MODERATOR)


def auth(client, user):
    client.force_authenticate(user=user)
    return client


class bypass_append_only:
    """Simulate an attacker with raw DB access by disabling the Postgres append-only
    triggers (a no-op on SQLite, which has no triggers)."""

    TABLES = ("audit_auditlog", "stories_storyrevision")

    def _toggle(self, action):
        from django.db import connection

        if connection.vendor == "postgresql":
            with connection.cursor() as cur:
                for table in self.TABLES:
                    cur.execute(f"ALTER TABLE {table} {action} TRIGGER USER")  # noqa: S608

    def __enter__(self):
        self._toggle("DISABLE")

    def __exit__(self, *exc):
        self._toggle("ENABLE")
