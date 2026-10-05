from .base import *  # noqa: F403

# Development is intentionally bound to loopback by the launcher.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
DEMO_ENABLED = True
