from django.test import override_settings
from conftest import csrf


def test_health_is_minimal(api):
    response = api.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_requires_csrf_even_without_session(api, operator):
    response = api.post(
        "/api/v1/auth/login/",
        {"username": operator.username, "password": "testing-only-passphrase"},
        format="json",
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "csrf_failed"


def test_session_logout_revokes_access(signed_api):
    assert signed_api.get("/api/v1/auth/me/").json()["username"] == "operator"
    assert signed_api.cookies["sessionid"]["httponly"]
    assert signed_api.post("/api/v1/auth/logout/", {}, format="json").status_code == 200
    assert signed_api.get("/api/v1/auth/me/").status_code == 403


def test_logout_requires_csrf(signed_api):
    signed_api.credentials()
    assert signed_api.post("/api/v1/auth/logout/", {}, format="json").status_code == 403
    assert signed_api.get("/api/v1/auth/me/").status_code == 200


def test_invalid_unknown_and_inactive_are_generic(api, operator):
    csrf(api)
    responses = []
    for username in [operator.username, "missing"]:
        responses.append(
            api.post(
                "/api/v1/auth/login/",
                {"username": username, "password": "wrong"},
                format="json",
            )
        )
    operator.is_active = False
    operator.save()
    responses.append(
        api.post(
            "/api/v1/auth/login/",
            {"username": operator.username, "password": "testing-only-passphrase"},
            format="json",
        )
    )
    assert {r.status_code for r in responses} == {400}
    assert responses[0].json() == responses[1].json() == responses[2].json()


@override_settings(LOGIN_ACCOUNT_LIMIT=2)
def test_login_limit_blocks_even_correct_password(api, operator):
    csrf(api)
    for _ in range(2):
        assert (
            api.post(
                "/api/v1/auth/login/",
                {"username": operator.username, "password": "wrong"},
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


def test_anonymous_and_invalid_json_are_json(api):
    assert api.get("/api/v1/auth/me/").status_code == 403
    csrf(api)
    response = api.post(
        "/api/v1/auth/login/", "{broken", content_type="application/json"
    )
    assert response.status_code == 400
    assert "error" in response.json()
