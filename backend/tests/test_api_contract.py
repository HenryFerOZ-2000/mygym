from django.conf import settings
from drf_spectacular.generators import SchemaGenerator
from conftest import csrf


def test_openapi_includes_all_routes_and_error_responses():
    schema = SchemaGenerator().get_schema(request=None, public=True)
    assert "/api/v1/health/" in schema["paths"]
    assert len(schema["paths"]) == 27
    prefix = "/api/v1/workspaces/{workspace_id}/"
    assert prefix + "gym/plans/" in schema["paths"]
    assert prefix + "clients/{client_id}/gym/memberships/" in schema["paths"]
    assert (
        prefix + "clients/{client_id}/receivables/payments/{payment_id}/refunds/"
        in schema["paths"]
    )
    responses = schema["paths"]["/api/v1/workspaces/{workspace_id}/clients/"]["post"][
        "responses"
    ]
    assert {"201", "400", "403", "404"} <= set(responses)


def test_oversize_json_and_method_errors_are_json(api):
    csrf(api)
    response = api.post(
        "/api/v1/auth/login/",
        {"username": "a", "password": "x" * (settings.DATA_UPLOAD_MAX_MEMORY_SIZE + 1)},
        format="json",
    )
    assert response.status_code == 400
    assert response["Content-Type"].startswith("application/json")
    response = api.post("/api/v1/health/", {}, format="json")
    assert response.status_code == 405
    assert response["Content-Type"].startswith("application/json")


def test_private_response_not_cached(signed_api):
    response = signed_api.get("/api/v1/auth/me/")
    assert "no-store" in response["Cache-Control"]
