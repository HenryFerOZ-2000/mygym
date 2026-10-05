import uuid
import psycopg
from django.conf import settings


def test_application_context_commits_and_rolls_back_without_residual_state(
    django_db_blocker,
):
    from django.db import connection
    from tenancy.context import workspace_context

    with django_db_blocker.unblock():
        assert connection.get_autocommit()
        for fail in [False, True]:
            try:
                with workspace_context(uuid.uuid4()):
                    if fail:
                        raise ValueError("exercise rollback")
            except ValueError:
                pass
            assert connection.get_autocommit()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT nullif(current_setting('app.workspace_id', true), '')"
                )
                assert cursor.fetchone() == (None,)


def test_real_commit_rollback_and_connection_reuse_clear_local_setting():
    database = settings.DATABASES["default"]
    with psycopg.connect(
        host=database["HOST"],
        port=database["PORT"],
        dbname=database["NAME"],
        user=database["USER"],
        password=database["PASSWORD"],
        autocommit=True,
    ) as conn:
        assert conn.execute("SELECT current_user").fetchone()[0] == "mygym_runtime"
        for action in ["commit", "rollback"]:
            try:
                with conn.transaction():
                    conn.execute(
                        "SELECT set_config('app.workspace_id', %s, true)",
                        (str(uuid.uuid4()),),
                    )
                    if action == "rollback":
                        raise ValueError("rollback")
            except ValueError:
                pass
            assert (
                conn.execute(
                    "SELECT nullif(current_setting('app.workspace_id', true), '')"
                ).fetchone()[0]
                is None
            )
            assert (
                conn.execute("SELECT count(*) FROM clients_clientrecord").fetchone()[0]
                == 0
            )
            assert (
                conn.execute("SELECT count(*) FROM audit_auditevent").fetchone()[0] == 0
            )
