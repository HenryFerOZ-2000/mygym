"""Fail before starting application data work if PostgreSQL privileges bypass RLS."""

import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
import django

django.setup()
from tenancy.checks import assert_runtime_role  # noqa: E402

assert_runtime_role()
print("Runtime role restricted; RLS enabled and forced on all protected business tables.")
