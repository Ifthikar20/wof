import math
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.audit.models import ImmutableRecordError
from apps.common.hashing import canonical_json, sha256_hex


class Media(models.Model):
    """An uploaded image. Raw bytes stay in the private bucket; only re-encoded,
    EXIF-stripped, watermarked variants are published to the CDN bucket."""

    class Status(models.TextChoices):
        PENDING = "pending", "Awaiting upload"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="media"
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    declared_type = models.CharField(max_length=32)
    original_key = models.CharField(max_length=255)
    display_key = models.CharField(max_length=255, blank=True)
    thumb_key = models.CharField(max_length=255, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    dominant_color = models.CharField(max_length=7, blank=True)  # masonry placeholder
    rejection_reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_ready(self) -> bool:
        return self.status == self.Status.READY

    @property
    def display_url(self) -> str | None:
        return f"{settings.MEDIA_CDN_URL}/{self.display_key}" if self.display_key else None

    @property
    def thumb_url(self) -> str | None:
        return f"{settings.MEDIA_CDN_URL}/{self.thumb_key}" if self.thumb_key else None


class Tag(models.Model):
    name = models.CharField(max_length=40, unique=True)
    slug = models.SlugField(max_length=40, unique=True)

    def __str__(self) -> str:
        return self.name


class Story(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        HIDDEN = "hidden", "Hidden by moderator"
        REMOVED = "removed", "Removed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stories"
    )
    slug = models.SlugField(max_length=120, unique=True)
    title = models.CharField(max_length=140)
    dek = models.CharField("subtitle", max_length=280, blank=True)
    body_markdown = models.TextField(max_length=60_000)
    body_html = models.TextField(blank=True)  # sanitised render cache, never user-supplied
    cover = models.ForeignKey(
        Media, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="stories")
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True
    )

    revision_number = models.PositiveIntegerField(default=0)
    content_hash = models.CharField(max_length=64, blank=True)
    reading_minutes = models.PositiveSmallIntegerField(default=1)

    like_count = models.PositiveIntegerField(default=0)
    save_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    featured_at = models.DateTimeField(null=True, blank=True)  # editor's pick for the digest

    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "stories"
        indexes = [models.Index(fields=["status", "-published_at"])]

    def __str__(self) -> str:
        return self.title

    @property
    def is_public(self) -> bool:
        return self.status == self.Status.PUBLISHED

    def content_payload(self) -> dict:
        return {"title": self.title, "dek": self.dek, "body_markdown": self.body_markdown}

    def compute_content_hash(self) -> str:
        return sha256_hex(canonical_json(self.content_payload()))

    def update_reading_time(self) -> None:
        words = len(self.body_markdown.split())
        self.reading_minutes = max(1, math.ceil(words / 230))

    def publish(self) -> None:
        self.status = self.Status.PUBLISHED
        self.published_at = self.published_at or timezone.now()


class StoryRevision(models.Model):
    """Immutable snapshot of every saved version of a story, forming a per-story hash chain.
    Lets anyone (moderators, the author, the public via content_hash) prove what was
    published and when, and lets us detect any out-of-band edit to the stories table."""

    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name="revisions")
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=140)
    dek = models.CharField(max_length=280, blank=True)
    body_markdown = models.TextField()
    content_hash = models.CharField(max_length=64)
    prev_hash = models.CharField(max_length=64, blank=True)
    chain_hash = models.CharField(max_length=64)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["story", "number"]
        constraints = [
            models.UniqueConstraint(fields=["story", "number"], name="unique_story_revision")
        ]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ImmutableRecordError("Story revisions are immutable")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ImmutableRecordError("Story revisions cannot be deleted")
