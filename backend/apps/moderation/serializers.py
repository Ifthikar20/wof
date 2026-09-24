from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.engagement.models import Comment, Report

from .models import ModerationAction


class ActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=ModerationAction.Action.choices)
    target_id = serializers.CharField(max_length=64)
    reason = serializers.CharField(max_length=500)
    report_id = serializers.UUIDField(required=False)


class ModReportSerializer(serializers.ModelSerializer):
    reporter = serializers.CharField(source="reporter.handle", default=None)

    class Meta:
        model = Report
        fields = [
            "id",
            "reporter",
            "target_type",
            "target_id",
            "reason",
            "details",
            "status",
            "created_at",
            "target",
        ]

    target = serializers.SerializerMethodField()

    def get_target(self, obj):
        """Human-readable summary of what was reported, so moderators needn't look up IDs."""
        from apps.accounts.models import User
        from apps.stories.models import Story

        try:
            if obj.target_type == Report.Target.STORY:
                story = Story.objects.select_related("author").get(pk=obj.target_id)
                return {
                    "label": story.title,
                    "url": f"/s/{story.slug}",
                    "status": story.status,
                    "author": story.author.handle,
                }
            if obj.target_type == Report.Target.COMMENT:
                comment = Comment.objects.select_related("author", "story").get(pk=obj.target_id)
                return {
                    "label": comment.body[:140],
                    "url": f"/s/{comment.story.slug}",
                    "status": comment.status,
                    "author": comment.author.handle,
                }
            if obj.target_type == Report.Target.USER:
                user = User.objects.get(pk=obj.target_id)
                return {
                    "label": f"@{user.handle}",
                    "url": f"/f/{user.handle}",
                    "status": "suspended" if user.is_suspended else "active",
                    "author": user.handle,
                }
        except (ObjectDoesNotExist, ValueError, DjangoValidationError):
            pass
        return {"label": "(no longer exists)", "url": None, "status": "missing", "author": None}


class HeldCommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.handle")
    story = serializers.CharField(source="story.slug")

    class Meta:
        model = Comment
        fields = ["id", "author", "story", "body", "spam_flags", "created_at"]
