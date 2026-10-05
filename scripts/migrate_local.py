"""Migrate allowlisted private databases using a separate owner connection."""

import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    dbname = sys.argv[1] if len(sys.argv) > 1 else "mygym_dev"
    if dbname not in {"mygym_dev", "mygym_test", "mygym_e2e"}:
        raise SystemExit("Only dedicated MyGym development databases are allowed.")
    state = json.loads((ROOT / ".local/database.json").read_text())
    env = os.environ | {
        "DB_NAME": dbname,
        "DB_USER": "mygym_migrator",
        "DB_PASSWORD": state["migrator"],
    }
    subprocess.run(
        [sys.executable, "manage.py", "migrate", "--noinput"],
        cwd=ROOT / "backend",
        env=env,
        check=True,
    )
    import psycopg

    with psycopg.connect(
        host="127.0.0.1",
        port=55432,
        dbname=dbname,
        user="mygym_migrator",
        password=state["migrator"],
    ) as conn:
        conn.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
        conn.execute("GRANT USAGE ON SCHEMA public TO mygym_runtime")
        conn.execute(
            "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mygym_runtime"
        )
        conn.execute(
            "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mygym_runtime"
        )
        conn.execute("REVOKE ALL ON django_migrations FROM mygym_runtime")
        conn.execute("GRANT SELECT ON django_migrations TO mygym_runtime")
        if conn.execute("SELECT to_regclass('audit_auditevent')").fetchone()[0]:
            conn.execute("REVOKE UPDATE, DELETE ON audit_auditevent FROM mygym_runtime")
        if conn.execute("SELECT to_regclass('clients_clientrecord')").fetchone()[0]:
            conn.execute("REVOKE DELETE ON clients_clientrecord FROM mygym_runtime")
        from psycopg import sql

        tables = conn.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' AND (tablename LIKE 'gym_%' OR tablename LIKE 'receivables_%')"
        ).fetchall()
        for (table,) in tables:
            immutable = table not in {"gym_plan", "gym_membership"}
            privileges = sql.SQL("UPDATE, DELETE" if immutable else "DELETE")
            conn.execute(
                sql.SQL("REVOKE {} ON {} FROM mygym_runtime").format(
                    privileges, sql.Identifier(table)
                )
            )
    print(f"Migrated {dbname}; runtime grants applied.")


if __name__ == "__main__":
    main()
