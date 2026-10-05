from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from modules.workspaces.policies import require_business
from tenancy.context import workspace_context
from modules.shared.api import page
from modules.shared.operations import lock_client
from .models import Membership
from .memberships import preview, enroll, membership_data
from .changes import change_membership
from .serializers import (
    PreviewSerializer,
    PreviewReadSerializer,
    EnrollmentSerializer,
    MembershipReadSerializer,
    MembershipPageSerializer,
    ChangeSerializer,
    CancelSerializer,
)


def enrollment_context(request, workspace_id):
    context = require_business(request.user, workspace_id, "gym.manage")
    require_business(request.user, workspace_id, "receivables.manage")
    return context


class MembershipsView(APIView):
    @extend_schema(responses=MembershipPageSerializer)
    def get(self, request, workspace_id, client_id):
        context = require_business(request.user, workspace_id, "gym.manage")
        with workspace_context(context.workspace.id):
            client = lock_client(context, client_id)
            queryset = (
                Membership.objects.filter(workspace=context.workspace, client=client)
                .select_related("plan_version", "client")
                .order_by("start_date", "created_at", "id")
            )
            return Response(
                page(
                    request,
                    queryset,
                    lambda m: (
                        MembershipReadSerializer(membership_data(context, m)).data
                    ),
                )
            )


class PreviewView(APIView):
    @extend_schema(request=PreviewSerializer, responses=PreviewReadSerializer)
    def post(self, request, workspace_id, client_id):
        context = enrollment_context(request, workspace_id)
        serializer = PreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with workspace_context(context.workspace.id):
            return Response(
                PreviewReadSerializer(
                    preview(context, client_id, serializer.validated_data)
                ).data
            )


class EnrollmentView(APIView):
    @extend_schema(
        request=EnrollmentSerializer, responses={201: MembershipReadSerializer}
    )
    def post(self, request, workspace_id, client_id):
        context = enrollment_context(request, workspace_id)
        serializer = EnrollmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with workspace_context(context.workspace.id):
            return Response(
                MembershipReadSerializer(
                    membership_data(
                        context, enroll(context, client_id, serializer.validated_data)
                    )
                ).data,
                status=201,
            )


class ChangeView(APIView):
    kind = "FREEZE"
    input_serializer = ChangeSerializer

    @extend_schema(request=ChangeSerializer, responses=MembershipReadSerializer)
    def post(self, request, workspace_id, client_id, membership_id):
        context = require_business(request.user, workspace_id, "gym.manage", owner=True)
        serializer = self.input_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with workspace_context(context.workspace.id):
            result = change_membership(
                context, client_id, membership_id, self.kind, serializer.validated_data
            )
            return Response(
                MembershipReadSerializer(membership_data(context, result)).data
            )


class CorrectView(ChangeView):
    kind = "CORRECT"


class CancelView(ChangeView):
    kind = "CANCEL"
    input_serializer = CancelSerializer

    @extend_schema(request=CancelSerializer, responses=MembershipReadSerializer)
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)
