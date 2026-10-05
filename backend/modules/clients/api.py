from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.workspaces.policies import require_client_management
from tenancy.context import workspace_context
from .serializers import (
    ClientReadSerializer,
    ClientWriteSerializer,
    ClientPageSerializer,
)
from .selectors import clients_for, get_client
from .services import create_client, update_client


class ClientListView(APIView):
    @extend_schema(
        operation_id="clients_list",
        responses=ClientPageSerializer,
        parameters=[OpenApiParameter("page", int), OpenApiParameter("page_size", int)],
    )
    def get(self, request, workspace_id):
        context = require_client_management(request.user, workspace_id)
        try:
            page = int(request.query_params.get("page", 1))
            size = min(int(request.query_params.get("page_size", 25)), 100)
            if page < 1 or size < 1:
                raise ValueError()
        except ValueError:
            raise ValidationError({"pagination": ["Usa enteros positivos."]}) from None
        with workspace_context(context.workspace.id):
            queryset = clients_for(context)
            count = queryset.count()
            start = (page - 1) * size
            if page > 1 and start >= count:
                raise NotFound()
            results = ClientReadSerializer(
                queryset[start : start + size], many=True
            ).data
            base = f"/api/v1/workspaces/{context.workspace.id}/clients/"
            return Response(
                {
                    "count": count,
                    "next": f"{base}?page={page + 1}&page_size={size}"
                    if start + size < count
                    else None,
                    "previous": f"{base}?page={page - 1}&page_size={size}"
                    if page > 1
                    else None,
                    "results": results,
                }
            )

    @extend_schema(request=ClientWriteSerializer, responses={201: ClientReadSerializer})
    def post(self, request, workspace_id):
        context = require_client_management(request.user, workspace_id)
        serializer = ClientWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with workspace_context(context.workspace.id):
            return Response(
                ClientReadSerializer(
                    create_client(context, serializer.validated_data)
                ).data,
                status=201,
            )


class ClientDetailView(APIView):
    @extend_schema(responses=ClientReadSerializer)
    def get(self, request, workspace_id, client_id):
        context = require_client_management(request.user, workspace_id)
        with workspace_context(context.workspace.id):
            return Response(ClientReadSerializer(get_client(context, client_id)).data)

    @extend_schema(request=ClientWriteSerializer, responses=ClientReadSerializer)
    def patch(self, request, workspace_id, client_id):
        context = require_client_management(request.user, workspace_id)
        with workspace_context(context.workspace.id):
            get_client(context, client_id)
            serializer = ClientWriteSerializer(data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            return Response(
                ClientReadSerializer(
                    update_client(context, client_id, serializer.validated_data)
                ).data
            )
