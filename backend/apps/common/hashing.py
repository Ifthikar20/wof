import hashlib
import json
import secrets


def sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode()
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False)


def new_token() -> tuple[str, str]:
    """Return (raw_token, sha256_hash). Only the hash is ever persisted."""
    raw = secrets.token_urlsafe(32)
    return raw, sha256_hex(raw)
