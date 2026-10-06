"""Independent recovery checks; never restores, activates, or exports business rows."""

import argparse
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from recovery.archive import ArchiveError, open_archive, seal_archive  # noqa: E402
from recovery.guards import RecoveryError, assert_backup_role, dump_arguments  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-check",
        action="store_true",
        help="Protect test schema only; no business rows, passwords or sessions.",
    )
    args = parser.parse_args()
    os.environ["DB_NAME"] = "mygym_test"
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.test"
    import django

    django.setup()
    from django.db import connection
    from tenancy.checks import assert_runtime_role

    config = connection.settings_dict
    if config["HOST"] != "127.0.0.1" or str(config["PORT"]) != "55432":
        raise RecoveryError(
            "Only the existing private loopback test cluster is admitted."
        )
    assert_runtime_role()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT current_database(), current_setting('server_version_num')::integer"
        )
        name, version = cursor.fetchone()
        if name != "mygym_test" or version // 10000 != 17:
            raise RecoveryError("Only PostgreSQL 17 on mygym_test is allowed.")
        cursor.execute(
            "SELECT current_user,rolsuper,rolbypassrls,rolcreatedb,rolcreaterole FROM pg_roles WHERE rolname=current_user"
        )
        role = cursor.fetchone()
    if not args.fixture_check:
        assert_backup_role(role)
        raise RecoveryError(
            "Full restoration is gated pending separately approved identities and destination."
        )
    binary = ROOT / ".local/pg17/pgsql/bin"
    config = connection.settings_dict
    env = os.environ | {
        "PGHOST": config["HOST"],
        "PGPORT": str(config["PORT"]),
        "PGUSER": config["USER"],
        "PGPASSWORD": config["PASSWORD"],
    }
    # Existing credentials are passed privately to the child; never command line/logs.
    command = dump_arguments(binary / "pg_dump.exe", "mygym_test") + ["--schema-only"]
    result = subprocess.run(command, env=env, capture_output=True, timeout=60)
    if result.returncode or result.stderr:
        raise RecoveryError("Schema fixture export failed; no archive was published.")
    from uuid import uuid4

    path = ROOT / ".local/recovery-fixtures" / (str(uuid4()) + ".mygym-recovery")
    seal_archive(path, result.stdout, source="mygym_test", postgres_major=17)
    recovered = open_archive(path)
    inspected = subprocess.run(
        [str(binary / "pg_restore.exe"), "--list"],
        input=recovered,
        env=env,
        capture_output=True,
        timeout=30,
    )
    if inspected.returncode or inspected.stderr:
        raise RecoveryError("Recovered fixture is not readable by PostgreSQL 17.")
    print(
        "PASS: test schema -> Windows-user protection -> decrypt -> PostgreSQL archive inspection."
    )
    print(
        "No business rows, authentication hashes or sessions exported. No database restored or activated."
    )
    print(
        "Encrypted schema fixture retained under .local/recovery-fixtures (ignored by Git)."
    )
    print(
        "BLOCKED: complete backup/restore needs separately approved database identities and a new test destination."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ArchiveError, RecoveryError) as error:
        print("Recovery check refused: " + str(error), file=sys.stderr)
        raise SystemExit(2)
    except subprocess.TimeoutExpired:
        print(
            "Recovery check refused: PostgreSQL operation timed out; no restore was attempted.",
            file=sys.stderr,
        )
        raise SystemExit(2)
