"""
Password reset (forgot password) and password change.

Reset links use Django's stateless PasswordResetTokenGenerator: an HMAC over the user's
id, current password hash, last login and a timestamp. Nothing is stored, a link expires
after PASSWORD_RESET_TIMEOUT, and it stops working the moment the password changes
(so it is single-use). Changing the password also invalidates every other session,
because Django ties each session to a hash of the password.
"""

from django.conf import settings
from django.contrib.auth import password_validation, update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit import services as audit
from apps.common.tasks import send_email_task
from apps.common.turnstile import require_turnstile

from .models import User

RESET_COOLDOWN_SECONDS = 10 * 60
GENERIC_OK = {"ok": True, "message": "If that email has an account, a reset link is on its way."}


def _notify_password_changed(user: User) -> None:
    send_email_task.delay(
        subject="Your Wall of Founders password was changed",
        body=(
            f"Hi {user.display_name or user.handle},\n\n"
            "The password for your account was just changed, and you've been signed out "
            "on all other devices.\n\n"
            f"If this wasn't you, reset your password right away: {settings.SITE_URL}/forgot\n"
        ),
        to=user.email,
    )


class ResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)


class ResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=64)
    token = serializers.CharField(max_length=128)
    password = serializers.CharField(max_length=128, write_only=True)


class ChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(max_length=128, write_only=True)
    new_password = serializers.CharField(max_length=128, write_only=True)


class PasswordResetRequestView(APIView):
    """Always answers the same way, so it can't be used to find out who has an account."""

    permission_classes = [AllowAny]
    throttle_scope = "password"

    def post(self, request):
        require_turnstile(request)
        ser = ResetRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        email = ser.validated_data["email"].strip().lower()
        user = User.objects.filter(email=email, is_active=True, is_suspended=False).first()
        # Per-account cooldown stops the endpoint being used to flood someone's inbox.
        if user and cache.add(f"pwreset:{user.pk}", 1, RESET_COOLDOWN_SECONDS):
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            link = f"{settings.SITE_URL}/reset?uid={uid}&token={token}"
            send_email_task.delay(
                subject="Reset your Wall of Founders password",
                body=(
                    f"Hi {user.display_name or user.handle},\n\n"
                    "Use this link to choose a new password. It works once and expires in 1 hour:\n"
                    f"{link}\n\n"
                    "If you didn't ask for this, ignore this email; your password won't change."
                ),
                to=user.email,
            )
            audit.record("auth.password_reset_requested", target=user, request=request)
        return Response(GENERIC_OK, status=status.HTTP_202_ACCEPTED)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "password"

    def post(self, request):
        ser = ResetConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        try:
            user = User.objects.get(
                pk=force_str(urlsafe_base64_decode(data["uid"])), is_active=True
            )
        except (User.DoesNotExist, ValueError, TypeError, DjangoValidationError, OverflowError):
            user = None
        if user is None or not default_token_generator.check_token(user, data["token"]):
            return Response(
                {
                    "error": {
                        "code": "invalid_token",
                        "message": "This reset link is invalid or has expired. Request a new one.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            password_validation.validate_password(data["password"], user)
        except DjangoValidationError as exc:
            return Response(
                {
                    "error": {
                        "code": "invalid",
                        "message": "Choose a stronger password.",
                        "fields": {"password": list(exc.messages)},
                    }
                },
                status=400,
            )
        user.set_password(data["password"])
        user.failed_login_count = 0
        user.locked_until = None
        user.save(update_fields=["password", "failed_login_count", "locked_until"])
        audit.record("auth.password_reset", target=user, request=request)
        _notify_password_changed(user)
        # No automatic login: the user signs in normally (with 2FA if enabled).
        return Response({"ok": True})


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "password"

    def post(self, request):
        ser = ChangeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(ser.validated_data["current_password"]):
            return Response(
                {
                    "error": {
                        "code": "invalid",
                        "message": "Invalid request.",
                        "fields": {"current_password": ["That isn't your current password."]},
                    }
                },
                status=400,
            )
        try:
            password_validation.validate_password(ser.validated_data["new_password"], user)
        except DjangoValidationError as exc:
            return Response(
                {
                    "error": {
                        "code": "invalid",
                        "message": "Choose a stronger password.",
                        "fields": {"new_password": list(exc.messages)},
                    }
                },
                status=400,
            )
        user.set_password(ser.validated_data["new_password"])
        user.save(update_fields=["password"])
        update_session_auth_hash(request, user)  # keep this session; all others are signed out
        audit.record("auth.password_changed", actor=user, target=user, request=request)
        _notify_password_changed(user)
        return Response({"ok": True})
