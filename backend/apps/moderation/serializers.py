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
        ]


class HeldCommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.handle")
    story = serializers.CharField(source="story.slug")

    class Meta:
        model = Comment
        fields = ["id", "author", "story", "body", "spam_flags", "created_at"]
