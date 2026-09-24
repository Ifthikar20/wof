from .base import *  # noqa: F403
from .base import FIELD_ENCRYPTION_KEYS, TURNSTILE_SECRET_KEY, ImproperlyConfigured, env

DEBUG = False

SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = [r"^healthz$"]
SECURE_HSTS_SECONDS = 63072000  # 2 years
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_NAME = "__Host-wof_session"  # __Host- prefix: Secure, no Domain, Path=/

DATABASES["default"]["OPTIONS"]["sslmode"] = env("POSTGRES_SSLMODE", "require")  # noqa: F405

EMAIL_USE_TLS = env("EMAIL_USE_TLS", "true").lower() in {"1", "true", "yes"}
EMAIL_TIMEOUT = 10

if not FIELD_ENCRYPTION_KEYS:
    raise ImproperlyConfigured("FIELD_ENCRYPTION_KEYS must be set in production")
if not TURNSTILE_SECRET_KEY:
    raise ImproperlyConfigured("TURNSTILE_SECRET_KEY must be set in production")
