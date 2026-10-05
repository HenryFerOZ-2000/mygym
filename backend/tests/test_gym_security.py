from datetime import timedelta
from uuid import uuid4

import pytest
from django.db import connection, transaction, DatabaseError


def test_all_business_tables_enforce_rls_and_immutable_history(gym_case, gym_spaces):
    from django.apps import apps
    from tenancy.context import workspace_context
    from modules.gym.models import PlanVersion

    api, space, _, url, _, _, _, enroll = gym_case
    enroll()
    tables = [
        m._meta.db_table
        for m in apps.get_models()
        if m._meta.app_label in {"gym", "receivables"}
    ]
    with connection.cursor() as cursor:
        for table in tables:
            cursor.execute(f'SELECT count(*) FROM "{table}"')
            assert cursor.fetchone()[0] == 0
    with workspace_context(gym_spaces[1].id):
        assert PlanVersion.objects.count() == 0
    with workspace_context(space.id):
        with pytest.raises(DatabaseError), transaction.atomic():
            PlanVersion.objects.update(amount="1.00")
        with connection.cursor() as cursor:
            for table in tables:
                cursor.execute(
                    "SELECT has_table_privilege(current_user, %s, 'DELETE')", [table]
                )
                assert cursor.fetchone()[0] is False
    assert api.get(url + "gym/").json()["count"] == 1


def test_permission_revocation_and_foreign_charge(gym_case, gym_spaces, operator):
    from modules.workspaces.models import WorkspaceAccess, WorkspaceCapability

    api, space, _, url, _, _, _, enroll = gym_case
    member, _ = enroll()
    charges = api.get(url + "receivables/").json()["results"]
    other_base = f"/api/v1/workspaces/{gym_spaces[1].id}/clients/"
    other = api.post(other_base, {"full_name": "Otro"}, format="json").json()
    payload = {
        "request_id": str(uuid4()),
        "amount": "1.00",
        "currency": "USD",
        "method": "CASH",
        "allocations": [{"charge_id": charges[0]["id"], "amount": "1.00"}],
    }
    assert (
        api.post(
            other_base + other["id"] + "/receivables/payments/", payload, format="json"
        ).status_code
        == 404
    )
    WorkspaceAccess.objects.filter(workspace=space, user=operator).update(
        role="RECEPTION"
    )
    paid = api.post(url + "receivables/payments/", payload, format="json")
    assert paid.status_code == 201
    refund = {
        "request_id": str(uuid4()),
        "reason": "Intento no autorizado",
        "allocations": payload["allocations"],
    }
    assert (
        api.post(
            url + "receivables/payments/" + paid.json()["id"] + "/refunds/",
            refund,
            format="json",
        ).status_code
        == 403
    )
    WorkspaceCapability.objects.filter(
        workspace=space, code="receivables.manage"
    ).update(enabled=False)
    assert api.get(url + "receivables/").status_code == 403
    assert api.post(url + "gym/preview/", {}, format="json").status_code == 403
    WorkspaceAccess.objects.filter(workspace=space, user=operator).update(
        is_active=False
    )
    assert api.get(url + "gym/").status_code == 404


def test_promotion_dates_inactive_client_and_unknown_fields(gym_case):
    from modules.gym.dates import today

    api, space, base, url, _, plan, _, enroll = gym_case
    later = str(today(space) + timedelta(days=10))
    response = api.patch(
        base + "gym/plans/" + plan["id"] + "/",
        {"expected_version": 1, "available_from": later},
        format="json",
    )
    assert response.status_code == 200
    preview = {"plan_id": plan["id"], "start_date": later}
    assert api.post(url + "gym/preview/", preview, format="json").status_code == 400
    assert (
        api.post(
            url + "gym/preview/", {**preview, "workspace": str(space.id)}, format="json"
        ).status_code
        == 400
    )
    api.patch(
        base + "gym/plans/" + plan["id"] + "/",
        {"expected_version": 2, "available_from": None},
        format="json",
    )
    api.patch(url, {"is_active": False}, format="json")
    assert api.post(url + "gym/preview/", preview, format="json").status_code == 400
