from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from modules.workspaces.policies import require_business
from modules.shared.api import page
from modules.shared.operations import lock_client
from tenancy.context import workspace_context
from .models import Charge, Payment
from .services import charge_data, payment_data, record_payment, refund_payment
from .serializers import (
    ChargePageSerializer,
    PaymentPageSerializer,
    PaymentSerializer,
    PaymentReadSerializer,
    RefundSerializer,
    RefundReadSerializer,
)


class ChargesView(APIView):
    @extend_schema(responses=ChargePageSerializer)
    def get(self, request, workspace_id, client_id):
        context = require_business(request.user, workspace_id, "receivables.manage")
        with workspace_context(context.workspace.id):
            client = lock_client(context, client_id)
            return Response(
                page(
                    request,
                    Charge.objects.filter(
                        workspace=context.workspace, client=client
                    ).order_by("created_at", "id"),
                    charge_data,
                )
            )


class PaymentsView(APIView):
    @extend_schema(responses=PaymentPageSerializer)
    def get(self, request, workspace_id, client_id):
        context = require_business(request.user, workspace_id, "receivables.manage")
        with workspace_context(context.workspace.id):
            client = lock_client(context, client_id)
            return Response(
                page(
                    request,
                    Payment.objects.filter(
                        workspace=context.workspace, client=client
                    ).order_by("created_at", "id"),
                    payment_data,
                )
            )

    @extend_schema(request=PaymentSerializer, responses={201: PaymentReadSerializer})
    def post(self, request, workspace_id, client_id):
        context = require_business(request.user, workspace_id, "receivables.manage")
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with workspace_context(context.workspace.id):
            return Response(
                payment_data(
                    record_payment(context, client_id, serializer.validated_data)
                ),
                status=201,
            )


class RefundView(APIView):
    @extend_schema(request=RefundSerializer, responses={201: RefundReadSerializer})
    def post(self, request, workspace_id, client_id, payment_id):
        context = require_business(
            request.user, workspace_id, "receivables.manage", owner=True
        )
        serializer = RefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with workspace_context(context.workspace.id):
            result = refund_payment(
                context, client_id, payment_id, serializer.validated_data
            )
            return Response(
                {"id": result.id, "amount": format(result.amount, ".2f")}, status=201
            )
