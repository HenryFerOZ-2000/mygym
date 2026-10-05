from datetime import date, timezone
from decimal import Decimal
from uuid import uuid4


def test_date_range_uses_local_boundaries_and_validates():
    from modules.shared.reporting import period_bounds, ReportRangeSerializer

    start, end = period_bounds(date(2026, 3, 8), date(2026, 3, 8), "America/New_York")
    assert (
        end.astimezone(timezone.utc) - start.astimezone(timezone.utc)
    ).total_seconds() == 23 * 3600
    assert not ReportRangeSerializer(
        data={"from_date": "2026-01-01", "to_date": "2027-01-02"}
    ).is_valid()


def test_financial_report_currencies_allocations_refunds_and_current_balance(
    gym_case, operator
):
    from modules.workspaces.models import WorkspaceCapability
    from modules.workspaces.policies import WorkspaceContext
    from modules.clients.models import ClientRecord
    from modules.receivables.services import (
        create_charge,
        record_payment,
        refund_payment,
    )
    from tenancy.context import workspace_context

    api, space, base, url, client, *_ = gym_case
    WorkspaceCapability.objects.create(workspace=space, code="receivables.reports")
    context = WorkspaceContext(workspace=space, actor=operator)
    with workspace_context(space.id):
        customer = ClientRecord.objects.get(pk=client["id"])
        usd = [
            create_charge(context, customer, uuid4(), Decimal("30.00"), "USD", "Prueba")
            for _ in range(2)
        ]
        create_charge(context, customer, uuid4(), Decimal("9.00"), "EUR", "Otra moneda")
        payment = record_payment(
            context,
            customer.id,
            {
                "request_id": uuid4(),
                "amount": Decimal("40.00"),
                "currency": "USD",
                "method": "CASH",
                "allocations": [
                    {"charge_id": usd[0].id, "amount": Decimal("30.00")},
                    {"charge_id": usd[1].id, "amount": Decimal("10.00")},
                ],
            },
        )
        for amount in ("3.00", "2.00"):
            refund_payment(
                context,
                customer.id,
                payment.id,
                {
                    "request_id": uuid4(),
                    "reason": "Prueba",
                    "allocations": [
                        {"charge_id": usd[0].id, "amount": Decimal(amount)}
                    ],
                },
            )
    from modules.gym.dates import today

    day = str(today(space))
    response = api.get(base + f"reports/financial/?from_date={day}&to_date={day}")
    assert response.status_code == 200, response.content
    rows = {r["currency"]: r for r in response.json()["currencies"]}
    assert rows["USD"] == {
        "currency": "USD",
        "payments": "40.00",
        "refunds": "5.00",
        "net": "35.00",
        "outstanding_now": "25.00",
    }
    assert rows["EUR"]["outstanding_now"] == "9.00"
    assert rows["EUR"]["payments"] == "0.00"
    assert (
        api.get(
            base + "reports/financial/?from_date=2026-01-01&to_date=2025-01-01"
        ).status_code
        == 400
    )
    assert (
        api.get(
            base + f"reports/financial/?from_date={day}&to_date={day}&workspace=bad"
        ).status_code
        == 400
    )


def test_expiries_do_not_label_renewed_client_expired(gym_case):
    api, space, base, url, client, _, _, enroll = gym_case
    first, _ = enroll()
    second, _ = enroll()
    response = api.get(base + "gym/expiries/?status=FUTURE")
    assert response.status_code == 200, response.content
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["client_id"] == client["id"]
    assert api.get(base + "gym/expiries/?status=EXPIRED").json()["count"] == 0


def test_expiry_contiguous_renewal_and_gap(gym_case, operator, monkeypatch):
    from datetime import datetime, time, timedelta
    from zoneinfo import ZoneInfo

    api, space, base, url, _, _, start, enroll = gym_case
    api.force_authenticate(user=operator)
    first, _ = enroll()
    second, _ = enroll()
    monkeypatch.setattr(
        "django.utils.timezone.now",
        lambda: datetime.combine(
            start + timedelta(days=29), time(12), ZoneInfo(space.timezone)
        ),
    )
    assert api.get(base + "gym/expiries/?status=EXPIRING").json()["count"] == 0
    active = api.get(base + "gym/expiries/?status=ACTIVE").json()["results"][0]
    assert active["coverage_end"] == second["end_date"]
    assert active["calendar_days_remaining"] == 30
    changed = api.post(
        url + "gym/memberships/" + second["id"] + "/correct/",
        {
            "request_id": str(uuid4()),
            "reason": "Brecha solicitada",
            "start_date": str(start + timedelta(days=32)),
            "end_date": str(start + timedelta(days=62)),
        },
        format="json",
    )
    assert changed.status_code == 200, changed.content
    rows = api.get(base + "gym/expiries/?status=EXPIRING").json()["results"]
    assert rows[0]["coverage_end"] == first["end_date"]
    assert rows[0]["next_start"] == str(start + timedelta(days=32))
    monkeypatch.setattr(
        "django.utils.timezone.now",
        lambda: datetime.combine(
            start + timedelta(days=32), time(12), ZoneInfo(space.timezone)
        ),
    )
    assert api.get(base + "gym/expiries/?status=EXPIRED").json()["count"] == 0


def test_report_permissions_and_independent_capabilities(gym_case, operator):
    from modules.workspaces.models import WorkspaceAccess, WorkspaceCapability

    api, space, base, *_ = gym_case
    query = "?from_date=2026-10-01&to_date=2026-10-02"
    for code in ("gym.reports", "receivables.reports"):
        WorkspaceCapability.objects.create(workspace=space, code=code)
    WorkspaceCapability.objects.filter(workspace=space, code="gym.manage").update(
        enabled=False
    )
    assert api.get(base + "reports/financial/" + query).status_code == 200
    assert api.get(base + "reports/attendance/" + query).status_code == 200
    assert api.get(base + "gym/expiries/").status_code == 403
    WorkspaceAccess.objects.filter(workspace=space, user=operator).update(
        role="RECEPTION"
    )
    assert api.get(base + "reports/financial/" + query).status_code == 403
    assert api.get(base + "reports/attendance/" + query).status_code == 403


def test_refund_period_follows_refund_date_and_debt_includes_inactive(
    gym_case, operator, monkeypatch
):
    from datetime import datetime
    from modules.workspaces.policies import WorkspaceContext
    from modules.clients.models import ClientRecord
    from modules.receivables.services import (
        create_charge,
        record_payment,
        refund_payment,
    )
    from modules.receivables.reports import financial_report
    from tenancy.context import workspace_context

    api, space, _, url, client, *_ = gym_case
    context = WorkspaceContext(space, operator)
    api.patch(url, {"is_active": False}, format="json")
    with workspace_context(space.id):
        customer = ClientRecord.objects.get(pk=client["id"])
        charge = create_charge(
            context, customer, uuid4(), Decimal("30.00"), "USD", "Prueba"
        )
        monkeypatch.setattr(
            "django.utils.timezone.now",
            lambda: datetime(2026, 10, 2, 4, 59, 59, tzinfo=timezone.utc),
        )
        payment = record_payment(
            context,
            customer.id,
            {
                "request_id": uuid4(),
                "amount": Decimal("30.00"),
                "currency": "USD",
                "method": "CASH",
                "allocations": [{"charge_id": charge.id, "amount": Decimal("30.00")}],
            },
        )
        monkeypatch.setattr(
            "django.utils.timezone.now",
            lambda: datetime(2026, 10, 2, 5, 0, 0, tzinfo=timezone.utc),
        )
        refund_payment(
            context,
            customer.id,
            payment.id,
            {
                "request_id": uuid4(),
                "reason": "Prueba",
                "allocations": [{"charge_id": charge.id, "amount": Decimal("5.00")}],
            },
        )
        row = financial_report(context, date(2026, 10, 2), date(2026, 10, 2))[
            "currencies"
        ][0]
        assert row == {
            "currency": "USD",
            "payments": "0.00",
            "refunds": "5.00",
            "net": "-5.00",
            "outstanding_now": "5.00",
        }
