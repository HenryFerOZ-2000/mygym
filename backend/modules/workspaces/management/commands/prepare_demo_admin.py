"""Interactive, explicitly confirmed fictional demo identity; never resets users."""

import getpass
import sys
import uuid
import warnings

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from modules.identity.demo_access import DEMO_GROUP
from modules.workspaces.models import Workspace, WorkspaceAccess
from .seed_demo import NAMESPACE


class Command(BaseCommand):
    help = "Prepare one admin operator only in a confirmed fictional demo. Password is entered privately and never defaults."

    def add_arguments(self, parser):
        parser.add_argument("--confirm-fictional", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        if (
            not options["confirm_fictional"]
            or not getattr(settings, "DEMO_ENABLED", False)
            or settings.DATABASES["default"]["NAME"]
            not in {"mygym_dev", "mygym_test", "mygym_e2e"}
        ):
            raise CommandError(
                "Requires a dedicated demo profile/database and explicit --confirm-fictional. Never use on real data."
            )
        User = get_user_model()
        if User.objects.filter(username="admin").exists():
            raise CommandError(
                "Username admin already exists; no account or password was modified."
            )
        expected = {
            uuid.uuid5(NAMESPACE, name): name for name in ("Gym Titan", "Gym Aurora")
        }
        workspaces = list(Workspace.objects.all())
        if len(workspaces) != 2 or any(
            expected.get(space.id) != space.name for space in workspaces
        ):
            raise CommandError(
                "Requires exactly the two fictional seeded demo workspaces."
            )
        if User.objects.exclude(
            username__in=["demo.owner", "demo.reception", "demo.coach"]
        ).exists():
            raise CommandError("Non-demo identities found. No account was created.")
        if not sys.stdin.isatty():
            raise CommandError(
                "Run in an interactive local terminal; passwords cannot be supplied by command line or environment."
            )
        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            try:
                password = getpass.getpass(
                    "Contraseña del administrador DEMO (oculta): "
                )
                confirmation = getpass.getpass("Confirma la contraseña DEMO (oculta): ")
            except (getpass.GetPassWarning, EOFError):
                raise CommandError(
                    "Secure password entry unavailable; nothing was created."
                ) from None
        if not password or password != confirmation:
            raise CommandError(
                "Password empty or confirmation differs; nothing was created."
            )
        # Demo-only weak input is permitted by explicit fictional confirmation.
        # Global password validators remain unchanged; this identity is blocked
        # by login and session middleware when DEMO_ENABLED is false.
        user = User.objects.create_user(username="admin", password=password)
        group, _ = Group.objects.get_or_create(name=DEMO_GROUP)
        user.groups.add(group)
        for workspace in workspaces:
            WorkspaceAccess.objects.create(user=user, workspace=workspace, role="OWNER")
        self.stdout.write(
            "Demo admin prepared as workspace OWNER, without Django staff/superuser access. Password not printed. Existing accounts preserved."
        )
