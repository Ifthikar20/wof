"""Stateless, signed tokens for digest confirm/unsubscribe links (nothing stored in the DB)."""

from django.core import signing

CONFIRM_SALT = "wof.digest.confirm"
UNSUB_SALT = "wof.digest.unsubscribe"
CONFIRM_MAX_AGE = 60 * 60 * 48


def make_confirm_token(sub_id) -> str:
    return signing.dumps(str(sub_id), salt=CONFIRM_SALT)


def read_confirm_token(token: str) -> str | None:
    try:
        return signing.loads(token, salt=CONFIRM_SALT, max_age=CONFIRM_MAX_AGE)
    except signing.BadSignature:
        return None


def make_unsubscribe_token(sub_id) -> str:
    return signing.dumps(str(sub_id), salt=UNSUB_SALT)


def read_unsubscribe_token(token: str) -> str | None:
    try:
        return signing.loads(token, salt=UNSUB_SALT)
    except signing.BadSignature:
        return None
