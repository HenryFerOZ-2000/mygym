import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings

from conftest import csrf

pytestmark = pytest.mark.django_db


def test_marked_demo_account_cannot_login_or_keep_session_outside_demo(api, operator):
    operator.groups.add(Group.objects.create(name="mygym_demo_only"))
    csrf(api)
    payload = {"username": operator.username, "password": "testing-only-passphrase"}
    assert api.post("/api/v1/auth/login/", payload, format="json").status_code == 200
    with override_settings(DEMO_ENABLED=False):
        assert api.get("/api/v1/auth/me/").status_code == 403
        csrf(api)
        assert (
            api.post("/api/v1/auth/login/", payload, format="json").status_code == 400
        )


def test_prepare_admin_requires_fictional_confirmation_and_demo_profile():
    with pytest.raises(CommandError):
        call_command("prepare_demo_admin")
    with override_settings(DEMO_ENABLED=False), pytest.raises(CommandError):
        call_command("prepare_demo_admin", confirm_fictional=True)


def test_prepare_admin_creates_owner_without_global_privileges(monkeypatch):
    monkeypatch.setenv("MYGYM_DEMO_PASSWORD", "fictional-seed-testing-passphrase")
    call_command("seed_demo")
    # mygym_test retains baseline fixtures. Scope only the inventory reads to
    # these real seeded rows; account/password/access writes remain real SQL
    # inside the rollback transaction. Production inventory guards are intact.
    from modules.workspaces.models import Workspace
    from modules.workspaces.management.commands.seed_demo import NAMESPACE
    import uuid

    demo_ids = [uuid.uuid5(NAMESPACE, name) for name in ("Gym Titan", "Gym Aurora")]
    monkeypatch.setattr(
        Workspace.objects, "all", lambda: Workspace.objects.filter(id__in=demo_ids)
    )
    user_manager = get_user_model().objects
    original_exclude = user_manager.exclude
    demo_users = list(
        user_manager.filter(
            username__in=["demo.owner", "demo.reception", "demo.coach"]
        ).values_list("pk", flat=True)
    )
    monkeypatch.setattr(
        user_manager,
        "exclude",
        lambda *args, **kwargs: original_exclude(*args, **kwargs).filter(
            pk__in=demo_users
        ),
    )
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("getpass.getpass", lambda *args: "fixture-testing-passphrase")
    call_command("prepare_demo_admin", confirm_fictional=True)
    user = get_user_model().objects.get(username="admin")
    assert not user.is_superuser and not user.is_staff
    assert user.groups.filter(name="mygym_demo_only").exists()
    assert user.workspaceaccess_set.filter(role="OWNER").count() == 2
    original = user.password
    with pytest.raises(CommandError):
        call_command("prepare_demo_admin", confirm_fictional=True)
    user.refresh_from_db()
    assert user.password == original


def test_prepare_admin_does_not_modify_existing_identity(operator):
    operator.username = "admin"
    operator.save()
    with pytest.raises(CommandError):
        call_command("prepare_demo_admin", confirm_fictional=True)
