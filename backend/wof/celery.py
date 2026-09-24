import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wof.settings.dev")

app = Celery("wof")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Build next week's draft digest every Sunday 12:00 UTC; editors review it in admin.
    "digest-build-weekly": {
        "task": "apps.digest.tasks.build_weekly_digest",
        "schedule": crontab(hour=12, minute=0, day_of_week="sun"),
    },
    # Send any issue an editor has approved and scheduled.
    "digest-send-scheduled": {
        "task": "apps.digest.tasks.send_scheduled_issues",
        "schedule": crontab(minute="*/15"),
    },
    # Expire founder verifications older than 12 months.
    "verification-expire": {
        "task": "apps.verification.tasks.expire_verifications",
        "schedule": crontab(hour=3, minute=0),
    },
    # Recompute the audit chain and alert on any break.
    "audit-verify-chain": {
        "task": "apps.audit.tasks.verify_chain_task",
        "schedule": crontab(hour=4, minute=0),
    },
}
