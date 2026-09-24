from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import VerificationRequest
from .serializers import (
    ConfirmSerializer,
    VerificationRequestSerializer,
    VerificationSubmitSerializer,
)


class MyVerificationView(APIView):
    """GET: my latest request. POST: start a new one (supersedes any open request)."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "verification"

    def get(self, request):
        req = VerificationRequest.objects.filter(user=request.user).order_by("-created_at").first()
        return Response(VerificationRequestSerializer(req).data if req else None)

    def post(self, request):
        ser = VerificationSubmitSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        req = services.submit(request.user, ser.validated_data, request=request)
        return Response(VerificationRequestSerializer(req).data, status=status.HTTP_201_CREATED)


class ConfirmEmailView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "verification"

    def post(self, request):
        ser = ConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            req = services.confirm_email(request.user, ser.validated_data["token"], request)
        except services.VerificationError as exc:
            return Response(
                {"error": {"code": "invalid_token", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(VerificationRequestSerializer(req).data)
