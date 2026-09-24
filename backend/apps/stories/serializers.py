from rest_framework import serializers

from .models import Media, Story, StoryRevision, Tag


class CoverSerializer(serializers.ModelSerializer):
    url = serializers.CharField(source="display_url")
    thumb_url = serializers.CharField()

    class Meta:
        model = Media
        fields = ["url", "thumb_url", "width", "height", "dominant_color"]


class AuthorSerializer(serializers.Serializer):
    handle = serializers.CharField()
    display_name = serializers.CharField()
    is_verified_founder = serializers.BooleanField()
    company = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()

    def _profile(self, obj):
        return getattr(obj, "founder_profile", None)

    def get_company(self, obj):
        p = self._profile(obj)
        return p.company.name if p and p.is_currently_verified else None

    def get_title(self, obj):
        p = self._profile(obj)
        return p.title if p and p.is_currently_verified else None


class StoryCardSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    cover = serializers.SerializerMethodField()
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field="slug")

    class Meta:
        model = Story
        fields = [
            "slug",
            "title",
            "dek",
            "cover",
            "author",
            "tags",
            "reading_minutes",
            "like_count",
            "save_count",
            "comment_count",
            "published_at",
        ]

    def get_cover(self, obj):
        if obj.cover_id and obj.cover.is_ready:
            return CoverSerializer(obj.cover).data
        return None


class StoryDetailSerializer(StoryCardSerializer):
    viewer = serializers.SerializerMethodField()

    class Meta(StoryCardSerializer.Meta):
        fields = StoryCardSerializer.Meta.fields + [
            "body_html",
            "status",
            "revision_number",
            "content_hash",
            "updated_at",
            "viewer",
        ]

    def to_representation(self, obj):
        data = super().to_representation(obj)
        viewer = data.get("viewer")
        if viewer and viewer["is_author"]:
            data["body_markdown"] = obj.body_markdown  # editor needs the source text
        return data

    def get_viewer(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            return None
        return {
            "liked": obj.likes.filter(user=user).exists(),
            "is_author": obj.author_id == user.pk,
        }


class StoryWriteSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.SlugField(max_length=40), max_length=5, required=False
    )
    cover_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Story
        fields = ["title", "dek", "body_markdown", "tags", "cover_id"]
        extra_kwargs = {"body_markdown": {"max_length": 60_000}}

    def validate_cover_id(self, value):
        if value is None:
            return None
        user = self.context["request"].user
        media = Media.objects.filter(pk=value, owner=user, status=Media.Status.READY).first()
        if media is None:
            raise serializers.ValidationError("Unknown or unprocessed image.")
        return media

    def validate_tags(self, value):
        return list(Tag.objects.filter(slug__in=value))

    def _apply(self, story, data):
        tags = data.pop("tags", None)
        if "cover_id" in data:
            story.cover = data.pop("cover_id")
        for key, val in data.items():
            setattr(story, key, val)
        return tags


class RevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryRevision
        fields = ["number", "content_hash", "chain_hash", "created_at"]


class UploadRequestSerializer(serializers.Serializer):
    content_type = serializers.ChoiceField(choices=["image/jpeg", "image/png", "image/webp"])


class MediaSerializer(serializers.ModelSerializer):
    url = serializers.CharField(source="display_url")
    thumb_url = serializers.CharField()

    class Meta:
        model = Media
        fields = ["id", "status", "url", "thumb_url", "width", "height", "rejection_reason"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["name", "slug"]
