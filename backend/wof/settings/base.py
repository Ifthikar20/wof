"""
Base settings shared by every environment.

Security-relevant defaults live here so that dev/test/prod can only *relax* them
explicitly (and visibly) rather than forgetting to turn them on.
"""

import os
from datetime import timedelta
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env(name: str, default: str | None = None, *, required: bool = False) -> str:
    value = os.environ.get(name, default)
    if required and not value:
        raise ImproperlyConfigured(f"Environment variable {name} is required")
    return value or ""


def env_bool(name: str, default: bool = False) -> bool:
    return env(name, str(default)).lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in env(name, default).split(",") if item.strip()]


SECRET_KEY = env("DJANGO_SECRET_KEY", required=True)
DEBUG = False
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

# The public site origin (Next.js). The API is served under the same origin via a
# reverse-proxy rewrite (/api/* -> Django), so cookies are first-party and no CORS is needed.
SITE_URL = env("SITE_URL", "http://localhost:3000")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", SITE_URL)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.common",
    "apps.audit",
    "apps.accounts",
    "apps.verification",
    "apps.stories",
    "apps.engagement",
    "apps.moderation",
    "apps.digest",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.common.middleware.SecurityHeadersMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "wof.urls"
# Non-default admin path in production cuts drive-by scanning noise (not a security control).
ADMIN_URL = env("DJANGO_ADMIN_URL", "admin/")
WSGI_APPLICATION = "wof.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "wof"),
        "USER": env("POSTGRES_USER", "wof_app"),
        "PASSWORD": env("POSTGRES_PASSWORD", ""),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {"sslmode": env("POSTGRES_SSLMODE", "prefer")},
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REDIS_URL = env("REDIS_URL", "redis://localhost:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

# --- Authentication -------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["apps.accounts.backends.EmailBackend"]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    {"NAME": "apps.accounts.validators.PwnedPasswordValidator"},
]
# Query HaveIBeenPwned (k-anonymity range API) on signup / password change.
PWNED_PASSWORDS_CHECK = env_bool("PWNED_PASSWORDS_CHECK", True)

LOGIN_MAX_FAILURES = 5  # failures before temporary lockout kicks in
LOGIN_LOCKOUT_MAX_MINUTES = 60
REQUIRE_2FA_FOR_FOUNDERS = env_bool("REQUIRE_2FA_FOR_FOUNDERS", True)
REQUIRE_2FA_FOR_STAFF = env_bool("REQUIRE_2FA_FOR_STAFF", True)

# --- Sessions & cookies ---------------------------------------------------------------------
SESSION_ENGINE = "django.contrib.sessions.backends.cache"  # Redis-backed, revocable
SESSION_COOKIE_NAME = "wof_session"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_AGE = int(timedelta(days=14).total_seconds())
CSRF_COOKIE_NAME = "wof_csrftoken"
CSRF_COOKIE_HTTPONLY = False  # the SPA must read it to echo it in X-CSRFToken
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = True
CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"

# --- Transport / browser security headers ---------------------------------------------------
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 0  # enabled in prod.py
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Only trust client-IP headers when running behind a known proxy (Cloudflare / load balancer).
TRUSTED_PROXY_IP_HEADER = env("TRUSTED_PROXY_IP_HEADER", "")  # e.g. "HTTP_CF_CONNECTING_IP"

# Hard caps on request sizes: stories are text; images go straight to object storage.
DATA_UPLOAD_MAX_MEMORY_SIZE = 512 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 512 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 200

# --- Field-level encryption (verification evidence, TOTP secrets) ---------------------------
# Comma-separated Fernet keys; the first encrypts, all decrypt (supports key rotation).
FIELD_ENCRYPTION_KEYS = env_list("FIELD_ENCRYPTION_KEYS", "")

# --- Django REST Framework ------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_THROTTLE_CLASSES": [
        "apps.common.throttles.BurstRateThrottle",
        "apps.common.throttles.SustainedRateThrottle",
        "apps.common.throttles.ScopedThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "burst": "60/min",
        "sustained": "2000/day",
        "feed": "120/min",
        "auth": "10/min",
        "signup": "5/hour",
        "verification": "5/hour",
        "comment": "20/hour",
        "report": "20/hour",
        "subscribe": "5/hour",
        "upload": "30/hour",
        "write": "60/hour",
    },
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.FeedCursorPagination",
    "EXCEPTION_HANDLER": "apps.common.exceptions.api_exception_handler",
}

# --- Object storage (S3 / R2 / MinIO) -------------------------------------------------------
S3_ENDPOINT_URL = env("S3_ENDPOINT_URL", "")
S3_PUBLIC_ENDPOINT_URL = env("S3_PUBLIC_ENDPOINT_URL", S3_ENDPOINT_URL)
S3_REGION = env("S3_REGION", "auto")
S3_ACCESS_KEY_ID = env("S3_ACCESS_KEY_ID", "")
S3_SECRET_ACCESS_KEY = env("S3_SECRET_ACCESS_KEY", "")
S3_PRIVATE_BUCKET = env("S3_PRIVATE_BUCKET", "wof-uploads")  # raw uploads, never public
S3_PUBLIC_BUCKET = env("S3_PUBLIC_BUCKET", "wof-media")  # processed variants, behind CDN
MEDIA_CDN_URL = env("MEDIA_CDN_URL", "http://localhost:9000/wof-media")
UPLOAD_MAX_BYTES = 10 * 1024 * 1024
UPLOAD_ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"]
UPLOAD_MAX_PIXELS = 40_000_000  # decompression-bomb guard

# --- Email ----------------------------------------------------------------------------------
EMAIL_BACKEND = env("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", "localhost")
EMAIL_PORT = int(env("EMAIL_PORT", "1025"))
EMAIL_HOST_USER = env("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", "Wall of Founders <hello@walloffounders.local>")
DIGEST_FROM_EMAIL = env(
    "DIGEST_FROM_EMAIL", "Wall of Founders Digest <digest@walloffounders.local>"
)

# --- Bot protection -------------------------------------------------------------------------
TURNSTILE_SECRET_KEY = env("TURNSTILE_SECRET_KEY", "")  # empty => check disabled (dev only)

# --- Founder verification -------------------------------------------------------------------
VERIFICATION_TOKEN_TTL = timedelta(hours=24)
VERIFICATION_VALIDITY = timedelta(days=365)
VERIFICATION_CHECK_MX = env_bool("VERIFICATION_CHECK_MX", True)

# --- Celery ---------------------------------------------------------------------------------
CELERY_BROKER_URL = env("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = None
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]

# --- Static / i18n --------------------------------------------------------------------------
STATIC_URL = "/django-static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Logging (structured, no secrets / PII in messages) -------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"ts":"%(asctime)s","level":"%(levelname)s",'
            '"logger":"%(name)s","msg":"%(message)s"}'
        }
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
    "loggers": {"django.security": {"handlers": ["console"], "level": "WARNING"}},
}
