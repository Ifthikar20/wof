from django.db import transaction
from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.accounts.serializers import PublicUserSerializer
from apps.audit import services as audit
from apps.common.pagination import SmallCursorPagination
from apps.common.permissions import IsAuthorOrReadOnly, IsVerifiedFounder

from . import services, storage
from .models import Media, Story, Tag
from .serializers import (
    MediaSerializer,
    RevisionSerializer,
    StoryCardSerializer,
    StoryDetailSerializer,
    StoryWriteSerializer,
    TagSerializer,
    UploadRequestSerializer,
)
from .tasks import process_media


def public_stories():
    return (
        Story.objects.filter(status=Story.Status.PUBLISHED, author__is_suspended=False)
        .select_related("author", "author__founder_profile__company", "cover")
        .prefetch_related(Prefetch("tags", queryset=Tag.objects.only("slug")))
    )


class PublicCacheMixin:
    """Let the CDN cache anonymous reads briefly (absorbs scraping bursts cheaply)."""

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        anonymous = not request.user.is_authenticated
        if request.method == "GET" and anonymous and response.status_code == 200:
            response["Cache-Control"] = "public, max-age=30, s-maxage=60"
            response["Vary"] = "Cookie"
        return response


class FeedView(PublicCacheMixin, generics.ListCreateAPIView):
    """GET: the public wall (cursor-paginated). POST: verified founders create a draft."""

    throttle_scope = "feed"

    def get_permissions(self):
        return [AllowAny()] if self.request.method == "GET" else [IsVerifiedFounder()]

    def get_throttles(self):
        if self.request.method != "GET":
            self.throttle_scope = "write"
        return super().get_throttles()

    def get_serializer_class(self):
        return StoryCardSerializer if self.request.method == "GET" else StoryWriteSerializer

    def get_queryset(self):
        qs = public_stories()
        if tag := self.request.query_params.get("tag"):
            qs = qs.filter(tags__slug=tag[:40])
        if author := self.request.query_params.get("author"):
            qs = qs.filter(author__handle=author[:30])
        if q := self.request.query_params.get("q", "").strip()[:80]:
            # Simple substring search; same throttle + cursor pagination as the feed, so it
            # adds no cheaper way to enumerate the corpus. Tag match via subquery avoids
            # duplicate rows from the M2M join.
            tagged = Story.objects.filter(tags__name__icontains=q).values("pk")
            qs = qs.filter(Q(title__icontains=q) | Q(dek__icontains=q) | Q(pk__in=tagged))
        return qs

    def create(self, request, *args, **kwargs):
        ser = StoryWriteSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        with transaction.atomic():
            slug = services.unique_slug(ser.validated_data["title"])
            story = Story(author=request.user, slug=slug)
            tags = ser._apply(story, dict(ser.validated_data))
            services.save_revision(story, request.user, request=request, action="story.created")
            if tags is not None:
                story.tags.set(tags)
        return Response(
            StoryDetailSerializer(story, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class StoryDetailView(PublicCacheMixin, APIView):
    permission_classes = [IsVerifiedFounder, IsAuthorOrReadOnly]
    throttle_scope = "feed"

    def get_object(self, slug):
        story = get_object_or_404(
            Story.objects.select_related("author", "author__founder_profile__company", "cover"),
            slug=slug,
        )
        user = self.request.user
        if not story.is_public and story.author_id != getattr(user, "pk", None):
            if not (user.is_authenticated and user.is_moderator):
                raise Http404  # drafts/hidden stories are indistinguishable from missing
        self.check_object_permissions(self.request, story)
        return story

    def get(self, request, slug):
        return Response(
            StoryDetailSerializer(self.get_object(slug), context={"request": request}).data
        )

    def patch(self, request, slug):
        story = self.get_object(slug)
        if story.status in (Story.Status.HIDDEN, Story.Status.REMOVED):
            return Response(
                {"error": {"code": "locked", "message": "This story is locked."}},
                status=status.HTTP_403_FORBIDDEN,
            )
        ser = StoryWriteSerializer(
            story, data=request.data, partial=True, context={"request": request}
        )
        ser.is_valid(raise_exception=True)
        with transaction.atomic():
            tags = ser._apply(story, dict(ser.validated_data))
            services.save_revision(story, request.user, request=request)
            if tags is not None:
                story.tags.set(tags)
        return Response(StoryDetailSerializer(story, context={"request": request}).data)

    def delete(self, request, slug):
        story = self.get_object(slug)
        with transaction.atomic():
            story.status = Story.Status.REMOVED
            story.save(update_fields=["status", "updated_at"])
            audit.record("story.removed_by_author", target=story, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PublishView(APIView):
    permission_classes = [IsVerifiedFounder]
    throttle_scope = "write"

    def post(self, request, slug):
        story = get_object_or_404(Story, slug=slug, author=request.user)
        if story.status != Story.Status.DRAFT:
            return Response(
                {"error": {"code": "invalid_state", "message": "Only drafts can be published."}},
                status=400,
            )
        with transaction.atomic():
            story.publish()
            story.save(update_fields=["status", "published_at", "updated_at"])
            audit.record(
                "story.published",
                target=story,
                request=request,
                metadata={"content_hash": story.content_hash},
            )
        return Response(StoryDetailSerializer(story, context={"request": request}).data)


class RevisionListView(PublicCacheMixin, generics.ListAPIView):
    """Public, verifiable edit history (hashes only) of a published story."""

    permission_classes = [AllowAny]
    serializer_class = RevisionSerializer
    pagination_class = None

    def get_queryset(self):
        story = get_object_or_404(Story, slug=self.kwargs["slug"], status=Story.Status.PUBLISHED)
        return story.revisions.order_by("number")


class MyStoriesView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StoryDetailSerializer
    pagination_class = SmallCursorPagination

    def get_queryset(self):
        return (
            Story.objects.filter(author=self.request.user)
            .exclude(status=Story.Status.REMOVED)
            .select_related("author", "cover")
            .order_by("-created_at")
        )


class FounderView(PublicCacheMixin, APIView):
    permission_classes = [AllowAny]
    throttle_scope = "feed"

    def get(self, request, handle):
        user = get_object_or_404(
            User.objects.select_related("founder_profile__company"),
            handle=handle,
            is_suspended=False,
            is_active=True,
        )
        data = PublicUserSerializer(user).data
        profile = getattr(user, "founder_profile", None)
        if profile and profile.is_currently_verified:
            data["founder"] = {
                "company": profile.company.name,
                "domain": profile.company.domain,
                "title": profile.title,
                "verified_at": profile.verified_at,
            }
        data["follower_count"] = user.followers.count()
        return Response(data)


class TagListView(PublicCacheMixin, generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = TagSerializer
    pagination_class = None
    queryset = Tag.objects.order_by("name")


class UploadView(APIView):
    """Step 1 of an upload: reserve a Media row and hand back a presigned POST."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "upload"

    def post(self, request):
        ser = UploadRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        media = Media(owner=request.user, declared_type=ser.validated_data["content_type"])
        media.original_key = f"u/{request.user.pk.hex}/{media.id.hex}"
        media.save()
        return Response(
            {
                "media_id": str(media.id),
                "upload": storage.presigned_upload(media.original_key, media.declared_type),
            },
            status=status.HTTP_201_CREATED,
        )


class UploadCompleteView(APIView):
    """Step 2: the client says the upload finished; a worker sanitises the file."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "upload"

    def post(self, request, media_id):
        media = get_object_or_404(Media, pk=media_id, owner=request.user)
        if media.status == Media.Status.PENDING:
            media.status = Media.Status.PROCESSING
            media.save(update_fields=["status"])
            transaction.on_commit(lambda: process_media.delay(str(media.id)))
        return Response(MediaSerializer(media).data, status=status.HTTP_202_ACCEPTED)

    def get(self, request, media_id):
        media = get_object_or_404(Media, pk=media_id, owner=request.user)
        return Response(MediaSerializer(media).data)
