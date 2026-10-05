"""Provision ONLY this project's private development cluster and databases."""

import json
import os
from pathlib import Path
import secrets
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / ".local"
BIN = PRIVATE / "pg17" / "pgsql" / "bin"
DATA = PRIVATE / "pgdata"
STATE = PRIVATE / "database.json"


def main():
    PRIVATE.mkdir(exist_ok=True)
    # Restrict inherited access before storing passwords/cluster data on Windows.
    if os.name == "nt":
        account = subprocess.check_output(["whoami"], text=True).strip()
        subprocess.run(
            [
                "icacls",
                str(PRIVATE),
                "/inheritance:r",
                "/grant:r",
                f"{account}:(OI)(CI)F",
                "SYSTEM:(OI)(CI)F",
            ],
            check=True,
            capture_output=True,
        )
    if STATE.exists():
        state = json.loads(STATE.read_text())
    else:
        state = {
            key: secrets.token_urlsafe(36)
            for key in ["admin", "migrator", "runtime", "secret"]
        }
        STATE.write_text(json.dumps(state), encoding="utf-8")
    if not DATA.exists():
        password_file = PRIVATE / "init-password"
        password_file.write_text(state["admin"], encoding="utf-8")
        try:
            subprocess.run(
                [
                    str(BIN / "initdb.exe"),
                    "-D",
                    str(DATA),
                    "-U",
                    "mygym_admin",
                    "--encoding=UTF8",
                    "--locale=C",
                    "--auth=scram-sha-256",
                    f"--pwfile={password_file}",
                ],
                check=True,
            )
        finally:
            password_file.unlink(missing_ok=True)
        with (DATA / "postgresql.conf").open("a", encoding="utf-8") as f:
            f.write(
                "\nlisten_addresses = '127.0.0.1'\nport = 55432\nlog_statement = 'none'\nlog_min_error_statement = 'panic'\n"
            )
    status = subprocess.run(
        [str(BIN / "pg_ctl.exe"), "-D", str(DATA), "status"], capture_output=True
    )
    if status.returncode:
        subprocess.run(
            [
                str(BIN / "pg_ctl.exe"),
                "-D",
                str(DATA),
                "-l",
                str(PRIVATE / "postgres.log"),
                "-w",
                "start",
            ],
            check=True,
        )
    import psycopg
    from psycopg import sql

    with psycopg.connect(
        host="127.0.0.1",
        port=55432,
        dbname="postgres",
        user="mygym_admin",
        password=state["admin"],
        autocommit=True,
    ) as conn:
        for role, key in [("mygym_migrator", "migrator"), ("mygym_runtime", "runtime")]:
            if not conn.execute(
                "SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)
            ).fetchone():
                conn.execute(
                    sql.SQL(
                        "CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOINHERIT"
                    ).format(sql.Identifier(role), sql.Literal(state[key]))
                )
        for dbname in ["mygym_dev", "mygym_test", "mygym_e2e"]:
            if not conn.execute(
                "SELECT 1 FROM pg_database WHERE datname=%s", (dbname,)
            ).fetchone():
                conn.execute(
                    sql.SQL("CREATE DATABASE {} OWNER mygym_migrator").format(
                        sql.Identifier(dbname)
                    )
                )
            conn.execute(
                sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(
                    sql.Identifier(dbname)
                )
            )
            conn.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO mygym_runtime").format(
                    sql.Identifier(dbname)
                )
            )
    env_path = ROOT / ".env"
    if not env_path.exists():
        env_path.write_text(
            f"DJANGO_SECRET_KEY={state['secret']}\nDB_HOST=127.0.0.1\nDB_PORT=55432\nDB_NAME=mygym_dev\nDB_USER=mygym_runtime\nDB_PASSWORD={state['runtime']}\nDEPLOYMENT_MODE=LOCAL\n",
            encoding="utf-8",
        )
        if os.name == "nt":
            subprocess.run(
                [
                    "icacls",
                    str(env_path),
                    "/inheritance:r",
                    "/grant:r",
                    f"{account}:F",
                    "SYSTEM:F",
                ],
                check=True,
                capture_output=True,
            )
    print(
        "Private PostgreSQL ready on loopback:55432. Secrets stored privately; no credentials printed."
    )


if __name__ == "__main__":
    main()
