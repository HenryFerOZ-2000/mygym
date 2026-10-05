import pytest
from django.db import transaction, DatabaseError


def test_audit_records_field_names_only_and_is_append_only(signed_api, workspaces):
    from modules.audit.models import AuditEvent
    from tenancy.context import workspace_context

    a = workspaces[0]
    response = signed_api.post(
        f"/api/v1/workspaces/{a.id}/clients/",
        {"full_name": "Sensitive Fictional Name", "phone": "0999999999"},
        format="json",
    )
    assert response.status_code == 201
    with workspace_context(a.id):
        event = AuditEvent.objects.get()
        assert set(event.changed_fields) == {"full_name", "phone"}
        assert "Sensitive" not in str(event.__dict__)
        assert "0999999999" not in str(event.__dict__)
        with pytest.raises(DatabaseError), transaction.atomic():
            AuditEvent.objects.filter(pk=event.pk).update(action="tampered")


def test_audit_failure_rolls_back_client(signed_api, workspaces, monkeypatch):
    from modules.clients.models import ClientRecord
    from modules.audit import services
    from tenancy.context import workspace_context

    a = workspaces[0]

    def fail(**kwargs):
        raise RuntimeError("simulated audit storage failure")

    # Inject failure at the real storage boundary, verify database side effect.
    monkeypatch.setattr(services, "record_event", fail)
    with pytest.raises(RuntimeError):
        signed_api.post(
            f"/api/v1/workspaces/{a.id}/clients/",
            {"full_name": "Must rollback"},
            format="json",
        )
    with workspace_context(a.id):
        assert ClientRecord.objects.count() == 0
