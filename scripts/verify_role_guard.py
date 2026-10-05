"""Verify runtime is accepted and the actual migration owner is rejected."""

import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
state = json.loads((ROOT / ".local/database.json").read_text())
runtime = subprocess.run(
    [sys.executable, str(ROOT / "scripts/check_runtime.py")],
    capture_output=True,
    text=True,
)
if runtime.returncode:
    raise SystemExit(
        "Runtime guard rejected the application role. Inspect configuration."
    )
owner_env = os.environ | {"DB_USER": "mygym_migrator", "DB_PASSWORD": state["migrator"]}
owner = subprocess.run(
    [sys.executable, str(ROOT / "scripts/check_runtime.py")],
    env=owner_env,
    capture_output=True,
    text=True,
)
if (
    owner.returncode == 0
    or "Runtime/table configuration does not enforce RLS" not in owner.stderr
):
    raise SystemExit("Guard did not reject migration owner as expected.")
print(
    "Real runtime accepted; real migration owner rejected. No privileged isolation test accepted."
)
