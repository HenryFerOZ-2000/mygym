from .models import AuditEvent


def record_event(*, workspace, actor, action, object_id, changed_fields):
    return AuditEvent.objects.create(
        workspace=workspace,
        actor=actor,
        action=action,
        object_id=object_id,
        changed_fields=sorted(changed_fields),
    )
