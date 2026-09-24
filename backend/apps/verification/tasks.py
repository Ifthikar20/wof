from celery import shared_task

from .services import expire_due


@shared_task
def expire_verifications() -> int:
    return expire_due()
