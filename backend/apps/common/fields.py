"""
Encrypted-at-rest model field for sensitive values (verification evidence, TOTP secrets).

Uses Fernet (AES-128-CBC + HMAC-SHA256) via MultiFernet so keys can be rotated:
the first key in FIELD_ENCRYPTION_KEYS encrypts, every key can decrypt.
"""

from functools import lru_cache

from cryptography.fernet import Fernet, MultiFernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models


@lru_cache(maxsize=1)
def _fernet(keys: tuple[str, ...]) -> MultiFernet:
    if not keys:
        raise ImproperlyConfigured("FIELD_ENCRYPTION_KEYS is empty")
    return MultiFernet([Fernet(k.encode()) for k in keys])


def fernet() -> MultiFernet:
    return _fernet(tuple(settings.FIELD_ENCRYPTION_KEYS))


class EncryptedTextField(models.TextField):
    description = "Text encrypted at rest with Fernet"

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value in (None, ""):
            return value
        return fernet().encrypt(value.encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value in (None, ""):
            return value
        return fernet().decrypt(value.encode()).decode()
