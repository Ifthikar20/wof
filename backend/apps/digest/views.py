from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.turnstile import require_turnstile

from . import services
from .models import DigestIssue
from .serializers import IssueSerializer, SubscribeSerializer, TokenSerializer


class SubscribeView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "subscribe"

    def post(self, request):
        require_turnstile(request)
        ser = SubscribeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = request.user if request.user.is_authenticated else None
        services.subscribe(ser.validated_data["email"], user=user)
        return Response(
            {"ok": True, "message": "Check your inbox to confirm."}, status=status.HTTP_202_ACCEPTED
        )


class ConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "subscribe"

    def post(self, request):
        ser = TokenSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if not services.confirm(ser.validated_data["token"]):
            return Response(
                {"error": {"code": "invalid_token", "message": "This link is invalid or expired."}},
                status=400,
            )
        return Response({"ok": True})


@csrf_exempt  # RFC 8058 one-click POST comes from the mail provider, authorised by the token
@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def unsubscribe_view(request):
    # POST only: link scanners (Outlook Safe Links etc.) prefetch GETs, which must never
    # unsubscribe anyone. The email footer links to a frontend page that POSTs here.
    token = request.query_params.get("token") or request.data.get("token", "")
    ok = services.unsubscribe(token)
    return Response({"ok": ok}, status=200 if ok else 400)


class IssueArchiveView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = IssueSerializer
    queryset = DigestIssue.objects.filter(status=DigestIssue.Status.SENT)
    pagination_class = None

    def get_queryset(self):
        return super().get_queryset()[:52]


class IssueDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, number):
        issue = get_object_or_404(DigestIssue, number=number, status=DigestIssue.Status.SENT)
        return Response(IssueSerializer(issue).data)
