import json

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import Client, override_settings


@pytest.fixture
def build(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets/app-abc123.js").write_text("console.log('demo');")
    (tmp_path / "index.html").write_text(
        '<html><script type="module" src="/assets/app-abc123.js"></script></html>'
    )
    (tmp_path / ".vite").mkdir()
    (tmp_path / ".vite/manifest.json").write_text(
        json.dumps({"index.html": {"file": "assets/app-abc123.js", "isEntry": True}})
    )
    return tmp_path


def test_build_guard_rejects_missing_or_stale_assets(build):
    from config.local_delivery import validate_build

    validate_build(build)
    (build / "assets/app-abc123.js").unlink()
    with pytest.raises(ImproperlyConfigured):
        validate_build(build)


def test_local_config_rejects_cloud_debug_and_remote_database(monkeypatch):
    from config.local_delivery import validate_configuration

    with override_settings(
        DEBUG=False,
        DEPLOYMENT_MODE="LOCAL",
        ALLOWED_HOSTS=["127.0.0.1"],
        SESSION_COOKIE_SECURE=False,
        CSRF_COOKIE_SECURE=False,
    ):
        validate_configuration()
        with override_settings(DEBUG=True), pytest.raises(ImproperlyConfigured):
            validate_configuration()
        with (
            override_settings(DEPLOYMENT_MODE="CLOUD"),
            pytest.raises(ImproperlyConfigured),
        ):
            validate_configuration()
        with (
            override_settings(ALLOWED_HOSTS=["*"]),
            pytest.raises(ImproperlyConfigured),
        ):
            validate_configuration()
        from django.conf import settings

        with monkeypatch.context() as config:
            config.setitem(settings.DATABASES["default"], "HOST", "192.168.1.1")
            with pytest.raises(ImproperlyConfigured):
                validate_configuration()
        with override_settings(SECRET_KEY="short"), pytest.raises(ImproperlyConfigured):
            validate_configuration()


def test_spa_routes_assets_and_api_are_separate(build):
    with override_settings(ROOT_URLCONF="config.local_urls", LOCAL_FRONTEND_DIST=build):
        client = Client()
        for route in (
            "/",
            "/login",
            "/workspaces",
            "/workspaces/abc/clients",
            "/workspaces/abc/reports",
        ):
            response = client.get(route)
            assert response.status_code == 200
            assert response["Content-Type"].startswith("text/html")
            assert response["Cache-Control"] == "no-store"
        assert client.get("/api/v1/health/").json() == {"status": "ok"}
        for route in (
            "/api/missing",
            "/api",
            "/assets/missing.js",
            "/.env",
            "/unknown",
            "/assets/../index.html",
        ):
            assert client.get(route).status_code == 404
        response = client.get("/assets/app-abc123.js")
        assert response.status_code == 200
        assert b"console.log" in b"".join(response.streaming_content)
        assert response["X-Content-Type-Options"] == "nosniff"
        assert client.post("/login").status_code == 405


@pytest.mark.django_db
def test_preflight_checks_real_test_database_without_migration(build):
    from config.local_delivery import preflight

    with override_settings(
        DEBUG=False,
        DEPLOYMENT_MODE="LOCAL",
        ALLOWED_HOSTS=["127.0.0.1"],
        SESSION_COOKIE_SECURE=False,
        CSRF_COOKIE_SECURE=False,
        LOCAL_FRONTEND_DIST=build,
    ):
        preflight()


@pytest.mark.django_db
def test_preflight_refuses_pending_migrations(build, monkeypatch):
    from config.local_delivery import preflight
    from django.db.migrations.executor import MigrationExecutor

    monkeypatch.setattr(
        MigrationExecutor, "migration_plan", lambda *args: [("pending", False)]
    )
    with override_settings(
        DEBUG=False,
        DEPLOYMENT_MODE="LOCAL",
        ALLOWED_HOSTS=["127.0.0.1"],
        SESSION_COOKIE_SECURE=False,
        CSRF_COOKIE_SECURE=False,
        LOCAL_FRONTEND_DIST=build,
    ):
        with pytest.raises(ImproperlyConfigured, match="Pending migrations"):
            preflight()


def test_build_guard_rejects_manifest_escape(build):
    from config.local_delivery import validate_build

    manifest = build / ".vite/manifest.json"
    manifest.write_text(
        json.dumps({"index.html": {"file": "../private.js", "isEntry": True}})
    )
    with pytest.raises(ImproperlyConfigured):
        validate_build(build)
