import uuid

from django.conf import settings
from django.db import models


class ModerationAction(models.Model):
    class Action(models.TextChoices):
        HIDE_STORY = "hide_story", "Hide story"
        RESTORE_STORY = "restore_story", "Restore story"
        REMOVE_STORY = "remove_story", "Remove story"
        HIDE_COMMENT = "hide_comment", "Hide comment"
        APPROVE_COMMENT = "approve_comment", "Approve held comment"
        SUSPEND_USER = "suspend_user", "Suspend user"
        UNSUSPEND_USER = "unsuspend_user", "Unsuspend user"
        DISMISS_REPORT = "dismiss_report", "Dismiss report"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="moderation_actions"
    )
    action = models.CharField(max_length=24, choices=Action.choices)
    target_type = models.CharField(max_length=16)
    target_id = models.CharField(max_length=64)
    report = models.ForeignKey(
        "engagement.Report",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="actions",
    )
    reason = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
