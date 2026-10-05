from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from modules.shared.api import StrictSerializer
from modules.shared.reporting import ReportRangeSerializer
from modules.workspaces.policies import require_business
from modules.receivables.reports import financial_report
from tenancy.context import workspace_context
from .reports import attendance_report, expiry_report


class AttendanceReportSerializer(ReportRangeSerializer):
    as_of = serializers.DateTimeField()
    entries = serializers.IntegerField()
    clients = serializers.IntegerField()
    exceptions = serializers.IntegerField()
    voided = serializers.IntegerField()


class CurrencyReportSerializer(serializers.Serializer):
    currency = serializers.CharField()
    payments = serializers.DecimalField(max_digits=24, decimal_places=2)
    refunds = serializers.DecimalField(max_digits=24, decimal_places=2)
    net = serializers.DecimalField(max_digits=24, decimal_places=2)
    outstanding_now = serializers.DecimalField(max_digits=24, decimal_places=2)


class FinancialReportSerializer(ReportRangeSerializer):
    timezone = serializers.CharField()
    as_of = serializers.DateTimeField()
    currencies = CurrencyReportSerializer(many=True)


class ExpiryQuerySerializer(StrictSerializer):
    status = serializers.ChoiceField(
        choices=[
            "EXPIRING",
            "ACTIVE",
            "EXPIRED",
            "FROZEN",
            "FUTURE",
            "NO_MEMBERSHIP",
            "CLIENT_INACTIVE",
        ],
        default="EXPIRING",
    )
    horizon = serializers.IntegerField(min_value=1, max_value=90, default=7)
    q = serializers.CharField(max_length=120, allow_blank=True, default="")
    page = serializers.IntegerField(min_value=1, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, default=25)


class ExpiryRowSerializer(serializers.Serializer):
    client_id = serializers.UUIDField()
    full_name = serializers.CharField()
    status = serializers.CharField()
    coverage_end = serializers.DateField(allow_null=True)
    previous_end = serializers.DateField(allow_null=True)
    next_start = serializers.DateField(allow_null=True)
    last_day = serializers.DateField(allow_null=True)
    calendar_days_remaining = serializers.IntegerField(allow_null=True)


class ExpiryPageSerializer(serializers.Serializer):
    as_of = serializers.DateTimeField()
    reference_date = serializers.DateField()
    timezone = serializers.CharField()
    count = serializers.IntegerField()
    next = serializers.IntegerField(allow_null=True)
    previous = serializers.IntegerField(allow_null=True)
    results = ExpiryRowSerializer(many=True)


class AttendanceReportView(APIView):
    @extend_schema(
        parameters=[ReportRangeSerializer], responses=AttendanceReportSerializer
    )
    def get(self, request, workspace_id):
        context = require_business(
            request.user, workspace_id, "gym.reports", owner=True
        )
        query = ReportRangeSerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        with workspace_context(context.workspace.id):
            return Response(
                attendance_report(
                    context,
                    query.validated_data["from_date"],
                    query.validated_data["to_date"],
                )
            )


class FinancialReportView(APIView):
    @extend_schema(
        parameters=[ReportRangeSerializer], responses=FinancialReportSerializer
    )
    def get(self, request, workspace_id):
        context = require_business(
            request.user, workspace_id, "receivables.reports", owner=True
        )
        require_business(request.user, workspace_id, "receivables.manage", owner=True)
        query = ReportRangeSerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        with workspace_context(context.workspace.id):
            return Response(
                financial_report(
                    context,
                    query.validated_data["from_date"],
                    query.validated_data["to_date"],
                )
            )


class ExpiryView(APIView):
    @extend_schema(parameters=[ExpiryQuerySerializer], responses=ExpiryPageSerializer)
    def get(self, request, workspace_id):
        context = require_business(request.user, workspace_id, "gym.manage")
        query = ExpiryQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        with workspace_context(context.workspace.id):
            return Response(expiry_report(context, query.validated_data))
