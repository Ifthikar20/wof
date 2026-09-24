from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task(bind=True, max_retries=5, default_retry_delay=60, acks_late=True)
def send_email_task(self, subject: str, body: str, to: str, from_email: str | None = None):
    """Transactional email off the request path: SMTP/provider outages retry with backoff
    instead of surfacing as 500s, and response timing no longer depends on the mail server."""
    try:
        send_mail(subject, body, from_email or settings.DEFAULT_FROM_EMAIL, [to])
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * 2**self.request.retries) from exc
