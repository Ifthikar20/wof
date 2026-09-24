import json
import logging

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import AuditLog
from .services import head_hash, verify_chain

logger = logging.getLogger("wof.audit")


def anchor_head(head: str) -> str | None:
    """Write today's chain head to the write-once (object-lock) bucket. Once written it
    can't be changed or deleted for 7 years, so any later rewrite of history is provable."""
    bucket = settings.AUDIT_ANCHOR_BUCKET
    if not bucket:
        return None
    from apps.stories.storage import _client

    now = timezone.now()
    key = f"audit-head/{now:%Y/%m/%d}.json"
    body = json.dumps(
        {"head_hash": head, "entries": AuditLog.objects.count(), "at": now.isoformat()}
    )
    _client().put_object(Bucket=bucket, Key=key, Body=body.encode(), ContentType="application/json")
    return key


@shared_task
def verify_chain_task() -> dict:
    ok, bad_id = verify_chain()
    if not ok:
        # Matched by a CloudWatch metric filter that pages on-call (infra/terraform/monitoring.tf).
        logger.critical("AUDIT CHAIN BROKEN at entry %s", bad_id)
        return {"ok": False, "bad_id": bad_id}
    head = head_hash()
    key = anchor_head(head)
    logger.info("audit chain ok head=%s anchored=%s", head, key or "no (AUDIT_ANCHOR_BUCKET unset)")
    return {"ok": True, "bad_id": None, "anchored": key}
