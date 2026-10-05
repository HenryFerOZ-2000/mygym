from .development import *  # noqa: F403

DATABASES["default"]["NAME"] = "mygym_test"  # noqa: F405
DATABASES["default"]["CONN_MAX_AGE"] = 0  # noqa: F405
# Production password hashing is retained, including the dummy-user path.
