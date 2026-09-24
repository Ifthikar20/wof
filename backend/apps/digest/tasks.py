from celery import shared_task
from django.utils import timezone

from . import services
from .models import DigestIssue


@shared_task
def build_weekly_digest() -> int | None:
    issue = services.build_issue()
    return issue.number if issue else None


@shared_task
def send_scheduled_issues() -> int:
    due = DigestIssue.objects.filter(
        status=DigestIssue.Status.SCHEDULED, send_at__lte=timezone.now()
    )
    for issue in due:
        send_issue_task.delay(issue.pk)
    return len(due)


@shared_task(acks_late=True)
def send_issue_task(issue_id: int) -> int:
    return services.send_issue(issue_id)
