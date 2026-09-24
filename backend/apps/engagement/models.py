import uuid

from django.conf import settings
from django.db import models

from apps.stories.models import Story


class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="likes"
    )
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "story"], name="unique_like")]


class Board(models.Model):
    """A Pinterest-style collection of saved stories."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="boards"
    )
    name = models.CharField(max_length=60)
    description = models.CharField(max_length=280, blank=True)
    is_private = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["owner", "name"], name="unique_board_name")]


class Save(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name="saves")
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="saves")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["board", "story"], name="unique_save")]


class Comment(models.Model):
    class Status(models.TextChoices):
        VISIBLE = "visible", "Visible"
        PENDING = "pending", "Held for review"
        HIDDEN = "hidden", "Hidden by moderator"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    body = models.TextField(max_length=2000)  # plain text; rendered escaped by the frontend
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.VISIBLE, db_index=True
    )
    spam_flags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following"
    )
    founder = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "founder"], name="unique_follow"),
            models.CheckConstraint(
                condition=~models.Q(follower=models.F("founder")), name="no_self_follow"
            ),
        ]


class Report(models.Model):
    class Target(models.TextChoices):
        STORY = "story", "Story"
        COMMENT = "comment", "Comment"
        USER = "user", "User"

    class Reason(models.TextChoices):
        SPAM = "spam", "Spam or advertising"
        FALSE_CLAIM = "false_claim", "False founder claim / impersonation"
        PLAGIARISM = "plagiarism", "Plagiarism / not their story"
        HARASSMENT = "harassment", "Harassment or hate"
        MISINFORMATION = "misinformation", "Misleading or false facts"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACTIONED = "actioned", "Actioned"
        DISMISSED = "dismissed", "Dismissed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="reports_filed"
    )
    target_type = models.CharField(max_length=16, choices=Target.choices)
    target_id = models.CharField(max_length=64)
    reason = models.CharField(max_length=24, choices=Reason.choices)
    details = models.CharField(max_length=1000, blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.OPEN, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["reporter", "target_type", "target_id"],
                condition=models.Q(status="open"),
                name="one_open_report_per_target_per_user",
            )
        ]
