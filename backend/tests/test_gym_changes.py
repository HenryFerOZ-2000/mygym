from datetime import timedelta
from uuid import uuid4


def test_change_request_key_cannot_be_reused_for_another_membership(gym_case):
    api, _, _, url, _, _, _, enroll = gym_case
    first, _ = enroll()
    second, _ = enroll()
    request_id = str(uuid4())

    def cancel(member):
        return api.post(
            url + "gym/memberships/" + member["id"] + "/cancel/",
            {
                "request_id": request_id,
                "reason": "Cancelación solicitada",
                "effective_date": member["start_date"],
            },
            format="json",
        )

    assert cancel(first).status_code == 200
    assert cancel(second).status_code == 400
    current = next(
        m for m in api.get(url + "gym/").json()["results"] if m["id"] == second["id"]
    )
    assert current["cancelled_on"] is None


def test_freeze_shifts_future_periods_cancel_keeps_debt(gym_case):
    api, _, _, url, _, _, start, enroll = gym_case
    first, _ = enroll()
    second, _ = enroll()
    change_url = url + "gym/memberships/" + first["id"] + "/"
    payload = {
        "request_id": str(uuid4()),
        "reason": "Viaje",
        "start_date": str(start),
        "end_date": str(start + timedelta(days=3)),
    }
    response = api.post(change_url + "freeze/", payload, format="json")
    assert response.status_code == 200, response.content
    assert response.json()["end_date"] == str(start + timedelta(days=33))
    assert api.post(change_url + "freeze/", payload, format="json").status_code == 200
    history = api.get(url + "gym/").json()["results"]
    future = next(m for m in history if m["id"] == second["id"])
    assert future["start_date"] == str(start + timedelta(days=33))
    assert future["end_date"] == str(start + timedelta(days=63))
    overlap = {**payload, "request_id": str(uuid4())}
    assert api.post(change_url + "freeze/", overlap, format="json").status_code == 400
    cancelled = api.post(
        change_url + "cancel/",
        {
            "request_id": str(uuid4()),
            "reason": "Solicitud del cliente",
            "effective_date": str(start + timedelta(days=5)),
        },
        format="json",
    )
    assert cancelled.status_code == 200
    assert api.get(url + "receivables/").json()["results"][0]["balance"] == "30.00"


def test_corrections_require_owner_reason_and_no_overlap(gym_case, operator):
    from modules.workspaces.models import WorkspaceAccess

    api, space, _, url, _, _, start, enroll = gym_case
    first, _ = enroll()
    action = url + "gym/memberships/" + first["id"] + "/correct/"
    data = {
        "request_id": str(uuid4()),
        "reason": "Fecha solicitada",
        "start_date": str(start + timedelta(days=1)),
        "end_date": str(start + timedelta(days=31)),
    }
    assert api.post(action, data, format="json").status_code == 200
    WorkspaceAccess.objects.filter(workspace=space, user=operator).update(
        role="RECEPTION"
    )
    assert (
        api.post(
            action, {**data, "request_id": str(uuid4())}, format="json"
        ).status_code
        == 403
    )
