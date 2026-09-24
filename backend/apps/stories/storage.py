"""Thin wrapper over S3-compatible object storage (AWS S3, Cloudflare R2, MinIO)."""

from functools import lru_cache

import boto3
from botocore.config import Config
from django.conf import settings


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


def presigned_upload(key: str, content_type: str) -> dict:
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


def read_private(key: str) -> bytes:
    obj = _client().get_object(Bucket=settings.S3_PRIVATE_BUCKET, Key=key)
    if obj["ContentLength"] > settings.UPLOAD_MAX_BYTES:
        raise ValueError("object too large")
    return obj["Body"].read(settings.UPLOAD_MAX_BYTES + 1)


def write_public(key: str, data: bytes, content_type: str) -> None:
    _client().put_object(
        Bucket=settings.S3_PUBLIC_BUCKET,
        Key=key,
        Body=data,
        ContentType=content_type,
        CacheControl="public, max-age=31536000, immutable",
    )


def delete_private(key: str) -> None:
    _client().delete_object(Bucket=settings.S3_PRIVATE_BUCKET, Key=key)
