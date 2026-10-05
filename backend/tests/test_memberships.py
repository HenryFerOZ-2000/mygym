from datetime import timedelta
from uuid import uuid4


def test_enroll_renew_snapshot_and_retries(gym_case):
    api, space, base, url, client, plan, start, enroll = gym_case
    first, payload = enroll()
    again = api.post(url + "gym/memberships/", payload, format="json")
    assert again.status_code == 201 and again.json()["id"] == first["id"]
    bad = api.post(
        url + "gym/memberships/", {**payload, "expected_version": 2}, format="json"
    )
    assert bad.status_code == 400
    second, _ = enroll()
    assert second["start_date"] == first["end_date"]
    assert first["last_day"] == str(start + timedelta(days=29))
    charges = api.get(url + "receivables/").json()
    assert charges["count"] == 2
    assert all(c["balance"] == "30.00" for c in charges["results"])
    api.patch(
        base + "gym/plans/" + plan["id"] + "/",
        {"expected_version": 1, "amount": "15.00"},
        format="json",
    )
    history = api.get(url + "gym/").json()["results"]
    assert history[0]["amount"] == "30.00"
    stale = {**payload, "request_id": str(uuid4())}
    assert api.post(url + "gym/memberships/", stale, format="json").status_code == 400


def test_enrollment_charge_atomic_and_cross_tenant(gym_case, gym_spaces, monkeypatch):
    from modules.receivables import services

    api, space, base, url, client, plan, start, enroll = gym_case

    def broken(*args, **kwargs):
        raise RuntimeError("injected charge failure")

    monkeypatch.setattr(services, "create_charge", broken)
    import pytest

    with pytest.raises(RuntimeError, match="injected"):
        enroll()
    assert api.get(url + "gym/").json()["count"] == 0
    alien = url.replace(str(space.id), str(gym_spaces[1].id))
    assert api.get(alien + "gym/").status_code == 404


def test_cancelled_future_period_does_not_delay_replacement(gym_case):
    from modules.gym.dates import today

    api, space, _, url, _, plan, start, enroll = gym_case
    member, _ = enroll()
    cancelled = api.post(
        url + "gym/memberships/" + member["id"] + "/cancel/",
        {
            "request_id": str(uuid4()),
            "reason": "No utilizará el período futuro",
            "effective_date": str(start),
        },
        format="json",
    )
    assert cancelled.status_code == 200
    response = api.post(
        url + "gym/preview/",
        {"plan_id": plan["id"], "start_date": str(today(space))},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["start_date"] == str(today(space))
