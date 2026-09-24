import logging
from datetime import timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.template.loader import render_to_string
from django.utils import timezone

from apps.audit import services as audit
from apps.common.tasks import send_email_task

from . import curation, tokens
from .models import DigestDelivery, DigestIssue, DigestItem, Subscription

logger = logging.getLogger(__name__)
RESEND_COOLDOWN = timedelta(minutes=10)
BATCH_SIZE = 500


def subscribe(email: str, user=None) -> None:
    """Double opt-in. Always behaves identically for new/existing emails (no enumeration)."""
    email = email.strip().lower()
    sub, _ = Subscription.objects.get_or_create(email=email, defaults={"user": user})
    if sub.status == Subscription.Status.ACTIVE or sub.status == Subscription.Status.BOUNCED:
        return
    now = timezone.now()
    if sub.confirmation_sent_at and now - sub.confirmation_sent_at < RESEND_COOLDOWN:
        return  # stops the endpoint being used to mail-bomb someone
    sub.status = Subscription.Status.PENDING
    sub.confirmation_sent_at = now
    sub.save(update_fields=["status", "confirmation_sent_at"])
    link = f"{settings.SITE_URL}/digest/confirm?token={tokens.make_confirm_token(sub.id)}"
    send_email_task.delay(
        subject="Confirm your Wall of Founders digest subscription",
        body=f"Tap to start receiving one founder-story digest a week:\n{link}\n\n"
        "Didn't ask for this? Ignore this email and you won't hear from us.",
        to=email,
        from_email=settings.DIGEST_FROM_EMAIL,
    )


def confirm(token: str) -> bool:
    sub_id = tokens.read_confirm_token(token)
    if not sub_id:
        return False
    updated = Subscription.objects.filter(pk=sub_id, status=Subscription.Status.PENDING).update(
        status=Subscription.Status.ACTIVE, confirmed_at=timezone.now()
    )
    return (
        bool(updated)
        or Subscription.objects.filter(pk=sub_id, status=Subscription.Status.ACTIVE).exists()
    )


def unsubscribe(token: str) -> bool:
    sub_id = tokens.read_unsubscribe_token(token)
    if not sub_id:
        return False
    Subscription.objects.filter(pk=sub_id).update(
        status=Subscription.Status.UNSUBSCRIBED, unsubscribed_at=timezone.now()
    )
    return True


@transaction.atomic
def build_issue(now=None) -> DigestIssue | None:
    now = now or timezone.now()
    selected = curation.select_stories(now)
    if len(selected) < curation.MIN_ITEMS:
        logger.info("digest: only %s eligible stories, skipping", len(selected))
        return None
    number = (DigestIssue.objects.aggregate(n=Max("number"))["n"] or 0) + 1
    lead = selected[0][0]
    issue = DigestIssue.objects.create(
        number=number,
        subject=f"This week on the Wall: {lead.title}"[:140],
        week_of=now.date(),
    )
    DigestItem.objects.bulk_create(
        [
            DigestItem(issue=issue, story=story, position=i, editor_pick=pick)
            for i, (story, pick) in enumerate(selected)
        ]
    )
    audit.record("digest.drafted", target=issue, metadata={"stories": len(selected)})
    return issue


def render_issue(issue: DigestIssue, sub: Subscription) -> tuple[str, str, str]:
    token = tokens.make_unsubscribe_token(sub.id)
    one_click = f"{settings.SITE_URL}/api/v1/digest/unsubscribe?token={token}"  # RFC 8058 POST
    footer = f"{settings.SITE_URL}/digest/unsubscribe?token={token}"  # human-facing page
    ctx = {
        "issue": issue,
        "items": issue.items.select_related(
            "story__author__founder_profile__company", "story__cover"
        ),
        "site_url": settings.SITE_URL,
        "unsubscribe_url": footer,
    }
    return (
        render_to_string("digest/issue.txt", ctx),
        render_to_string("digest/issue.html", ctx),
        one_click,
    )


def send_issue(issue_id: int) -> int:
    issue = DigestIssue.objects.get(pk=issue_id)
    if issue.status not in (DigestIssue.Status.SCHEDULED, DigestIssue.Status.SENDING):
        return 0
    DigestIssue.objects.filter(pk=issue.pk).update(status=DigestIssue.Status.SENDING)
    sent = 0
    already = DigestDelivery.objects.filter(issue=issue).values("subscription_id")
    pending = (
        Subscription.objects.filter(status=Subscription.Status.ACTIVE)
        .exclude(pk__in=already)
        .order_by("id")
    )
    connection = get_connection()
    for sub in pending.iterator(chunk_size=BATCH_SIZE):
        try:
            DigestDelivery.objects.create(issue=issue, subscription=sub)  # claim first
        except IntegrityError:
            continue  # another worker already sent this one
        text, html, unsub = render_issue(issue, sub)
        msg = EmailMultiAlternatives(
            subject=issue.subject,
            body=text,
            from_email=settings.DIGEST_FROM_EMAIL,
            to=[sub.email],
            connection=connection,
            headers={
                # RFC 8058 one-click unsubscribe (required by Gmail/Yahoo bulk-sender rules).
                "List-Unsubscribe": f"<{unsub}>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
                "List-Id": "Wall of Founders Digest <digest.walloffounders>",
                **(
                    {"X-PM-Message-Stream": settings.DIGEST_MESSAGE_STREAM}
                    if settings.DIGEST_MESSAGE_STREAM
                    else {}
                ),
            },
        )
        msg.attach_alternative(html, "text/html")
        msg.send()
        sent += 1
    DigestIssue.objects.filter(pk=issue.pk).update(
        status=DigestIssue.Status.SENT, sent_at=timezone.now()
    )
    audit.record("digest.sent", target=issue, metadata={"recipients": sent})
    return sent
