from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.apps import apps


def assert_runtime_role():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname=current_user"
        )
        if any(cursor.fetchone()):
            raise ImproperlyConfigured("Runtime must not be superuser or BYPASSRLS.")
        tables = ["clients_clientrecord", "audit_auditevent"] + [
            model._meta.db_table
            for model in apps.get_models()
            if model._meta.app_label in {"gym", "receivables"}
        ]
        cursor.execute(
            """
            SELECT relname, relrowsecurity, relforcerowsecurity,
                   pg_has_role(current_user, relowner, 'MEMBER')
            FROM pg_class WHERE oid = ANY(ARRAY(SELECT unnest(%s::text[])::regclass))
        """,
            [tables],
        )
        rows = cursor.fetchall()
        if len(rows) != len(tables) or any(
            not rls or not force or owner for _, rls, force, owner in rows
        ):
            raise ImproperlyConfigured(
                "Runtime/table configuration does not enforce RLS."
            )
