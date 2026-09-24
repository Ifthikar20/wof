from django.db import connection, transaction
from django.utils import timezone

from apps.common.net import client_ip, user_agent

from .models import GENESIS_HASH, AuditLog

# Arbitrary constant used as the Postgres advisory-lock key that serialises chain appends.
_CHAIN_LOCK_KEY = 0x574F46  # "WOF"


def _lock_chain() -> None:
    if connection.vendor == "postgresql":
        with connection.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(%s)", [_CHAIN_LOCK_KEY])


def record(
    action: str,
    *,
    actor=None,
    target=None,
    target_type: str = "",
    target_id: str = "",
    metadata: dict | None = None,
    request=None,
) -> AuditLog:
    """Append an entry to the audit chain. Call inside the same transaction as the change."""
    if target is not None:
        target_type = target_type or target._meta.label_lower
        target_id = target_id or str(target.pk)
    if actor is None and request is not None and request.user.is_authenticated:
        actor = request.user
    with transaction.atomic():
        _lock_chain()
        last = AuditLog.objects.order_by("-id").only("hash").first()
        entry = AuditLog(
            actor=actor,
            actor_label=getattr(actor, "email", "") if actor else "system",
            action=action,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata or {},
            ip=client_ip(request) or None if request is not None else None,
            user_agent=user_agent(request) if request is not None else "",
            created_at=timezone.now(),
            prev_hash=last.hash if last else GENESIS_HASH,
        )
        entry.hash = entry.compute_hash()
        entry.save()
        return entry


def verify_chain() -> tuple[bool, int | None]:
    """Walk the whole chain. Returns (ok, id_of_first_bad_entry)."""
    expected_prev = GENESIS_HASH
    for entry in AuditLog.objects.order_by("id").iterator(chunk_size=2000):
        if entry.prev_hash != expected_prev or entry.compute_hash() != entry.hash:
            return False, entry.id
        expected_prev = entry.hash
    return True, None


def head_hash() -> str:
    last = AuditLog.objects.order_by("-id").only("hash").first()
    return last.hash if last else GENESIS_HASH
