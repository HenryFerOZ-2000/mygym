from .base import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = ["127.0.0.1"]
ROOT_URLCONF = "config.local_urls"
DEMO_ENABLED = False
# Plain HTTP is allowed only on the loopback address enforced by the launcher.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
LOCAL_FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"  # noqa: F405

# Ports do not isolate browser cookies; separate Local from the dev server.
SESSION_COOKIE_NAME = "mygym_local_sessionid"
CSRF_COOKIE_NAME = "mygym_local_csrftoken"
