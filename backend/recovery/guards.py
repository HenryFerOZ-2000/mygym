"""Fail-closed rehearsal guards. These functions never grant database privileges."""

import re


class RecoveryError(ValueError):
    pass


def validate_source(name):
    if name != "mygym_test":
        raise RecoveryError(
            "Only mygym_test fixtures are allowed; active databases are forbidden."
        )


def assert_backup_role(role):
    name, superuser, bypass, createdb, createrole = role
    if (
        name in {"mygym_admin", "mygym_runtime", "mygym_migrator"}
        or superuser
        or not bypass
        or createdb
        or createrole
    ):
        raise RecoveryError(
            "Requires a separately approved, non-superuser backup identity; no roles were changed."
        )


def assert_empty_destination(connection, name):
    if not re.fullmatch(r"mygym_restore_test_[a-z0-9]{8,32}", name):
        raise RecoveryError(
            "Destination must be a separately provisioned new rehearsal database."
        )
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT current_database(), current_setting('server_version_num')::integer"
        )
        actual, version = cursor.fetchone()
        if actual != name or version // 10000 != 17:
            raise RecoveryError(
                "Destination identity or PostgreSQL version does not match."
            )
        cursor.execute(
            "SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()"
        )
        if cursor.fetchone()[0]:
            raise RecoveryError(
                "Destination has other connections; no sessions were terminated."
            )
        cursor.execute(
            "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname NOT IN ('pg_catalog','information_schema') AND n.nspname NOT LIKE 'pg_toast%' AND n.nspname NOT LIKE 'pg_temp%'"
        )
        if cursor.fetchone()[0]:
            raise RecoveryError(
                "Destination is occupied; nothing was deleted or overwritten."
            )
        cursor.execute(
            "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname NOT IN ('pg_catalog','information_schema')"
        )
        if cursor.fetchone()[0]:
            raise RecoveryError(
                "Destination contains user functions; nothing was overwritten."
            )


def dump_arguments(executable, name):
    validate_source(name)
    return [
        str(executable),
        "--dbname=" + name,
        "--format=custom",
        "--no-owner",
        "--no-privileges",
        "--no-password",
        "--exclude-table-data=public.django_session",
    ]


def restore_arguments(executable, name):
    if not re.fullmatch(r"mygym_restore_test_[a-z0-9]{8,32}", name):
        raise RecoveryError("Invalid isolated destination.")
    return [
        str(executable),
        "--dbname=" + name,
        "--single-transaction",
        "--exit-on-error",
        "--no-owner",
        "--no-privileges",
        "--no-password",
    ]


def invalidate_restored_sessions(connection):
    # Caller must keep this and integrity checks inside the same transaction.
    if not connection.in_atomic_block:
        raise RecoveryError(
            "Session invalidation requires the recovery validation transaction."
        )
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database()")
        name = cursor.fetchone()[0]
        if name != "mygym_test" and not re.fullmatch(
            r"mygym_restore_test_[a-z0-9]{8,32}", name
        ):
            raise RecoveryError(
                "Session purge is restricted to isolated rehearsal databases."
            )
        cursor.execute("DELETE FROM django_session")
