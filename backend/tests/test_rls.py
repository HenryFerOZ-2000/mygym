import uuid

import pytest
from django.db import connection, transaction, DatabaseError

pytestmark = pytest.mark.django_db


def test_runtime_role_cannot_bypass_or_own_tables():
    from tenancy.checks import assert_runtime_role

    assert_runtime_role()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname=current_user"
        )
        assert cursor.fetchone() == (False, False)
        cursor.execute("SELECT pg_has_role(current_user, 'mygym_migrator', 'MEMBER')")
        assert cursor.fetchone() == (False,)


def test_without_context_reads_nothing_and_insert_fails(workspaces):
    from modules.clients.models import ClientRecord
    from modules.audit.models import AuditEvent

    assert ClientRecord.objects.count() == 0
    assert AuditEvent.objects.count() == 0
    with pytest.raises(DatabaseError), transaction.atomic():
        ClientRecord.objects.create(workspace=workspaces[0], full_name="Blocked")


def test_rls_blocks_cross_writes_and_reads(workspaces, operator):
    from tenancy.context import workspace_context
    from modules.clients.models import ClientRecord
    from modules.audit.models import AuditEvent

    a, b, _ = workspaces
    with workspace_context(a.id):
        record = ClientRecord.objects.create(workspace=a, full_name="A")
        AuditEvent.objects.create(
            workspace=a,
            actor=operator,
            action="created",
            object_id=record.id,
            changed_fields=["full_name"],
        )
        with pytest.raises(DatabaseError), transaction.atomic():
            ClientRecord.objects.create(workspace=b, full_name="B")
        with pytest.raises(DatabaseError), transaction.atomic():
            AuditEvent.objects.create(
                workspace=b,
                actor=operator,
                action="created",
                object_id=uuid.uuid4(),
                changed_fields=[],
            )
        with pytest.raises(DatabaseError), transaction.atomic():
            ClientRecord.objects.filter(pk=record.id).update(workspace=b)
    with workspace_context(b.id):
        assert not ClientRecord.objects.filter(pk=record.id).exists()
        assert ClientRecord.objects.filter(pk=record.id).update(full_name="stolen") == 0
        assert AuditEvent.objects.count() == 0


def test_context_restored_after_success_exception_and_nested_rejection(workspaces):
    from tenancy.context import workspace_context
    from modules.clients.models import ClientRecord

    a, b, _ = workspaces
    with workspace_context(a.id):
        ClientRecord.objects.create(workspace=a, full_name="A")
        with pytest.raises(RuntimeError):
            with workspace_context(b.id):
                pass
    assert ClientRecord.objects.count() == 0
    with pytest.raises(ValueError):
        with workspace_context(b.id):
            ClientRecord.objects.create(workspace=b, full_name="rollback")
            raise ValueError("rollback")
    assert ClientRecord.objects.count() == 0
    with workspace_context(b.id):
        assert ClientRecord.objects.count() == 0
    with workspace_context(a.id):
        assert ClientRecord.objects.count() == 1


def test_context_missing_is_blank_even_inside_outer_transaction(workspaces):
    from tenancy.context import workspace_context

    with workspace_context(workspaces[0].id):
        pass
    with connection.cursor() as cursor:
        cursor.execute("SELECT nullif(current_setting('app.workspace_id', true), '')")
        assert cursor.fetchone() == (None,)
