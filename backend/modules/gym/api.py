from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from modules.workspaces.policies import require_business
from tenancy.context import workspace_context
from modules.shared.api import page
from .models import Plan
from .serializers import (
    PlanWriteSerializer,
    PlanPatchSerializer,
    PlanReadSerializer,
    PlanPageSerializer,
)
from .services import create_plan, revise_plan, plan_data


class PlansView(APIView):
    @extend_schema(responses=PlanPageSerializer)
    def get(self, request, workspace_id):
        context = require_business(request.user, workspace_id, "gym.manage")
        with workspace_context(context.workspace.id):
            return Response(
                page(
                    request,
                    Plan.objects.filter(workspace=context.workspace).order_by(
                        "created_at", "id"
                    ),
                    lambda p: PlanReadSerializer(plan_data(p)).data,
                )
            )

    @extend_schema(request=PlanWriteSerializer, responses={201: PlanReadSerializer})
    def post(self, request, workspace_id):
        context = require_business(request.user, workspace_id, "gym.manage", owner=True)
        serializer = PlanWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with workspace_context(context.workspace.id):
            return Response(
                PlanReadSerializer(
                    plan_data(create_plan(context, serializer.validated_data))
                ).data,
                status=201,
            )


class PlanView(APIView):
    @extend_schema(request=PlanPatchSerializer, responses=PlanReadSerializer)
    def patch(self, request, workspace_id, plan_id):
        context = require_business(request.user, workspace_id, "gym.manage", owner=True)
        serializer = PlanPatchSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        with workspace_context(context.workspace.id):
            return Response(
                PlanReadSerializer(
                    plan_data(revise_plan(context, plan_id, serializer.validated_data))
                ).data
            )
