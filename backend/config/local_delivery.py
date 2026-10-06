"""Loopback-only delivery checks. Never migrate or provision databases here."""

import json
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from tenancy.checks import assert_runtime_role


def validate_configuration():
    database = settings.DATABASES["default"]
    if (
        settings.DEBUG
        or settings.DEPLOYMENT_MODE != "LOCAL"
        or set(settings.ALLOWED_HOSTS) != {"127.0.0.1"}
        or database["ENGINE"] != "django.db.backends.postgresql"
        or database.get("HOST") != "127.0.0.1"
        or not database.get("NAME")
        or not database.get("USER")
        or not database.get("PASSWORD")
        or len(settings.SECRET_KEY) < 32
        or settings.SECRET_KEY.startswith("django-insecure-")
        or settings.SESSION_COOKIE_SECURE
        or settings.CSRF_COOKIE_SECURE
    ):
        raise ImproperlyConfigured(
            "Local requires non-debug LOCAL settings, PostgreSQL and HTTP on 127.0.0.1 only."
        )


def validate_build(dist):
    dist = Path(dist).resolve()
    try:
        manifest = json.loads(
            (dist / ".vite/manifest.json").read_text(encoding="utf-8")
        )
        index = (dist / "index.html").read_text(encoding="utf-8")
        entry = manifest["index.html"]
        if not entry.get("isEntry") or not manifest:
            raise ValueError
        for item in manifest.values():
            for name in [item["file"], *item.get("css", []), *item.get("assets", [])]:
                path = (dist / name).resolve()
                if not path.is_relative_to(dist / "assets") or not path.is_file():
                    raise ValueError
        if f"/{entry['file']}" not in index:
            raise ValueError
    except (OSError, ValueError, KeyError, TypeError):
        raise ImproperlyConfigured(
            "Frontend build missing or inconsistent. Run scripts/build-local.ps1."
        ) from None


def preflight():
    validate_configuration()
    validate_build(settings.LOCAL_FRONTEND_DIST)
    connection.ensure_connection()
    executor = MigrationExecutor(connection)
    if executor.migration_plan(executor.loader.graph.leaf_nodes()):
        raise ImproperlyConfigured(
            "Pending migrations. Stop and coordinate a backup and migration before starting Local."
        )
    assert_runtime_role()
