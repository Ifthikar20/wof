"""
Object storage for uploads and processed media.

Two backends behind one interface:

* **S3-compatible** (AWS S3, Cloudflare R2, MinIO): the browser uploads straight to the
  private bucket with a presigned POST; processed variants go to the public bucket behind
  the CDN. Used by docker compose and production.
* **Local filesystem** (``LOCAL_MEDIA_ROOT`` set; DEBUG only): the same contract, with a
  signed upload token standing in for the S3 policy signature and a dev-only view serving
  the processed files. Lets the whole app run with no Docker and no object store.
"""

import re
from functools import lru_cache
from pathlib import Path

import boto3
from botocore.config import Config
from django.conf import settings
from django.core import signing

UPLOAD_TOKEN_SALT = "wof.local-upload"  # noqa: S105 - a signing salt, not a secret
UPLOAD_TOKEN_MAX_AGE = 300
_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9/._-]{0,200}$")


def is_local() -> bool:
    return bool(getattr(settings, "LOCAL_MEDIA_ROOT", ""))


def safe_key(key: str) -> str:
    """Reject anything that could escape the storage root (used by the local backend)."""
    if not _KEY_RE.match(key) or ".." in key or "//" in key:
        raise ValueError("invalid storage key")
    return key


# ---- S3 backend ---------------------------------------------------------------------------


@lru_cache(maxsize=2)
def _client(public: bool = False):
    return boto3.client(
        "s3",
        endpoint_url=(settings.S3_PUBLIC_ENDPOINT_URL if public else settings.S3_ENDPOINT_URL)
        or None,
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID or None,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY or None,
        config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
    )


def _s3_presigned_upload(key: str, content_type: str) -> dict:
    """Presigned POST: the browser uploads straight to the *private* bucket. The policy
    pins the exact key, content type and a max size, and expires in 5 minutes."""
    return _client(public=True).generate_presigned_post(
        Bucket=settings.S3_PRIVATE_BUCKET,
        Key=key,
        Fields={"Content-Type": content_type},
        Conditions=[
            {"Content-Type": content_type},
            ["content-length-range", 1, settings.UPLOAD_MAX_BYTES],
        ],
        ExpiresIn=300,
    )


def _s3_read_private(key: str) -> bytes:
    obj = _client().get_object(Bucket=settings.S3_PRIVATE_BUCKET, Key=key)
    if obj["ContentLength"] > settings.UPLOAD_MAX_BYTES:
        raise ValueError("object too large")
    return obj["Body"].read(settings.UPLOAD_MAX_BYTES + 1)


def _s3_write_public(key: str, data: bytes, content_type: str) -> None:
    _client().put_object(
        Bucket=settings.S3_PUBLIC_BUCKET,
        Key=key,
        Body=data,
        ContentType=content_type,
        CacheControl="public, max-age=31536000, immutable",
    )


def _s3_delete(key: str, public: bool) -> None:
    bucket = settings.S3_PUBLIC_BUCKET if public else settings.S3_PRIVATE_BUCKET
    _client().delete_object(Bucket=bucket, Key=key)


# ---- Local filesystem backend (DEBUG only) ------------------------------------------------


def _local_path(key: str, public: bool) -> Path:
    root = Path(settings.LOCAL_MEDIA_ROOT).resolve() / ("public" if public else "private")
    path = (root / safe_key(key)).resolve()
    if root not in path.parents:
        raise ValueError("invalid storage key")
    return path


def make_upload_token(key: str, content_type: str) -> str:
    return signing.dumps({"key": key, "ct": content_type}, salt=UPLOAD_TOKEN_SALT)


def read_upload_token(token: str) -> dict | None:
    try:
        return signing.loads(token, salt=UPLOAD_TOKEN_SALT, max_age=UPLOAD_TOKEN_MAX_AGE)
    except signing.BadSignature:
        return None


def _local_presigned_upload(key: str, content_type: str) -> dict:
    """Same shape as S3's presigned POST, authorised by a signed, expiring token that pins
    the key and content type (the token is the policy; no cookie or CSRF involved)."""
    return {
        "url": f"{settings.SITE_URL}/api/v1/media/local-upload",
        "fields": {"token": make_upload_token(key, content_type), "Content-Type": content_type},
    }


def local_store_upload(key: str, content_type: str, chunks) -> None:
    path = _local_path(key, public=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(path, "wb") as fh:
        for chunk in chunks:
            written += len(chunk)
            if written > settings.UPLOAD_MAX_BYTES:
                fh.close()
                path.unlink(missing_ok=True)
                raise ValueError("object too large")
            fh.write(chunk)
    if written == 0:
        path.unlink(missing_ok=True)
        raise ValueError("empty upload")
    del content_type  # recorded on the Media row; the file itself is sniffed by the worker


def _local_read_private(key: str) -> bytes:
    path = _local_path(key, public=False)
    if path.stat().st_size > settings.UPLOAD_MAX_BYTES:
        raise ValueError("object too large")
    return path.read_bytes()


def _local_write_public(key: str, data: bytes, content_type: str) -> None:
    del content_type  # served by extension (.webp) from the dev view
    path = _local_path(key, public=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _local_delete(key: str, public: bool) -> None:
    _local_path(key, public).unlink(missing_ok=True)


# ---- Public interface ---------------------------------------------------------------------


def presigned_upload(key: str, content_type: str) -> dict:
    fn = _local_presigned_upload if is_local() else _s3_presigned_upload
    return fn(key, content_type)


def read_private(key: str) -> bytes:
    return (_local_read_private if is_local() else _s3_read_private)(key)


def write_public(key: str, data: bytes, content_type: str) -> None:
    (_local_write_public if is_local() else _s3_write_public)(key, data, content_type)


def delete_private(key: str) -> None:
    delete_object(key, public=False)


def delete_object(key: str, public: bool) -> None:
    (_local_delete if is_local() else _s3_delete)(key, public)
