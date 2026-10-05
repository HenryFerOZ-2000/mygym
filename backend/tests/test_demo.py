import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.auth import get_user_model
from django.test import override_settings

pytestmark = pytest.mark.django_db


def test_demo_idempotent_preserves_password_and_edits(monkeypatch):
    from modules.workspaces.models import Workspace, WorkspaceAccess
    from modules.clients.models import ClientRecord
    from tenancy.context import workspace_context

    monkeypatch.setenv("MYGYM_DEMO_PASSWORD", "randomly-provided-testing-passphrase")
    call_command("seed_demo")
    user = get_user_model().objects.get(username="demo.owner")
    original_hash = user.password
    workspace = Workspace.objects.get(name="Gym Titan")
    with workspace_context(workspace.id):
        record = ClientRecord.objects.first()
        record.full_name = "Edited by operator"
        record.save()
        count = ClientRecord.objects.count()
    monkeypatch.setenv("MYGYM_DEMO_PASSWORD", "different-testing-passphrase")
    call_command("seed_demo")
    user.refresh_from_db()
    assert user.password == original_hash
    assert Workspace.objects.filter(name__in=["Gym Titan", "Gym Aurora"]).count() == 2
    assert WorkspaceAccess.objects.filter(user=user).count() == 2
    with workspace_context(workspace.id):
        assert ClientRecord.objects.count() == count
        assert ClientRecord.objects.filter(full_name="Edited by operator").exists()


@override_settings(DEMO_ENABLED=False)
def test_demo_forbidden_outside_development():
    with pytest.raises(CommandError):
        call_command("seed_demo")
