from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import SmallCursorPagination
from apps.common.permissions import IsModerator
from apps.engagement.models import Comment, Report
from apps.verification import services as verification
from apps.verification.models import VerificationRequest
from apps.verification.serializers import DecisionSerializer, ModeratorVerificationSerializer

from . import services
from .serializers import ActionSerializer, HeldCommentSerializer, ModReportSerializer


class VerificationQueueView(generics.ListAPIView):
    permission_classes = [IsModerator]
    serializer_class = ModeratorVerificationSerializer
    pagination_class = SmallCursorPagination

    def get_queryset(self):
        wanted = self.request.query_params.get("status", VerificationRequest.Status.UNDER_REVIEW)
        return VerificationRequest.objects.filter(status=wanted).select_related("user")


class VerificationDecisionView(APIView):
    permission_classes = [IsModerator]

    def post(self, request, request_id):
        req = get_object_or_404(VerificationRequest, pk=request_id)
        ser = DecisionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            req = verification.decide(
                req,
                request.user,
                ser.validated_data["decision"],
                ser.validated_data.get("reason", ""),
                request=request,
            )
        except verification.VerificationError as exc:
            return Response({"error": {"code": "invalid_state", "message": str(exc)}}, status=400)
        return Response(ModeratorVerificationSerializer(req).data)


class ReportQueueView(generics.ListAPIView):
    permission_classes = [IsModerator]
    serializer_class = ModReportSerializer
    pagination_class = SmallCursorPagination

    def get_queryset(self):
        return Report.objects.filter(status=Report.Status.OPEN).select_related("reporter")


class HeldCommentsView(generics.ListAPIView):
    permission_classes = [IsModerator]
    serializer_class = HeldCommentSerializer
    pagination_class = SmallCursorPagination

    def get_queryset(self):
        return Comment.objects.filter(status=Comment.Status.PENDING).select_related(
            "author", "story"
        )


class ActionView(APIView):
    permission_classes = [IsModerator]

    def post(self, request):
        ser = ActionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        report = None
        if data.get("report_id"):
            report = get_object_or_404(Report, pk=data["report_id"])
        try:
            entry = services.apply(
                request.user,
                data["action"],
                data["target_id"],
                data["reason"],
                report=report,
                request=request,
            )
        except (services.ModerationError, ObjectDoesNotExist, ValueError) as exc:
            return Response({"error": {"code": "invalid", "message": str(exc)}}, status=400)
        return Response(
            {"id": str(entry.id), "action": entry.action}, status=status.HTTP_201_CREATED
        )
