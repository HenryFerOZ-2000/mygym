from uuid import uuid4

import pytest


def test_preview_dates_respect_cancellation_and_future_gap(
    attendance_case, operator, monkeypatch
):
    from datetime import datetime, time, timedelta
    from zoneinfo import ZoneInfo

    api, space, _, url, _, _, start, enroll = attendance_case
    api.force_authenticate(user=operator)
    first, _ = enroll()
    second, _ = enroll()
    monkeypatch.setattr(
        "django.utils.timezone.now",
        lambda: datetime.combine(start, time(12), ZoneInfo(space.timezone)),
    )
    response = api.get(url + "attendance/preview/")
    assert response.status_code == 200
    data = response.json()
    assert data["last_day"] == str(start + timedelta(days=29))
    assert data["next_start"] == second["start_date"]
    assert data["previous_last_day"] is None
    cancelled = api.post(
        url + "gym/memberships/" + first["id"] + "/cancel/",
        {
            "request_id": str(uuid4()),
            "reason": "Solicitud ficticia",
            "effective_date": str(start + timedelta(days=2)),
        },
        format="json",
    )
    assert cancelled.status_code == 200
    assert api.get(url + "attendance/preview/").json()["last_day"] == str(
        start + timedelta(days=1)
    )
    monkeypatch.setattr(
        "django.utils.timezone.now",
        lambda: datetime.combine(
            start + timedelta(days=2), time(12), ZoneInfo(space.timezone)
        ),
    )
    expired = api.get(url + "attendance/preview/").json()
    assert expired["status"] == "EXPIRED"
    assert expired["last_day"] is None
    assert expired["previous_last_day"] == str(start + timedelta(days=1))
    assert expired["next_start"] == second["start_date"]
    assert (
        api.post(
            url + "gym/memberships/" + second["id"] + "/cancel/",
            {
                "request_id": str(uuid4()),
                "reason": "Cancelar período futuro",
                "effective_date": second["start_date"],
            },
            format="json",
        ).status_code
        == 200
    )
    from modules.workspaces.models import WorkspaceCapability

    WorkspaceCapability.objects.filter(
        workspace=space, code__in=["gym.manage", "clients.manage"]
    ).update(enabled=False)
    isolated = api.get(url + "attendance/preview/")
    assert isolated.status_code == 200
    assert isolated.json()["next_start"] is None
    assert isolated.json()["previous_last_day"] == str(start + timedelta(days=1))


@pytest.fixture
def attendance_case(gym_case):
    from modules.workspaces.models import WorkspaceCapability

    api, space, base, url, client, plan, start, enroll = gym_case
    for code in ("gym.attendance", "gym.reports", "receivables.reports"):
        WorkspaceCapability.objects.create(workspace=space, code=code)
    return gym_case


def test_owner_exception_repetition_and_void(attendance_case, operator):
    api, _, base, url, client, *_ = attendance_case
    endpoint = url + "attendance/"
    preview = api.get(endpoint + "preview/")
    assert preview.status_code == 200
    data = {
        "request_id": str(uuid4()),
        "expected_date": preview.json()["local_date"],
        "expected_count": 0,
        "confirm_repeat": False,
        "exception": True,
        "reason": "Visita de cortesía",
    }
    first = api.post(endpoint, data, format="json")
    assert first.status_code == 201, first.content
    assert first.json()["actor"] == operator.username
    assert first.json()["decision"] == "EXCEPTION"
    assert first.json()["void_actor"] is None
    assert first.json()["voided_at"] is None
    assert api.post(endpoint, data, format="json").json()["id"] == first.json()["id"]
    assert (
        api.post(
            endpoint, {**data, "request_id": str(uuid4())}, format="json"
        ).status_code
        == 400
    )
    repeat = {
        **data,
        "request_id": str(uuid4()),
        "expected_count": 1,
        "confirm_repeat": True,
    }
    assert api.post(endpoint, repeat, format="json").status_code == 201
    assert api.get(base + "attendance/?q=" + client["full_name"]).json()["count"] == 2
    void_url = base + "attendance/" + first.json()["id"] + "/void/"
    void = {"request_id": str(uuid4()), "reason": "Registro equivocado"}
    annulled = api.post(void_url, void, format="json")
    assert annulled.status_code == 200
    assert annulled.json()["void_actor"] == operator.username
    assert annulled.json()["voided_at"]
    assert api.post(void_url, void, format="json").status_code == 200
    assert api.get(endpoint + "preview/").json()["today_count"] == 1
    day = data["expected_date"]
    report = api.get(base + f"reports/attendance/?from_date={day}&to_date={day}").json()
    assert (
        report["entries"],
        report["clients"],
        report["exceptions"],
        report["voided"],
    ) == (1, 1, 1, 1)


def test_reception_requires_active_service_and_debt_does_not_block(
    attendance_case, operator
):
    from modules.workspaces.models import WorkspaceAccess
    from modules.gym.dates import today

    api, space, _, url, _, plan, *_ = attendance_case
    WorkspaceAccess.objects.filter(workspace=space, user=operator).update(
        role="RECEPTION"
    )
    endpoint = url + "attendance/"
    day = str(today(space))
    payload = {
        "request_id": str(uuid4()),
        "expected_date": day,
        "expected_count": 0,
        "confirm_repeat": False,
        "exception": True,
        "reason": "Intento",
    }
    assert api.post(endpoint, payload, format="json").status_code == 403
    preview = api.post(
        url + "gym/preview/", {"plan_id": plan["id"], "start_date": day}, format="json"
    ).json()
    enrolled = api.post(
        url + "gym/memberships/",
        {
            "request_id": str(uuid4()),
            "plan_id": plan["id"],
            "start_date": day,
            "expected_start": day,
            "expected_end": preview["end_date"],
            "expected_version": 1,
        },
        format="json",
    )
    assert enrolled.status_code == 201
    assert api.get(url + "receivables/").json()["results"][0]["balance"] == "30.00"
    admitted = api.post(
        endpoint, {**payload, "exception": False, "reason": ""}, format="json"
    )
    assert admitted.status_code == 201
    assert admitted.json()["decision"] == "NORMAL"
    api.patch(url, {"is_active": False}, format="json")
    assert (
        api.post(
            endpoint,
            {
                **payload,
                "request_id": str(uuid4()),
                "expected_count": 1,
                "confirm_repeat": True,
            },
            format="json",
        ).status_code
        == 400
    )


def test_attendance_cross_workspace_denied(attendance_case, gym_spaces):
    api, space, base, url, *_ = attendance_case
    from modules.workspaces.models import WorkspaceCapability

    WorkspaceCapability.objects.create(workspace=gym_spaces[1], code="gym.attendance")
    alien = url.replace(str(space.id), str(gym_spaces[1].id))
    assert api.get(alien + "attendance/preview/").status_code == 404
    assert api.get(base + "attendance/clients/?q=Cliente").status_code == 200


def test_attendance_timestamp_matches_decision_at_midnight(
    attendance_case, operator, monkeypatch
):
    from datetime import datetime, timezone, timedelta
    from modules.gym.attendance import record_attendance
    from modules.workspaces.policies import WorkspaceContext
    from tenancy.context import workspace_context

    _, space, _, _, client, *_ = attendance_case
    before = datetime(2026, 10, 3, 4, 59, 59, tzinfo=timezone.utc)
    calls = iter([before, before + timedelta(seconds=2)])
    monkeypatch.setattr(
        "django.utils.timezone.now", lambda: next(calls, before + timedelta(seconds=2))
    )
    with workspace_context(space.id):
        entry = record_attendance(
            WorkspaceContext(space, operator),
            client["id"],
            {
                "request_id": uuid4(),
                "expected_date": before.date() - timedelta(days=1),
                "expected_count": 0,
                "confirm_repeat": False,
                "exception": True,
                "reason": "Cortesía",
            },
        )
        assert entry.created_at == before


def test_frozen_cancelled_and_date_boundaries(attendance_case, operator, monkeypatch):
    from datetime import timedelta, datetime, time
    from zoneinfo import ZoneInfo

    api, space, _, url, _, _, start, enroll = attendance_case
    api.force_authenticate(user=operator)
    member, _ = enroll()

    def clock(day):
        monkeypatch.setattr(
            "django.utils.timezone.now",
            lambda: datetime.combine(day, time(12), ZoneInfo(space.timezone)),
        )

    endpoint = url + "attendance/"
    clock(start)
    assert api.get(endpoint + "preview/").json()["status"] == "ACTIVE"
    change = url + "gym/memberships/" + member["id"] + "/"
    assert (
        api.post(
            change + "freeze/",
            {
                "request_id": str(uuid4()),
                "reason": "Viaje",
                "start_date": str(start),
                "end_date": str(start + timedelta(days=2)),
            },
            format="json",
        ).status_code
        == 200
    )
    assert api.get(endpoint + "preview/").json()["status"] == "FROZEN"
    payload = {
        "request_id": str(uuid4()),
        "expected_date": str(start),
        "expected_count": 0,
        "exception": True,
        "reason": "No permitida",
    }
    assert api.post(endpoint, payload, format="json").status_code == 400
    clock(start + timedelta(days=2))
    assert api.get(endpoint + "preview/").json()["status"] == "ACTIVE"
    assert api.post(endpoint, payload, format="json").status_code == 400
    assert (
        api.post(
            change + "cancel/",
            {
                "request_id": str(uuid4()),
                "reason": "Solicitud",
                "effective_date": str(start + timedelta(days=3)),
            },
            format="json",
        ).status_code
        == 200
    )
    clock(start + timedelta(days=3))
    assert api.get(endpoint + "preview/").json()["status"] == "EXPIRED"
    assert (
        api.post(
            endpoint,
            {**payload, "expected_date": str(start + timedelta(days=3))},
            format="json",
        ).status_code
        == 201
    )


def test_attendance_audit_failure_rolls_back_and_runtime_cannot_overwrite(
    attendance_case, operator, monkeypatch
):
    from django.db import DatabaseError, transaction
    from modules.gym.attendance import record_attendance
    from modules.gym.models import Attendance
    from modules.gym.dates import today
    from modules.workspaces.policies import WorkspaceContext
    from tenancy.context import workspace_context

    _, space, _, _, client, *_ = attendance_case

    def fail(*args):
        raise RuntimeError("audit unavailable")

    monkeypatch.setattr("modules.gym.attendance.audit", fail)
    with workspace_context(space.id):
        with pytest.raises(RuntimeError):
            record_attendance(
                WorkspaceContext(space, operator),
                client["id"],
                {
                    "request_id": uuid4(),
                    "expected_date": today(space),
                    "expected_count": 0,
                    "confirm_repeat": False,
                    "exception": True,
                    "reason": "Prueba",
                },
            )
        assert Attendance.objects.count() == 0
        with pytest.raises(DatabaseError), transaction.atomic():
            Attendance.objects.update(reason="Forbidden")
