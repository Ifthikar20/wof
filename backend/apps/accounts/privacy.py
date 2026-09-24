"""
Self-service data export and account deletion (GDPR/CCPA access and erasure).

Deletion anonymises the account instead of deleting the row: stories reference their
author (on_delete=PROTECT) and story revisions are append-only by design. Everything that
identifies the person is removed or blanked; revisions of removed stories are retained
as part of the tamper-evident record, which the privacy policy discloses.
"""

import uuid

from django.conf import settings
from django.contrib.auth import logout
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit import services as audit
from apps.audit.models import AuditLog
from apps.common.hashing import sha256_hex
from apps.common.tasks import send_email_task
from apps.digest.models import Subscription
from apps.engagement.models import Board, Comment, Follow, Like, Report, Save
from apps.stories.models import Media, Story
from apps.verification.models import FounderProfile, VerificationRequest

from . import totp
from .models import RetiredHandle, User


def _iso(dt):
    return dt.isoformat() if dt else None


def build_export(user: User) -> dict:
    profile = getattr(user, "founder_profile", None)
    stories = Story.objects.filter(author=user).prefetch_related("revisions", "tags")
    boards = Board.objects.filter(owner=user).prefetch_related("saves__story")
    events = AuditLog.objects.filter(actor=user) | AuditLog.objects.filter(target_id=str(user.pk))
    return {
        "exported_at": timezone.now().isoformat(),
        "account": {
            "id": str(user.pk),
            "email": user.email,
            "handle": user.handle,
            "display_name": user.display_name,
            "bio": user.bio,
            "role": user.role,
            "date_joined": _iso(user.date_joined),
            "last_login": _iso(user.last_login),
            "two_factor_enabled": user.totp_enabled,
        },
        "founder_profile": profile
        and {
            "company": profile.company.name,
            "domain": profile.company.domain,
            "title": profile.title,
            "status": profile.status,
            "verified_at": _iso(profile.verified_at),
            "expires_at": _iso(profile.expires_at),
            "linkedin_url": profile.linkedin_url,
        },
        "verification_requests": [
            {
                "company_name": r.company_name,
                "company_domain": r.company_domain,
                "work_email": r.work_email,
                "role_title": r.role_title,
                "linkedin_url": r.linkedin_url,
                "crunchbase_url": r.crunchbase_url,
                "notes": r.notes,
                "status": r.status,
                "decision_reason": r.decision_reason,
                "created_at": _iso(r.created_at),
            }
            for r in VerificationRequest.objects.filter(user=user)
        ],
        "stories": [
            {
                "slug": s.slug,
                "title": s.title,
                "subtitle": s.dek,
                "body_markdown": s.body_markdown,
                "status": s.status,
                "tags": [t.slug for t in s.tags.all()],
                "published_at": _iso(s.published_at),
                "created_at": _iso(s.created_at),
                "likes": s.like_count,
                "saves": s.save_count,
                "revisions": [
                    {
                        "number": r.number,
                        "created_at": _iso(r.created_at),
                        "title": r.title,
                        "subtitle": r.dek,
                        "body_markdown": r.body_markdown,
                        "content_hash": r.content_hash,
                    }
                    for r in s.revisions.all()
                ],
            }
            for s in stories
        ],
        "comments": [
            {
                "story": c.story.slug,
                "body": c.body,
                "status": c.status,
                "created_at": _iso(c.created_at),
            }
            for c in Comment.objects.filter(author=user).select_related("story")
        ],
        "likes": [
            {"story": lk.story.slug, "created_at": _iso(lk.created_at)}
            for lk in Like.objects.filter(user=user).select_related("story")
        ],
        "boards": [
            {
                "name": b.name,
                "description": b.description,
                "private": b.is_private,
                "stories": [sv.story.slug for sv in b.saves.all()],
                "created_at": _iso(b.created_at),
            }
            for b in boards
        ],
        "following": [
            f.founder.handle for f in Follow.objects.filter(follower=user).select_related("founder")
        ],
        "reports_filed": [
            {
                "target_type": r.target_type,
                "target_id": r.target_id,
                "reason": r.reason,
                "details": r.details,
                "status": r.status,
                "created_at": _iso(r.created_at),
            }
            for r in Report.objects.filter(reporter=user)
        ],
        "digest_subscriptions": [
            {"email": s.email, "status": s.status, "confirmed_at": _iso(s.confirmed_at)}
            for s in Subscription.objects.filter(user=user)
            | Subscription.objects.filter(email=user.email)
        ],
        "uploads": [
            {"id": str(m.id), "status": m.status, "created_at": _iso(m.created_at)}
            for m in Media.objects.filter(owner=user)
        ],
        "security_events": [
            {"action": e.action, "at": _iso(e.created_at), "ip": e.ip, "user_agent": e.user_agent}
            for e in events.order_by("-id")[:1000]
        ],
    }


@transaction.atomic
def delete_account(user: User, request=None) -> None:
    original_email = user.email
    # Stories leave the wall; revisions stay in the tamper-evident record.
    Story.objects.filter(author=user).exclude(status=Story.Status.REMOVED).update(
        status=Story.Status.REMOVED
    )

    # Comments: blank the text and hide; keep counters right.
    for c in Comment.objects.filter(author=user, status=Comment.Status.VISIBLE):
        Story.objects.filter(pk=c.story_id, comment_count__gt=0).update(
            comment_count=F("comment_count") - 1
        )
    Comment.objects.filter(author=user).update(body="", status=Comment.Status.HIDDEN, spam_flags=[])

    for like in Like.objects.filter(user=user):
        Story.objects.filter(pk=like.story_id, like_count__gt=0).update(
            like_count=F("like_count") - 1
        )
    Like.objects.filter(user=user).delete()
    for sv in Save.objects.filter(board__owner=user):
        Story.objects.filter(pk=sv.story_id, save_count__gt=0).update(
            save_count=F("save_count") - 1
        )
    Board.objects.filter(owner=user).delete()
    Follow.objects.filter(follower=user).delete()
    Follow.objects.filter(founder=user).delete()
    Report.objects.filter(reporter=user).update(reporter=None, details="")
    Subscription.objects.filter(user=user).delete()
    Subscription.objects.filter(email=original_email).delete()
    FounderProfile.objects.filter(user=user).delete()
    VerificationRequest.objects.filter(user=user).delete()

    media_keys = []
    for m in Media.objects.filter(owner=user):
        media_keys += [k for k in (m.original_key, m.display_key, m.thumb_key) if k]
    Media.objects.filter(owner=user).delete()
    if media_keys:
        from apps.stories.tasks import delete_media_objects

        transaction.on_commit(lambda: delete_media_objects.delay(media_keys))

    RetiredHandle.objects.get_or_create(handle_hash=sha256_hex(user.handle))
    token = uuid.uuid4().hex
    user.email = f"deleted-{token}@deleted.invalid"
    user.handle = f"deleted_{token[:12]}"
    user.display_name = "Deleted user"
    user.bio = ""
    user.avatar = None
    user.set_unusable_password()  # also invalidates every session (session hash changes)
    user.totp_secret = ""
    user.totp_enabled = False
    user.is_active = False
    user.is_staff = False
    user.is_superuser = False
    user.role = User.Role.READER
    user.email_verified = False
    user.save()
    audit.record("account.deleted", target=user, request=request)

    transaction.on_commit(
        lambda: send_email_task.delay(
            subject="Your Wall of Founders account was deleted",
            body=(
                "Your account and personal data have been deleted, and your stories are no longer "
                "on the Wall.\n\nIf you didn't do this, reply to this email right away.\n"
                f"{settings.SITE_URL}"
            ),
            to=original_email,
        )
    )


class DeleteSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=128, write_only=True)
    otp = serializers.CharField(max_length=8, required=False, allow_blank=True)
    confirm = serializers.CharField(max_length=16)


class ExportView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "export"

    def get(self, request):
        data = build_export(request.user)
        audit.record("account.exported", actor=request.user, target=request.user, request=request)
        filename = f"wall-of-founders-{request.user.handle}-{timezone.now():%Y-%m-%d}.json"
        response = JsonResponse(data, json_dumps_params={"indent": 2, "ensure_ascii": False})
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Cache-Control"] = "private, no-store"
        return response


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "password"

    def post(self, request):
        ser = DeleteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = request.user
        fields = {}
        if ser.validated_data["confirm"] != "DELETE":
            fields["confirm"] = ["Type DELETE to confirm."]
        if not user.check_password(ser.validated_data["password"]):
            fields["password"] = ["That isn't your password."]
        elif user.totp_enabled and not totp.verify(user, ser.validated_data.get("otp") or ""):
            fields["otp"] = ["Enter a valid code from your authenticator app."]
        if user.is_superuser:
            fields["confirm"] = ["Admin accounts must be removed by another admin."]
        if fields:
            return Response(
                {"error": {"code": "invalid", "message": "Invalid request.", "fields": fields}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        delete_account(user, request=request)
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)
