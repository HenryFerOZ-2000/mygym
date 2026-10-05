"""Seed fictional local data, keeping generated credentials in the private folder."""

import json
import os
from pathlib import Path
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
dbname = sys.argv[1] if len(sys.argv) > 1 else "mygym_dev"
if dbname not in {"mygym_dev", "mygym_e2e"}:
    raise SystemExit("Only development/e2e demo databases allowed.")
credential_file = ROOT / ".local" / f"{dbname}-demo.json"
if credential_file.exists():
    credentials = json.loads(credential_file.read_text())
else:
    credentials = {"username": "demo.owner", "password": secrets.token_urlsafe(20)}
    credential_file.write_text(json.dumps(credentials), encoding="utf-8")
env = os.environ | {"DB_NAME": dbname, "MYGYM_DEMO_PASSWORD": credentials["password"]}
subprocess.run(
    [sys.executable, "manage.py", "seed_demo"],
    cwd=ROOT / "backend",
    env=env,
    check=True,
)
print(f"Credentials stored in .local/{dbname}-demo.json; never printed or committed.")
