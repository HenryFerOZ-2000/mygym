from dataclasses import dataclass
from uuid import UUID

from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from .models import Workspace, WorkspaceCapability
from .selectors import list_authorized_workspaces


@dataclass(frozen=True)
class WorkspaceContext:
    workspace: Workspace
    actor: object


def parse_uuid(value):
    try:
        return UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError({"id": ["Identificador inválido."]}) from None


def require_client_management(user, workspace_id):
    workspace_id = parse_uuid(workspace_id)
    access = list_authorized_workspaces(user).filter(workspace_id=workspace_id).first()
    if access is None:
        raise NotFound()
    if (
        access.role not in {"OWNER", "RECEPTION"}
        or not WorkspaceCapability.objects.filter(
            workspace_id=workspace_id, code="clients.manage", enabled=True
        ).exists()
    ):
        raise PermissionDenied()
    return WorkspaceContext(workspace=access.workspace, actor=user)


def require_business(user, workspace_id, capability, owner=False):
    workspace_id = parse_uuid(workspace_id)
    access = list_authorized_workspaces(user).filter(workspace_id=workspace_id).first()
    if access is None:
        raise NotFound()
    if (
        access.role not in ({"OWNER"} if owner else {"OWNER", "RECEPTION"})
        or (capability.startswith("gym.") and access.workspace.kind != "GYM")
        or not WorkspaceCapability.objects.filter(
            workspace_id=workspace_id, code=capability, enabled=True
        ).exists()
    ):
        raise PermissionDenied()
    return WorkspaceContext(workspace=access.workspace, actor=user)
