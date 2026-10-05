from drf_spectacular.utils import extend_schema
from rest_framework.views import APIView
from rest_framework.response import Response
from modules.clients.models import ClientRecord
from modules.workspaces.policies import require_business
from modules.shared.api import page
from tenancy.context import workspace_context
from .models import Attendance
from .attendance import (
    attendance_data,
    attendance_preview,
    record_attendance,
    void_attendance,
)
from .attendance_serializers import (
    AttendanceWriteSerializer,
    VoidSerializer,
    AttendanceReadSerializer,
    AttendancePreviewSerializer,
    AttendancePageSerializer,
    SearchPageSerializer,
    SearchClientSerializer,
    AttendanceQuerySerializer,
)


class AttendanceSearchView(APIView):
    @extend_schema(
        parameters=[AttendanceQuerySerializer], responses=SearchPageSerializer
    )
    def get(self, request, workspace_id):
        context = require_business(request.user, workspace_id, "gym.attendance")
        query = AttendanceQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        with workspace_context(context.workspace.id):
            clients = ClientRecord.objects.filter(
                workspace=context.workspace,
                full_name__icontains=query.validated_data["q"],
            ).order_by("full_name", "id")
            return Response(
                page(request, clients, lambda c: SearchClientSerializer(c).data)
            )


class AttendanceListView(APIView):
    @extend_schema(
        parameters=[AttendanceQuerySerializer], responses=AttendancePageSerializer
    )
    def get(self, request, workspace_id):
        context = require_business(request.user, workspace_id, "gym.attendance")
        query = AttendanceQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        with workspace_context(context.workspace.id):
            entries = (
                Attendance.objects.filter(
                    workspace=context.workspace,
                    client__full_name__icontains=query.validated_data["q"],
                )
                .select_related("client", "actor", "void_record__actor")
                .order_by("-created_at", "id")
            )
            if "date" in query.validated_data:
                entries = entries.filter(local_date=query.validated_data["date"])
            return Response(page(request, entries, attendance_data))


class AttendancePreviewView(APIView):
    @extend_schema(responses=AttendancePreviewSerializer)
    def get(self, request, workspace_id, client_id):
        context = require_business(request.user, workspace_id, "gym.attendance")
        with workspace_context(context.workspace.id):
            return Response(attendance_preview(context, client_id))


class AttendanceCreateView(APIView):
    @extend_schema(
        request=AttendanceWriteSerializer, responses={201: AttendanceReadSerializer}
    )
    def post(self, request, workspace_id, client_id):
        context = require_business(request.user, workspace_id, "gym.attendance")
        data = AttendanceWriteSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        with workspace_context(context.workspace.id):
            return Response(
                attendance_data(
                    record_attendance(context, client_id, data.validated_data)
                ),
                status=201,
            )


class AttendanceVoidView(APIView):
    @extend_schema(request=VoidSerializer, responses=AttendanceReadSerializer)
    def post(self, request, workspace_id, attendance_id):
        context = require_business(
            request.user, workspace_id, "gym.attendance", owner=True
        )
        data = VoidSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        with workspace_context(context.workspace.id):
            return Response(
                attendance_data(
                    void_attendance(context, attendance_id, data.validated_data)
                )
            )
