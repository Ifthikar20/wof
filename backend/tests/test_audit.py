import pytest

from apps.audit import services
from apps.audit.models import AuditLog, ImmutableRecordError

from .conftest import bypass_append_only

pytestmark = pytest.mark.django_db


def test_chain_verifies_and_detects_tampering(reader):
    for i in range(5):
        services.record("test.event", target=reader, metadata={"i": i})
    assert services.verify_chain() == (True, None)

    victim = AuditLog.objects.order_by("id")[2]
    # Bypass the model guard (as a DB-level attacker would) and rewrite history.
    with bypass_append_only():
        AuditLog.objects.filter(pk=victim.pk).update(metadata={"i": 999})
    ok, bad = services.verify_chain()
    assert not ok and bad == victim.pk


def test_deleting_a_row_breaks_the_chain(reader):
    for i in range(3):
        services.record("test.event", target=reader, metadata={"i": i})
    middle = AuditLog.objects.order_by("id")[1]
    with bypass_append_only():
        AuditLog.objects.filter(pk=middle.pk).delete()
    assert services.verify_chain()[0] is False


def test_model_refuses_update_and_delete(reader):
    entry = services.record("test.event", target=reader)
    entry.action = "changed"
    with pytest.raises(ImmutableRecordError):
        entry.save()
    with pytest.raises(ImmutableRecordError):
        entry.delete()


def test_security_events_are_audited(client, reader):
    client.post("/api/v1/auth/login", {"email": reader.email, "password": "nope"}, format="json")
    assert AuditLog.objects.filter(action="auth.login_failed").exists()


def test_database_rejects_raw_updates_on_postgres(reader):
    from django.db import connection, transaction
    from django.db.utils import DatabaseError

    if connection.vendor != "postgresql":
        pytest.skip("append-only trigger is PostgreSQL-only")
    services.record("test.event", target=reader)
    with pytest.raises(DatabaseError), transaction.atomic():
        AuditLog.objects.update(action="rewritten")


def test_nightly_task_anchors_head_hash(reader, settings, monkeypatch):
    from apps.audit import tasks

    calls = []

    class FakeS3:
        def put_object(self, **kw):
            calls.append(kw)

    monkeypatch.setattr("apps.stories.storage._client", lambda public=False: FakeS3())
    settings.AUDIT_ANCHOR_BUCKET = "anchor-bucket"
    services.record("test.event", target=reader)
    result = tasks.verify_chain_task()
    assert result["ok"] and result["anchored"].startswith("audit-head/")
    assert calls[0]["Bucket"] == "anchor-bucket"
    assert services.head_hash() in calls[0]["Body"].decode()


def test_broken_chain_is_not_anchored(reader, settings, monkeypatch):
    from apps.audit import tasks

    settings.AUDIT_ANCHOR_BUCKET = "anchor-bucket"
    monkeypatch.setattr(
        "apps.stories.storage._client", lambda public=False: (_ for _ in ()).throw(AssertionError)
    )
    for i in range(2):
        services.record("test.event", target=reader, metadata={"i": i})
    with bypass_append_only():
        AuditLog.objects.filter(pk=AuditLog.objects.order_by("id").first().pk).update(action="x")
    assert tasks.verify_chain_task()["ok"] is False
