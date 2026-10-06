"""Browser regression against the compiled UI and Waitress, only on mygym_e2e."""

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
        if probe.connect_ex(("127.0.0.1", 8766)) == 0:
            raise SystemExit("Port 8766 is in use. No process was stopped.")
    credentials = json.loads((ROOT / ".local/mygym_e2e-demo.json").read_text())
    env = os.environ | {
        "DB_NAME": "mygym_e2e",
        "MYGYM_E2E_PASSWORD": credentials["password"],
    }
    env.pop("NO_COLOR", None)
    with (ROOT / ".local/local-e2e-server.log").open("w", encoding="utf-8") as log:
        server = subprocess.Popen(
            [sys.executable, str(ROOT / "scripts/serve_local.py"), "--port", "8766"],
            cwd=ROOT,
            env=env,
            stdout=log,
            stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            for _ in range(100):
                if server.poll() is not None:
                    raise RuntimeError(
                        "Local E2E preflight failed. Inspect .local/local-e2e-server.log."
                    )
                try:
                    urllib.request.urlopen(
                        "http://127.0.0.1:8766/api/v1/health/", timeout=1
                    ).close()
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("Local E2E readiness timeout.")
            result = subprocess.run(
                [
                    shutil.which("npm.cmd") or "npm",
                    "run",
                    "test:e2e",
                    "--",
                    "--config",
                    "playwright.local.config.ts",
                    *sys.argv[1:],
                ],
                cwd=ROOT / "frontend",
                env=env,
            )
        finally:
            server.terminate()
            server.wait(timeout=10)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
