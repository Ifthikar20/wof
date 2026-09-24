from django.core.management.base import BaseCommand, CommandError

from apps.audit.services import head_hash, verify_chain


class Command(BaseCommand):
    help = "Verify the integrity of the hash-chained audit log."

    def handle(self, *args, **options):
        ok, bad_id = verify_chain()
        if not ok:
            raise CommandError(f"Audit chain broken at entry {bad_id}")
        self.stdout.write(self.style.SUCCESS(f"Audit chain intact. head={head_hash()}"))
