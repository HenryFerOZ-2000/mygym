from .models import WorkspaceAccess


def list_authorized_workspaces(user):
    if not user.is_authenticated or not user.is_active:
        return WorkspaceAccess.objects.none()
    return (
        WorkspaceAccess.objects.filter(
            user=user, is_active=True, workspace__is_active=True
        )
        .select_related("workspace")
        .prefetch_related("workspace__capabilities")
        .order_by("workspace__name", "workspace_id")
    )
