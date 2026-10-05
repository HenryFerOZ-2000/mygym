from django.db import transaction
from modules.audit import services as audit
from .models import ClientRecord
from .selectors import get_client


@transaction.atomic
def create_client(context, data):
    record = ClientRecord.objects.create(workspace=context.workspace, **data)
    audit.record_event(
        workspace=context.workspace,
        actor=context.actor,
        action="client.created",
        object_id=record.id,
        changed_fields=list(data),
    )
    return record


@transaction.atomic
def update_client(context, client_id, changes):
    record = get_client(context, client_id, for_update=True)
    changed_fields = [
        key for key, value in changes.items() if getattr(record, key) != value
    ]
    if changed_fields:
        for key in changed_fields:
            setattr(record, key, changes[key])
        record.save(update_fields=changed_fields + ["updated_at"])
        audit.record_event(
            workspace=context.workspace,
            actor=context.actor,
            action="client.updated",
            object_id=record.id,
            changed_fields=changed_fields,
        )
    return record
