import os

os.environ.setdefault("DJANGO_SECRET_KEY", "dev-insecure-secret-key-change-me-0123456789abcdef")

from .base import *  # noqa: E402,F403
from .base import env, env_bool, env_list  # noqa: E402

DEBUG = True
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,backend")

# Local HTTP: cookies cannot be Secure without TLS.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

PWNED_PASSWORDS_CHECK = env_bool("PWNED_PASSWORDS_CHECK", False)
VERIFICATION_CHECK_MX = env_bool("VERIFICATION_CHECK_MX", False)
REQUIRE_2FA_FOR_FOUNDERS = env_bool("REQUIRE_2FA_FOR_FOUNDERS", False)
REQUIRE_2FA_FOR_STAFF = env_bool("REQUIRE_2FA_FOR_STAFF", False)

if not FIELD_ENCRYPTION_KEYS:  # noqa: F405
    # Deterministic dev-only key. Never used outside DEBUG.
    FIELD_ENCRYPTION_KEYS = ["ZGV2LW9ubHktZmllbGQta2V5LTMyLWJ5dGVzLWxvbmc="]

if env("USE_SQLITE", ""):
    DATABASES = {
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "dev.sqlite3"}  # noqa: F405
    }

# Serve admin static straight from app directories (no collectstatic needed with the
# read-only source mount used by docker compose).
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True

# Local load testing: scale every throttle (e.g. DEV_THROTTLE_SCALE=20 when many automated
# browsers share one IP). Dev only; production rates are fixed in base.py.
if _scale := env("DEV_THROTTLE_SCALE", ""):
    _factor = max(1, int(_scale))
    REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
        scope: f"{int(rate.split('/')[0]) * _factor}/{rate.split('/')[1]}"
        for scope, rate in REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"].items()  # noqa: F405
    }
