from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.audit import services as audit
from apps.common.pagination import SmallCursorPagination
from apps.common.turnstile import require_turnstile
from apps.moderation.rules import check_text
from apps.stories.models import Story

from .models import Board, Comment, Follow, Like, Save
from .serializers import (
    BoardDetailSerializer,
    BoardSerializer,
    CommentSerializer,
    ReportSerializer,
    SaveSerializer,
)


def published_story(slug):
    return get_object_or_404(Story, slug=slug, status=Story.Status.PUBLISHED)


class LikeView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "write"

    def post(self, request, slug):
        story = published_story(slug)
        try:
            with transaction.atomic():
                Like.objects.create(user=request.user, story=story)
                Story.objects.filter(pk=story.pk).update(like_count=F("like_count") + 1)
        except IntegrityError:
            pass  # idempotent
        return Response({"liked": True}, status=status.HTTP_200_OK)

    def delete(self, request, slug):
        story = published_story(slug)
        with transaction.atomic():
            deleted, _ = Like.objects.filter(user=request.user, story=story).delete()
            if deleted:
                Story.objects.filter(pk=story.pk, like_count__gt=0).update(
                    like_count=F("like_count") - 1
                )
        return Response({"liked": False})


class CommentListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = CommentSerializer
    pagination_class = SmallCursorPagination

    def get_throttles(self):
        self.throttle_scope = "comment" if self.request.method == "POST" else "feed"
        return super().get_throttles()

    def get_queryset(self):
        story = published_story(self.kwargs["slug"])
        return story.comments.filter(status=Comment.Status.VISIBLE).select_related(
            "author", "author__founder_profile"
        )

    def create(self, request, *args, **kwargs):
        if request.user.is_suspended:
            return Response(status=status.HTTP_403_FORBIDDEN)
        require_turnstile(request)
        story = published_story(self.kwargs["slug"])
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        flags = check_text(ser.validated_data["body"], request.user)
        with transaction.atomic():
            comment = Comment.objects.create(
                story=story,
                author=request.user,
                body=ser.validated_data["body"],
                status=Comment.Status.PENDING if flags else Comment.Status.VISIBLE,
                spam_flags=flags,
            )
            if not flags:
                Story.objects.filter(pk=story.pk).update(comment_count=F("comment_count") + 1)
        return Response(self.get_serializer(comment).data, status=status.HTTP_201_CREATED)


class BoardListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BoardSerializer
    pagination_class = None
    throttle_scope = "write"

    def get_queryset(self):
        return Board.objects.filter(owner=self.request.user).order_by("name")

    def perform_create(self, serializer):
        if Board.objects.filter(owner=self.request.user).count() >= 200:
            raise ValidationError("Board limit reached.")
        try:
            serializer.save(owner=self.request.user)
        except IntegrityError as exc:
            raise ValidationError({"name": "You already have a board with this name."}) from exc


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = BoardDetailSerializer
    lookup_url_kwarg = "board_id"

    def get_queryset(self):
        user = self.request.user
        if self.request.method == "GET":
            # Public boards are visible to everyone; private ones only to the owner.
            if user.is_authenticated:
                return Board.objects.filter(Q(is_private=False) | Q(owner=user))
            return Board.objects.filter(is_private=False)
        return Board.objects.filter(owner=user)


class BoardSaveView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "write"

    def post(self, request, board_id):
        board = get_object_or_404(Board, pk=board_id, owner=request.user)
        ser = SaveSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        story = published_story(ser.validated_data["story"])
        try:
            with transaction.atomic():
                Save.objects.create(board=board, story=story)
                Story.objects.filter(pk=story.pk).update(save_count=F("save_count") + 1)
        except IntegrityError:
            pass
        return Response({"saved": True}, status=status.HTTP_201_CREATED)

    def delete(self, request, board_id, slug):
        board = get_object_or_404(Board, pk=board_id, owner=request.user)
        with transaction.atomic():
            deleted, _ = Save.objects.filter(board=board, story__slug=slug).delete()
            if deleted:
                Story.objects.filter(slug=slug, save_count__gt=0).update(
                    save_count=F("save_count") - 1
                )
        return Response(status=status.HTTP_204_NO_CONTENT)


class FollowView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "write"

    def post(self, request, handle):
        founder = get_object_or_404(User, handle=handle, is_suspended=False)
        if founder.pk == request.user.pk:
            return Response(
                {"error": {"code": "invalid", "message": "You can't follow yourself."}}, status=400
            )
        Follow.objects.get_or_create(follower=request.user, founder=founder)
        return Response({"following": True})

    def delete(self, request, handle):
        Follow.objects.filter(follower=request.user, founder__handle=handle).delete()
        return Response({"following": False})


class ReportView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReportSerializer
    throttle_scope = "report"

    def create(self, request, *args, **kwargs):
        require_turnstile(request)
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                report = ser.save(reporter=request.user)
                audit.record(
                    "report.filed",
                    target=report,
                    request=request,
                    metadata={
                        "target": f"{report.target_type}:{report.target_id}",
                        "reason": report.reason,
                    },
                )
        except IntegrityError:
            return Response({"ok": True}, status=status.HTTP_202_ACCEPTED)  # already reported
        return Response(self.get_serializer(report).data, status=status.HTTP_201_CREATED)
