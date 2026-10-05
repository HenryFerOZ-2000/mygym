from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from .selectors import list_authorized_workspaces


class WorkspaceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    kind = serializers.CharField()
    timezone = serializers.CharField()
    role = serializers.CharField()
    capabilities = serializers.ListField(child=serializers.CharField())


class WorkspacesView(APIView):
    @extend_schema(responses=WorkspaceSerializer(many=True))
    def get(self, request):
        return Response(
            [
                {
                    "id": str(access.workspace_id),
                    "name": access.workspace.name,
                    "kind": access.workspace.kind,
                    "timezone": access.workspace.timezone,
                    "role": access.role,
                    "capabilities": [
                        c.code for c in access.workspace.capabilities.all() if c.enabled
                    ],
                }
                for access in list_authorized_workspaces(request.user)
            ]
        )
