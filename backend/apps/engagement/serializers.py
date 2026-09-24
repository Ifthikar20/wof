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
        fields = ["preview", "id", "name", "description", "is_private", "save_count", "created_at"]
        read_only_fields = ["id", "save_count", "created_at"]

    preview = serializers.SerializerMethodField()

    def get_preview(self, obj):
        """Up to 3 story slugs + thumbnails for the board's cover mosaic."""
        saves = obj.saves.select_related("story__cover").filter(story__status="published")
        return [
            {
                "slug": sv.story.slug,
                "thumb_url": sv.story.cover.thumb_url
                if sv.story.cover_id and sv.story.cover.is_ready
                else None,
            }
            for sv in saves.order_by("-created_at")[:3]
        ]


class BoardDetailSerializer(BoardSerializer):
    stories = serializers.SerializerMethodField()
    owner = serializers.CharField(source="owner.handle", read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta(BoardSerializer.Meta):
        fields = BoardSerializer.Meta.fields + ["stories", "owner", "is_owner"]

    def get_is_owner(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.owner_id == request.user.pk)

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
