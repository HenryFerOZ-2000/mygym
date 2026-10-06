"""Checked Waitress entry point. Binds only to 127.0.0.1; no cloud dependency."""

import argparse
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Port must be between 1024 and 65535.")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.local"
    import django
    from django.core.exceptions import ImproperlyConfigured
    from django.db import DatabaseError, connections

    try:
        django.setup()
        from config.local_delivery import preflight

        preflight()
    except (ImproperlyConfigured, DatabaseError):
        # Database exceptions may contain credentials or infrastructure details.
        print(
            "Local preflight failed. Check configuration, frontend build, database availability, pending migrations and restricted RLS role. No migrations were applied.",
            file=sys.stderr,
        )
        return 1
    finally:
        connections.close_all()
    from waitress import serve
    from django.core.wsgi import get_wsgi_application

    if args.check:
        print("Local preflight OK: build, database, migrations and runtime RLS.")
        return 0
    print(f"MyGym Local: http://127.0.0.1:{args.port}", flush=True)
    serve(
        get_wsgi_application(),
        host="127.0.0.1",
        port=args.port,
        threads=4,
        clear_untrusted_proxy_headers=True,
        max_request_body_size=16384,
        expose_tracebacks=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
