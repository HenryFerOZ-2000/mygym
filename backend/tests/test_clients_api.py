import pytest


def url(workspace, suffix=""):
    return f"/api/v1/workspaces/{workspace.id}/clients/{suffix}"


def test_create_edit_and_deactivate_without_contact(signed_api, workspaces):
    a = workspaces[0]
    response = signed_api.post(url(a), {"full_name": "  Ana Ejemplo  "}, format="json")
    assert response.status_code == 201
    record = response.json()
    assert record["full_name"] == "Ana Ejemplo"
    assert record["email"] == record["phone"] == ""
    assert "user" not in record
    detail = url(a, record["id"] + "/")
    response = signed_api.patch(detail, {"is_active": False}, format="json")
    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert signed_api.get(detail).status_code == 200
    assert signed_api.delete(detail).status_code == 405


@pytest.mark.parametrize(
    "field",
    [
        "workspace",
        "workspace_id",
        "user",
        "user_id",
        "role",
        "unknown",
        "id",
        "created_at",
    ],
)
def test_forbidden_fields_rejected_on_create_and_patch(signed_api, workspaces, field):
    a, b, _ = workspaces
    response = signed_api.post(
        url(a), {"full_name": "Ana", field: str(b.id)}, format="json"
    )
    assert response.status_code == 400
    created = signed_api.post(url(a), {"full_name": "Ana"}, format="json").json()
    assert (
        signed_api.patch(
            url(a, created["id"] + "/"), {field: str(b.id)}, format="json"
        ).status_code
        == 400
    )


def test_cross_workspace_object_and_list_isolation(signed_api, workspaces):
    a, b, outsider = workspaces
    record = signed_api.post(url(b), {"full_name": "Sólo B"}, format="json").json()
    assert signed_api.get(url(a)).json()["count"] == 0
    assert signed_api.get(url(b)).json()["count"] == 1
    wrong = url(a, record["id"] + "/")
    assert signed_api.get(wrong).status_code == 404
    assert (
        signed_api.patch(wrong, {"full_name": "Ataque"}, format="json").status_code
        == 404
    )
    assert (
        signed_api.post(
            url(outsider), {"full_name": "Ataque"}, format="json"
        ).status_code
        == 404
    )
    assert signed_api.get(url(b, record["id"] + "/")).json()["full_name"] == "Sólo B"


def test_same_email_does_not_merge_or_link(signed_api, workspaces):
    records = [
        signed_api.post(
            url(w),
            {"full_name": "Ana", "email": "ficticio@example.test"},
            format="json",
        ).json()
        for w in workspaces[:2]
    ]
    assert records[0]["id"] != records[1]["id"]


@pytest.mark.parametrize(
    "data",
    [
        {"full_name": ""},
        {"full_name": "   "},
        {"full_name": "a" * 201},
        {"full_name": "Ana", "email": "bad"},
        {"full_name": "Ana", "phone": "1" * 33},
    ],
)
def test_input_validation(signed_api, workspaces, data):
    assert signed_api.post(url(workspaces[0]), data, format="json").status_code == 400


def test_pagination_default_max_and_stable_order(signed_api, workspaces):
    a = workspaces[0]
    for index in range(27):
        assert (
            signed_api.post(
                url(a), {"full_name": f"Persona {index}"}, format="json"
            ).status_code
            == 201
        )
    first = signed_api.get(url(a)).json()
    assert first["count"] == 27
    assert len(first["results"]) == 25
    second = signed_api.get(url(a) + "?page=2").json()
    assert len(second["results"]) == 2
    assert first["results"][0]["full_name"] == "Persona 0"
    assert len(signed_api.get(url(a) + "?page_size=1000").json()["results"]) == 27
    assert signed_api.get(url(a) + "?page_size=bad").status_code == 400


def test_malformed_uuid_json_error(signed_api):
    response = signed_api.get("/api/v1/workspaces/not-a-uuid/clients/")
    assert response.status_code == 400
    assert "error" in response.json()


def test_maximum_page_size_is_100(signed_api, workspaces):
    from modules.clients.models import ClientRecord
    from tenancy.context import workspace_context

    a = workspaces[0]
    with workspace_context(a.id):
        ClientRecord.objects.bulk_create(
            [ClientRecord(workspace=a, full_name=f"Fictional {i}") for i in range(105)]
        )
    response = signed_api.get(url(a) + "?page_size=1000").json()
    assert response["count"] == 105
    assert len(response["results"]) == 100
    assert len(signed_api.get(response["next"]).json()["results"]) == 5
