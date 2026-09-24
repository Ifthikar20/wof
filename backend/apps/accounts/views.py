from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit import services as audit
from apps.common.turnstile import require_turnstile

from . import totp
from .models import User
from .serializers import (
    LoginSerializer,
    MeSerializer,
    OtpSerializer,
    ProfileUpdateSerializer,
    SignupSerializer,
)

GENERIC_LOGIN_ERROR = {
    "error": {"code": "invalid_credentials", "message": "Invalid email, password or code."}
}


class CsrfView(APIView):
    """Issue the CSRF cookie. The SPA calls this once before any unsafe request."""

    permission_classes = [AllowAny]

    def get(self, request):
        get_token(request)
        return Response({"ok": True})


class SignupView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "signup"

    def post(self, request):
        require_turnstile(request)
        ser = SignupSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        if User.objects.filter(email=data["email"]).exists():
            # Do not reveal whether an email is registered.
            return Response({"ok": True}, status=status.HTTP_202_ACCEPTED)
        with transaction.atomic():
            user = User.objects.create_user(
                email=data["email"],
                password=data["password"],
                handle=data["handle"],
                display_name=data.get("display_name", ""),
            )
            audit.record("user.signup", actor=user, target=user, request=request)
        login(request, user)
        return Response(MeSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth"

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        email = ser.validated_data["email"].strip().lower()
        user = User.objects.filter(email=email).first()

        if user and user.is_locked():
            return Response(
                {"error": {"code": "locked", "message": "Too many attempts. Try again later."}},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        authed = authenticate(request, email=email, password=ser.validated_data["password"])
        if authed is None or authed.is_suspended:
            if user:
                user.register_failed_login()
                audit.record("auth.login_failed", target=user, request=request)
            return Response(GENERIC_LOGIN_ERROR, status=status.HTTP_401_UNAUTHORIZED)

        if authed.totp_enabled:
            code = ser.validated_data.get("otp") or ""
            if not code:
                return Response(
                    {"error": {"code": "otp_required", "message": "Enter your 2FA code."}},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            if not totp.verify(authed, code):
                authed.register_failed_login()
                audit.record("auth.otp_failed", target=authed, request=request)
                return Response(GENERIC_LOGIN_ERROR, status=status.HTTP_401_UNAUTHORIZED)

        authed.register_successful_login()
        login(request, authed)  # rotates the session key (prevents session fixation)
        # Marks this session as second-factor verified; the Django admin requires it.
        request.session["otp_verified"] = bool(authed.totp_enabled)
        audit.record("auth.login", actor=authed, target=authed, request=request)
        return Response(MeSerializer(authed).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        audit.record("auth.logout", request=request, target=request.user)
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    throttle_scope = "write"

    def get_permissions(self):
        return [AllowAny()] if self.request.method == "GET" else [IsAuthenticated()]

    def get(self, request):
        # 200 + null for anonymous visitors: "not logged in" is a normal state, not an error.
        if not request.user.is_authenticated:
            return JsonResponse(None, safe=False)  # DRF would render None as an empty body
        return Response(MeSerializer(request.user).data)

    def patch(self, request):
        ser = ProfileUpdateSerializer(request.user, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(MeSerializer(request.user).data)


class TotpSetupView(APIView):
    """Step 1: generate a secret (not yet active). Step 2: confirm with a valid code."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "auth"

    def post(self, request):
        user = request.user
        if user.totp_enabled:
            return Response(
                {"error": {"code": "already_enabled", "message": "2FA is already enabled."}},
                status=400,
            )
        user.totp_secret = totp.new_secret()
        user.totp_last_used_step = 0
        user.save(update_fields=["totp_secret", "totp_last_used_step"])
        return Response({"otpauth_uri": totp.provisioning_uri(user.totp_secret, user.email)})


class TotpConfirmView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "auth"

    def post(self, request):
        ser = OtpSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = request.user
        if not totp.verify(user, ser.validated_data["code"]):
            return Response(
                {"error": {"code": "invalid_code", "message": "Invalid code."}}, status=400
            )
        user.totp_enabled = True
        user.save(update_fields=["totp_enabled"])
        audit.record("auth.totp_enabled", actor=user, target=user, request=request)
        return Response(MeSerializer(user).data)
