import logging

from celery import shared_task

from . import imaging, storage
from .models import Media

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_media(self, media_id: str) -> str:
    media = Media.objects.get(pk=media_id)
    if media.status not in (Media.Status.PROCESSING,):
        return media.status
    try:
        raw = storage.read_private(media.original_key)
        out = imaging.process(raw)
    except imaging.RejectedImage as exc:
        media.status = Media.Status.REJECTED
        media.rejection_reason = str(exc)
        media.save(update_fields=["status", "rejection_reason"])
        storage.delete_private(media.original_key)
        return media.status
    except Exception as exc:  # transient storage errors
        raise self.retry(exc=exc) from exc

    base = f"m/{media.id.hex}"
    storage.write_public(f"{base}/display.webp", out["display"], "image/webp")
    storage.write_public(f"{base}/thumb.webp", out["thumb"], "image/webp")
    media.display_key = f"{base}/display.webp"
    media.thumb_key = f"{base}/thumb.webp"
    media.width, media.height = out["width"], out["height"]
    media.dominant_color = out["dominant_color"]
    media.status = Media.Status.READY
    media.save()
    return media.status


@shared_task(bind=True, max_retries=5, default_retry_delay=300)
def delete_media_objects(self, keys: list[str]) -> int:
    """Erase a deleted account's uploads from both buckets (best effort, retried)."""
    from django.conf import settings

    from .storage import _client

    removed = 0
    for key in keys:
        bucket = settings.S3_PUBLIC_BUCKET if key.startswith("m/") else settings.S3_PRIVATE_BUCKET
        try:
            _client().delete_object(Bucket=bucket, Key=key)
            removed += 1
        except Exception as exc:
            logger.warning("media delete failed for %s", key)
            raise self.retry(exc=exc) from exc
    return removed
