import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture(scope="session")
def django_db_setup():
    """Database is explicitly provisioned/migrated outside runtime tests."""


@pytest.fixture
def operator(db):
    return get_user_model().objects.create_user(
        username="operator", password="testing-only-passphrase"
    )


@pytest.fixture
def api():
    return APIClient(enforce_csrf_checks=True)


def csrf(api):
    response = api.get("/api/v1/auth/csrf/")
    assert response.status_code == 200
    api.credentials(HTTP_X_CSRFTOKEN=response.json()["csrfToken"])


@pytest.fixture
def signed_api(api, operator):
    csrf(api)
    response = api.post(
        "/api/v1/auth/login/",
        {"username": operator.username, "password": "testing-only-passphrase"},
        format="json",
    )
    assert response.status_code == 200
    csrf(api)
    return api


@pytest.fixture
def workspaces(operator):
    from modules.workspaces.models import (
        Workspace,
        WorkspaceAccess,
        WorkspaceCapability,
    )

    spaces = [
        Workspace.objects.create(name=name) for name in ["Gym A", "Gym B", "Outsider"]
    ]
    for space in spaces[:2]:
        WorkspaceAccess.objects.create(workspace=space, user=operator, role="OWNER")
        WorkspaceCapability.objects.create(workspace=space, code="clients.manage")
    return spaces


@pytest.fixture
def gym_spaces(workspaces):
    from modules.workspaces.models import WorkspaceCapability

    for space in workspaces[:2]:
        for code in ("gym.manage", "receivables.manage"):
            WorkspaceCapability.objects.create(workspace=space, code=code)
    return workspaces


@pytest.fixture
def gym_case(signed_api, gym_spaces):
    from uuid import uuid4
    from datetime import timedelta
    from modules.gym.dates import today

    space = gym_spaces[0]
    base = f"/api/v1/workspaces/{space.id}/"
    client = signed_api.post(
        base + "clients/", {"full_name": "Cliente Membresía"}, format="json"
    ).json()
    plan = signed_api.post(
        base + "gym/plans/",
        {
            "name": "30 días",
            "amount": "30.00",
            "currency": "USD",
            "unit": "DAYS",
            "quantity": 30,
        },
        format="json",
    ).json()
    client_base = base + "clients/" + client["id"] + "/"
    start = today(space) + timedelta(days=2)

    def enroll():
        preview = signed_api.post(
            client_base + "gym/preview/",
            {"plan_id": plan["id"], "start_date": str(start)},
            format="json",
        )
        assert preview.status_code == 200, preview.content
        data = preview.json()
        payload = {
            "request_id": str(uuid4()),
            "plan_id": plan["id"],
            "start_date": str(start),
            "expected_version": data["version"],
            "expected_start": data["start_date"],
            "expected_end": data["end_date"],
        }
        response = signed_api.post(
            client_base + "gym/memberships/", payload, format="json"
        )
        assert response.status_code == 201, response.content
        return response.json(), payload

    return signed_api, space, base, client_base, client, plan, start, enroll
