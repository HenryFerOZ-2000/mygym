"""Run browser acceptance against a separate real PostgreSQL database."""

import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", 8000)) == 0:
            raise SystemExit(
                "Port 8000 is in use. Stop the development backend before browser tests."
            )
    credentials = json.loads((ROOT / ".local/mygym_e2e-demo.json").read_text())
    env = os.environ | {
        "DB_NAME": "mygym_e2e",
        "MYGYM_E2E_PASSWORD": credentials["password"],
    }
    env.pop("NO_COLOR", None)
    with (ROOT / ".local/e2e-backend.log").open("w", encoding="utf-8") as log:
        backend = subprocess.Popen(
            [sys.executable, "manage.py", "runserver", "127.0.0.1:8000", "--noreload"],
            cwd=ROOT / "backend",
            env=env,
            stdout=log,
            stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            for _ in range(100):
                if backend.poll() is not None:
                    raise RuntimeError(
                        "E2E backend failed; inspect .local/e2e-backend.log"
                    )
                try:
                    urllib.request.urlopen(
                        "http://127.0.0.1:8000/api/v1/health/", timeout=1
                    ).close()
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("E2E backend readiness timeout.")
            result = subprocess.run(
                [
                    shutil.which("npm.cmd") or "npm",
                    "run",
                    "test:e2e",
                    "--",
                    *sys.argv[1:],
                ],
                cwd=ROOT / "frontend",
                env=env,
            )
        finally:
            backend.terminate()
            backend.wait(timeout=10)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
