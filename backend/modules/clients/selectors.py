from rest_framework.exceptions import NotFound
from modules.workspaces.policies import parse_uuid
from .models import ClientRecord


def clients_for(context):
    return ClientRecord.objects.filter(workspace=context.workspace).order_by(
        "created_at", "id"
    )


def get_client(context, client_id, *, for_update=False):
    queryset = clients_for(context)
    if for_update:
        queryset = queryset.select_for_update()
    record = queryset.filter(pk=parse_uuid(client_id)).first()
    if record is None:
        raise NotFound()
    return record
