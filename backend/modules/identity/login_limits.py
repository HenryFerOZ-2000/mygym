from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.db import connection, transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac

from .models import LoginAttempt


def authenticate_limited(request, username, password):
    """Serialize counters in PostgreSQL; persist failures even on rejected login."""
    account_key = salted_hmac(
        "mygym.login.account", username.casefold(), algorithm="sha256"
    ).hexdigest()
    origin_key = salted_hmac(
        "mygym.login.origin", request.META.get("REMOTE_ADDR", ""), algorithm="sha256"
    ).hexdigest()
    limits = {
        account_key: settings.LOGIN_ACCOUNT_LIMIT,
        origin_key: settings.LOGIN_ORIGIN_LIMIT,
    }
    now = timezone.now()
    with transaction.atomic():
        for key in sorted(limits):
            # Order prevents deadlocks when concurrent attempts share an origin.
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_xact_lock(%s)", (int(key[:15], 16),))
        rows = []
        for key, limit in limits.items():
            row, _ = LoginAttempt.objects.get_or_create(
                key=key, defaults={"window_start": now}
            )
            if row.window_start <= now - timedelta(
                seconds=settings.LOGIN_WINDOW_SECONDS
            ):
                row.failures = 0
                row.window_start = now
            rows.append(row)
        if any(row.failures >= limits[row.key] for row in rows):
            return None
        user = authenticate(request, username=username, password=password)
        for row in rows:
            if user is None:
                row.failures += 1
            elif row.key == account_key:
                row.failures = 0
            row.save(update_fields=["failures", "window_start"])
        return user
