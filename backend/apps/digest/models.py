import uuid

from django.conf import settings
from django.db import models

from apps.stories.models import Story


class Subscription(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Awaiting confirmation"
        ACTIVE = "active", "Active"
        UNSUBSCRIBED = "unsubscribed", "Unsubscribed"
        BOUNCED = "bounced", "Hard-bounced / complained"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="subscriptions",
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    confirmation_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class DigestIssue(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft (editor review)"
        SCHEDULED = "scheduled", "Approved & scheduled"
        SENDING = "sending", "Sending"
        SENT = "sent", "Sent"

    number = models.PositiveIntegerField(unique=True)
    subject = models.CharField(max_length=140)
    intro = models.TextField(blank=True, max_length=2000)
    week_of = models.DateField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    send_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    stories = models.ManyToManyField(Story, through="DigestItem", related_name="digest_issues")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-number"]

    def __str__(self) -> str:
        return f"#{self.number} {self.subject}"


class DigestItem(models.Model):
    issue = models.ForeignKey(DigestIssue, on_delete=models.CASCADE, related_name="items")
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField()
    editor_pick = models.BooleanField(default=False)

    class Meta:
        ordering = ["position"]
        constraints = [models.UniqueConstraint(fields=["issue", "story"], name="unique_item")]


class DigestDelivery(models.Model):
    """One row per (issue, subscriber): makes sending idempotent across retries/crashes."""

    issue = models.ForeignKey(DigestIssue, on_delete=models.CASCADE, related_name="deliveries")
    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="deliveries"
    )
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["issue", "subscription"], name="unique_delivery")
        ]
