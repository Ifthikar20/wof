from django.db import transaction
from django.db.models import F

from apps.accounts.models import User
from apps.audit import services as audit
from apps.engagement.models import Comment, Report
from apps.stories.models import Story

from .models import ModerationAction

A = ModerationAction.Action


class ModerationError(Exception):
    pass


@transaction.atomic
def apply(
    actor, action: str, target_id: str, reason: str, report: Report | None = None, request=None
) -> ModerationAction:
    if not reason.strip():
        raise ModerationError("A reason is required for every moderation action.")

    if action in (A.HIDE_STORY, A.RESTORE_STORY, A.REMOVE_STORY):
        story = Story.objects.select_for_update().get(pk=target_id)
        story.status = {
            A.HIDE_STORY: Story.Status.HIDDEN,
            A.RESTORE_STORY: Story.Status.PUBLISHED,
            A.REMOVE_STORY: Story.Status.REMOVED,
        }[action]
        story.save(update_fields=["status", "updated_at"])
        target_type = "story"
    elif action in (A.HIDE_COMMENT, A.APPROVE_COMMENT):
        comment = Comment.objects.select_for_update().get(pk=target_id)
        was_visible = comment.status == Comment.Status.VISIBLE
        hide = action == A.HIDE_COMMENT
        comment.status = Comment.Status.HIDDEN if hide else Comment.Status.VISIBLE
        comment.save(update_fields=["status"])
        delta = (comment.status == Comment.Status.VISIBLE) - was_visible
        if delta:
            Story.objects.filter(pk=comment.story_id).update(
                comment_count=F("comment_count") + delta
            )
        target_type = "comment"
    elif action in (A.SUSPEND_USER, A.UNSUSPEND_USER):
        user = User.objects.select_for_update().get(pk=target_id)
        if user.pk == actor.pk:
            raise ModerationError("You cannot suspend yourself.")
        user.is_suspended = action == A.SUSPEND_USER
        user.save(update_fields=["is_suspended"])
        target_type = "user"
    elif action == A.DISMISS_REPORT:
        if report is None:
            raise ModerationError("dismiss_report needs a report.")
        target_type = "report"
    else:
        raise ModerationError("Unknown action.")

    if report is not None:
        report.status = (
            Report.Status.DISMISSED if action == A.DISMISS_REPORT else Report.Status.ACTIONED
        )
        report.save(update_fields=["status"])

    entry = ModerationAction.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        report=report,
        reason=reason[:500],
    )
    audit.record(
        f"moderation.{action}",
        actor=actor,
        target_type=target_type,
        target_id=str(target_id),
        request=request,
        metadata={"reason": reason[:200]},
    )
    return entry
