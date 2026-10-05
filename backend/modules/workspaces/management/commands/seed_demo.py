import getpass
import os
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from modules.clients.models import ClientRecord
from modules.clients.services import create_client
from modules.workspaces.models import Workspace, WorkspaceAccess, WorkspaceCapability
from modules.workspaces.policies import WorkspaceContext
from tenancy.context import workspace_context

NAMESPACE = uuid.UUID("aefb84a5-28db-442d-a451-79b95b58ed15")


class Command(BaseCommand):
    help = "Create non-destructive fictional development data; never resets existing users."

    @transaction.atomic
    def handle(self, *args, **options):
        if not getattr(settings, "DEMO_ENABLED", False) or settings.DATABASES[
            "default"
        ]["NAME"] not in {"mygym_dev", "mygym_test", "mygym_e2e"}:
            raise CommandError(
                "Demo is only permitted in dedicated development databases."
            )
        User = get_user_model()
        names = ["demo.owner", "demo.reception", "demo.coach"]
        password = None
        if User.objects.filter(username__in=names).count() < 3:
            password = os.environ.get("MYGYM_DEMO_PASSWORD") or getpass.getpass(
                "Nueva contraseña demo (no se muestra): "
            )
            try:
                validate_password(password)
            except ValidationError as exc:
                raise CommandError(
                    "Use a strong demo password of at least 12 characters."
                ) from exc
        users = {}
        for username in names:
            user = User.objects.filter(username=username).first()
            if user is None:
                user = User.objects.create_user(username=username, password=password)
            users[username] = user
        for name in ["Gym Titan", "Gym Aurora"]:
            workspace, _ = Workspace.objects.get_or_create(
                id=uuid.uuid5(NAMESPACE, name), defaults={"name": name}
            )
            for username, role in [
                ("demo.owner", "OWNER"),
                ("demo.reception", "RECEPTION"),
                ("demo.coach", "COACH"),
            ]:
                WorkspaceAccess.objects.get_or_create(
                    workspace=workspace, user=users[username], defaults={"role": role}
                )
            WorkspaceCapability.objects.get_or_create(
                workspace=workspace, code="clients.manage", defaults={"enabled": True}
            )
            for code in (
                "gym.manage",
                "receivables.manage",
                "gym.attendance",
                "gym.reports",
                "receivables.reports",
            ):
                WorkspaceCapability.objects.get_or_create(
                    workspace=workspace, code=code, defaults={"enabled": True}
                )
            with workspace_context(workspace.id):
                context = WorkspaceContext(
                    workspace=workspace, actor=users["demo.owner"]
                )
                for full_name in ["Ana Ejemplo", "Luis Ejemplo", "Carla Ejemplo"]:
                    record_id = uuid.uuid5(NAMESPACE, name + "/" + full_name)
                    if not ClientRecord.objects.filter(pk=record_id).exists():
                        create_client(
                            context, {"id": record_id, "full_name": full_name}
                        )
        self.stdout.write(
            "Demo preparada. Usuarios: demo.owner, demo.reception, demo.coach. Claves existentes conservadas."
        )
