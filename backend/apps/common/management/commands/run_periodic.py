"""
Run the scheduled (Celery beat) jobs once, synchronously. For local development without a
beat process, and for operators who want to trigger a cycle by hand.
"""

from django.core.management.base import BaseCommand

from apps.audit.tasks import verify_chain_task
from apps.digest.tasks import build_weekly_digest, send_scheduled_issues
from apps.verification.tasks import expire_verifications


class Command(BaseCommand):
    help = "Run every scheduled job once: verification expiry, digest build/send, audit check."

    def add_arguments(self, parser):
        parser.add_argument(
            "--only",
            choices=["expire", "digest-build", "digest-send", "audit"],
            help="Run a single job instead of all of them.",
        )

    def handle(self, *args, **options):
        jobs = {
            "expire": ("Expired founder verifications", expire_verifications),
            "digest-build": ("Drafted digest issue #", build_weekly_digest),
            "digest-send": ("Digest issues sent", send_scheduled_issues),
            "audit": ("Audit chain", verify_chain_task),
        }
        only = options.get("only")
        for key, (label, task) in jobs.items():
            if only and key != only:
                continue
            result = task()  # call directly: no broker needed
            self.stdout.write(f"{label}: {result}")
