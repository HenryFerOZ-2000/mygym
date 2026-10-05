from contextlib import contextmanager
from contextvars import ContextVar
from uuid import UUID
from django.db import connection, transaction
from .checks import assert_runtime_role

_active_workspace = ContextVar("active_workspace", default=None)


@contextmanager
def workspace_context(workspace_id):
    workspace_id = str(UUID(str(workspace_id)))
    active = _active_workspace.get()
    if active is not None:
        if active != workspace_id:
            raise RuntimeError("Cross-workspace nested contexts are forbidden.")
        with transaction.atomic():
            yield
        return
    assert_runtime_role()
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT nullif(current_setting('app.workspace_id', true), '')"
            )
            if cursor.fetchone()[0] is not None:
                raise RuntimeError("Residual database workspace context detected.")
            cursor.execute(
                "SELECT set_config('app.workspace_id', %s, true)", [workspace_id]
            )
        token = _active_workspace.set(workspace_id)
        try:
            # Savepoint restores database usability before clearing context on error.
            with transaction.atomic():
                yield
        finally:
            _active_workspace.reset(token)
            with connection.cursor() as cursor:
                cursor.execute("SELECT set_config('app.workspace_id', '', true)")
