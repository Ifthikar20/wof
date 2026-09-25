"""
Zero-dependency local mode: run the whole app with nothing but Python and Node.

    DJANGO_SETTINGS_MODULE=wof.settings.local

* SQLite (WAL mode) instead of PostgreSQL
* in-memory cache instead of Redis; sessions in the database
* Celery tasks run inline (emails, image processing) instead of on a worker
* emails are written to backend/.local/mail/ instead of being sent
* uploads and processed images live in backend/.local/media/, served by Django

Everything security-relevant still runs (sanitisation, hash chains, throttles, permissions);
only the infrastructure is swapped. Never use this module outside a developer machine.
"""

from .dev import *  # noqa: F403
from .dev import BASE_DIR, SITE_URL, env

LOCAL_DIR = BASE_DIR / ".local"
LOCAL_DIR.mkdir(exist_ok=True)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": LOCAL_DIR / "db.sqlite3",
        "OPTIONS": {
            "timeout": 20,
            # WAL lets readers proceed while a write is in flight (much better under a busy dev UI).
            "init_command": (
                "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA foreign_keys=ON;"
            ),
            "transaction_mode": "IMMEDIATE",
        },
    }
}

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
SESSION_ENGINE = "django.contrib.sessions.backends.db"

CELERY_BROKER_URL = "memory://"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = LOCAL_DIR / "mail"

LOCAL_MEDIA_ROOT = LOCAL_DIR / "media"
MEDIA_CDN_URL = f"{SITE_URL}/local-media"  # proxied to Django by next.config.ts

# Optional: point the prompt delay etc. at env as usual; nothing else differs from dev.
LOG_LEVEL = env("LOG_LEVEL", "INFO")
