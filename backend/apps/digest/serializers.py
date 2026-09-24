from rest_framework import serializers

from apps.stories.serializers import StoryCardSerializer

from .models import DigestIssue


class SubscribeSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    turnstile_token = serializers.CharField(required=False, allow_blank=True)


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=512)


class IssueSerializer(serializers.ModelSerializer):
    stories = serializers.SerializerMethodField()

    class Meta:
        model = DigestIssue
        fields = ["number", "subject", "intro", "week_of", "sent_at", "stories"]

    def get_stories(self, obj):
        items = obj.items.select_related("story__author", "story__cover").filter(
            story__status="published"
        )
        return StoryCardSerializer([i.story for i in items], many=True).data
