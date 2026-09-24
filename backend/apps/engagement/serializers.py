from rest_framework import serializers

from apps.stories.serializers import StoryCardSerializer

from .models import Board, Comment, Report


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ["id", "author", "body", "status", "created_at"]
        read_only_fields = ["id", "author", "status", "created_at"]

    def get_author(self, obj):
        return {
            "handle": obj.author.handle,
            "display_name": obj.author.display_name,
            "is_verified_founder": obj.author.is_verified_founder,
        }

    def validate_body(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Comment cannot be empty.")
        return value


class BoardSerializer(serializers.ModelSerializer):
    save_count = serializers.IntegerField(source="saves.count", read_only=True)

    class Meta:
        model = Board
        fields = ["id", "name", "description", "is_private", "save_count", "created_at"]
        read_only_fields = ["id", "save_count", "created_at"]


class BoardDetailSerializer(BoardSerializer):
    stories = serializers.SerializerMethodField()

    class Meta(BoardSerializer.Meta):
        fields = BoardSerializer.Meta.fields + ["stories"]

    def get_stories(self, obj):
        saves = (
            obj.saves.select_related("story__author", "story__cover")
            .filter(story__status="published")
            .order_by("-created_at")[:100]
        )
        return StoryCardSerializer([s.story for s in saves], many=True).data


class SaveSerializer(serializers.Serializer):
    story = serializers.SlugField()


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["id", "target_type", "target_id", "reason", "details", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at"]
