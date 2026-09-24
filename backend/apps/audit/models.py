"""
Append-only, hash-chained audit log.

Every row stores hash = SHA256(prev_hash || canonical(row fields)). Changing or deleting
any historical row breaks every hash after it, which `verify_chain()` detects. On
PostgreSQL a trigger (see migration 0002) additionally rejects UPDATE/DELETE outright,
and in production the application DB role is only GRANTed INSERT/SELECT on this table.
The daily head hash is also exported off-site so even a DB superuser rewrite is caught.
"""

from django.conf import settings
from django.db import models

from apps.common.hashing import canonical_json, sha256_hex

GENESIS_HASH = "0" * 64


class ImmutableRecordError(RuntimeError):
    pass


class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        db_constraint=False,
    )
    actor_label = models.CharField(max_length=320, blank=True)  # survives user deletion
    action = models.CharField(max_length=64, db_index=True)
    target_type = models.CharField(max_length=64, blank=True)
    target_id = models.CharField(max_length=64, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=256, blank=True)
    created_at = models.DateTimeField(db_index=True)
    prev_hash = models.CharField(max_length=64)
    hash = models.CharField(max_length=64, unique=True)

    class Meta:
        ordering = ["id"]

    def compute_hash(self) -> str:
        payload = {
            "actor_id": str(self.actor_id) if self.actor_id else None,
            "actor_label": self.actor_label,
            "action": self.action,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "metadata": self.metadata,
            "ip": self.ip,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat(),
        }
        return sha256_hex(self.prev_hash + canonical_json(payload))

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ImmutableRecordError("Audit log entries are append-only")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ImmutableRecordError("Audit log entries cannot be deleted")

    def __str__(self) -> str:
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.action} {self.target_type}:{self.target_id}"
