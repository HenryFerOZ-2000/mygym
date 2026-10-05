import hashlib
import json
from django.db import connection

from rest_framework.exceptions import ValidationError
from modules.clients.models import ClientRecord
from modules.audit.services import record_event
from modules.shared.api import find


def lock_client(context, identifier):
    return find(
        ClientRecord.objects.select_for_update().filter(workspace=context.workspace),
        identifier,
    )


def fingerprint(data):
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, default=str).encode()
    ).hexdigest()


def replay(queryset, data):
    # Serialize the request key even when concurrent submissions name different
    # clients. A client row lock alone cannot protect this workspace-wide key.
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(current_setting('app.workspace_id', true) || %s, 0))",
            [":" + queryset.model._meta.db_table + ":" + str(data["request_id"])],
        )
    existing = queryset.filter(request_id=data["request_id"]).first()
    if existing and existing.fingerprint != fingerprint(data):
        raise ValidationError(
            {"request_id": "Esta solicitud ya se utilizó con otras condiciones."}
        )
    return existing


def audit(context, action, obj, fields):
    record_event(
        workspace=context.workspace,
        actor=context.actor,
        action=action,
        object_id=obj.id,
        changed_fields=fields,
    )
