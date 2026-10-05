from datetime import date

import pytest


@pytest.mark.parametrize(
    "start,unit,quantity,end",
    [
        (date(2027, 1, 31), "MONTHS", 1, date(2027, 2, 28)),
        (date(2028, 1, 31), "MONTHS", 1, date(2028, 2, 29)),
        (date(2026, 12, 1), "MONTHS", 2, date(2027, 2, 1)),
        (date(2027, 1, 31), "DAYS", 30, date(2027, 3, 2)),
    ],
)
def test_period_end(start, unit, quantity, end):
    from modules.gym.dates import period_end

    assert period_end(start, unit, quantity) == end


@pytest.fixture
def gym_spaces(workspaces):
    from modules.workspaces.models import WorkspaceCapability

    for space in workspaces[:2]:
        for code in ("gym.manage", "receivables.manage"):
            WorkspaceCapability.objects.create(workspace=space, code=code)
    return workspaces


def plan_data(**extra):
    return {
        "name": "Mensual",
        "amount": "30.00",
        "currency": "USD",
        "unit": "MONTHS",
        "quantity": 1,
        **extra,
    }


def test_catalog_versions_and_security(signed_api, gym_spaces, operator):
    from modules.workspaces.models import WorkspaceAccess

    a, b, outsider = gym_spaces
    base = f"/api/v1/workspaces/{a.id}/gym/plans/"
    created = signed_api.post(base, plan_data(), format="json")
    assert created.status_code == 201, created.content
    plan = created.json()
    assert plan["version"] == 1
    updated = signed_api.patch(
        base + plan["id"] + "/",
        {"expected_version": 1, "amount": "20.00", "is_promotion": True},
        format="json",
    )
    assert updated.status_code == 200, updated.content
    assert updated.json()["version"] == 2
    assert (
        signed_api.patch(
            base + plan["id"] + "/",
            {"expected_version": 1, "amount": "10.00"},
            format="json",
        ).status_code
        == 400
    )
    assert (
        signed_api.post(base, plan_data(workspace=str(b.id)), format="json").status_code
        == 400
    )
    assert signed_api.get(f"/api/v1/workspaces/{b.id}/gym/plans/").json()["count"] == 0
    assert (
        signed_api.get(f"/api/v1/workspaces/{outsider.id}/gym/plans/").status_code
        == 404
    )
    WorkspaceAccess.objects.filter(workspace=a, user=operator).update(role="RECEPTION")
    assert signed_api.get(base).status_code == 200
    assert signed_api.post(base, plan_data(), format="json").status_code == 403
    WorkspaceAccess.objects.filter(workspace=a, user=operator).update(role="COACH")
    assert signed_api.get(base).status_code == 403
