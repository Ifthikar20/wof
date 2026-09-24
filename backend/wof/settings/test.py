import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key-not-for-production-0123456789")

from .base import *  # noqa: E402,F403
from .base import env  # noqa: E402

DEBUG = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]  # speed only
PWNED_PASSWORDS_CHECK = False
VERIFICATION_CHECK_MX = False
REQUIRE_2FA_FOR_FOUNDERS = False
REQUIRE_2FA_FOR_STAFF = False
FIELD_ENCRYPTION_KEYS = ["dGVzdC1vbmx5LWZpZWxkLWtleS0zMi1ieXRlcy1sb24="]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Use Postgres when provided (CI), SQLite otherwise for fast local runs.
if not env("POSTGRES_HOST"):
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
