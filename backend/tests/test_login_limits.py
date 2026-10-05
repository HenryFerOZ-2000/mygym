from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
import uuid

from django.test import override_settings
from django.utils import timezone
from conftest import csrf


@override_settings(LOGIN_ACCOUNT_LIMIT=3, LOGIN_ORIGIN_LIMIT=100)
def test_concurrent_failures_are_serialized_in_postgresql(django_db_blocker):
    from django.db import connections
    from django.test import RequestFactory
    from django.utils.crypto import salted_hmac
    from modules.identity.login_limits import authenticate_limited
    from modules.identity.models import LoginAttempt

    username = "concurrency-" + uuid.uuid4().hex
    origin = "test-origin-" + uuid.uuid4().hex
    keys = [
        salted_hmac("mygym.login.account", username, algorithm="sha256").hexdigest(),
        salted_hmac("mygym.login.origin", origin, algorithm="sha256").hexdigest(),
    ]

    def attempt(_):
        try:
            request = RequestFactory().post("/api/v1/auth/login/", REMOTE_ADDR=origin)
            return authenticate_limited(request, username, "wrong-test-password")
        finally:
            connections.close_all()

    with django_db_blocker.unblock():
        try:
            with ThreadPoolExecutor(max_workers=4) as pool:
                assert list(pool.map(attempt, range(8))) == [None] * 8
            assert LoginAttempt.objects.get(key=keys[0]).failures == 3
            assert LoginAttempt.objects.get(key=keys[1]).failures == 3
        finally:
            LoginAttempt.objects.filter(key__in=keys).delete()


@override_settings(LOGIN_ACCOUNT_LIMIT=1)
def test_limit_expires_and_does_not_store_identity_in_clear(api, operator):
    from modules.identity.models import LoginAttempt

    csrf(api)
    api.post(
        "/api/v1/auth/login/",
        {"username": operator.username, "password": "wrong"},
        format="json",
    )
    assert (
        api.post(
            "/api/v1/auth/login/",
            {"username": operator.username, "password": "testing-only-passphrase"},
            format="json",
        ).status_code
        == 400
    )
    assert all(
        len(key) == 64 and "operator" not in key
        for key in LoginAttempt.objects.values_list("key", flat=True)
    )
    LoginAttempt.objects.update(window_start=timezone.now() - timedelta(minutes=16))
    assert (
        api.post(
            "/api/v1/auth/login/",
            {"username": operator.username, "password": "testing-only-passphrase"},
            format="json",
        ).status_code
        == 200
    )


@override_settings(LOGIN_ORIGIN_LIMIT=2)
def test_origin_limit_blocks_username_rotation(api, operator):
    csrf(api)
    for username in ["missing-a", "missing-b"]:
        assert (
            api.post(
                "/api/v1/auth/login/",
                {"username": username, "password": "wrong"},
                format="json",
            ).status_code
            == 400
        )
    assert (
        api.post(
            "/api/v1/auth/login/",
            {"username": operator.username, "password": "testing-only-passphrase"},
            format="json",
        ).status_code
        == 400
    )
