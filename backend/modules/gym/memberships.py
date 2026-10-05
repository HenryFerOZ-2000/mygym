from datetime import timedelta
from django.db import transaction
from rest_framework.exceptions import ValidationError
from modules.receivables import services as receivables
from modules.shared.api import find
from .dates import period_end, today
from .models import Membership, Plan
from modules.shared.operations import lock_client, replay, fingerprint, audit
from .services import current


def calculate(context, client, data):
    if not client.is_active:
        raise ValidationError({"client": "Activa la ficha antes de inscribir."})
    plan = find(
        Plan.objects.select_for_update().filter(workspace=context.workspace),
        data["plan_id"],
    )
    version = current(plan)
    now = today(context.workspace)
    if (
        not version.is_active
        or (version.available_from and now < version.available_from)
        or (version.available_until and now > version.available_until)
    ):
        raise ValidationError(
            {"plan_id": "El plan no está disponible para nuevas inscripciones."}
        )
    start = data["start_date"]
    if start < now:
        raise ValidationError({"start_date": "Selecciona hoy o una fecha futura."})
    periods = Membership.objects.filter(workspace=context.workspace, client=client)
    last = max(
        (
            min(m.end_date, m.cancelled_on) if m.cancelled_on else m.end_date
            for m in periods
            if not m.cancelled_on or m.cancelled_on > m.start_date
        ),
        default=start,
    )
    start = max(start, last)
    end = period_end(start, version.unit, version.quantity)
    return version, {
        "version": version.version,
        "plan_id": plan.id,
        "name": version.name,
        "start_date": start,
        "end_date": end,
        "last_day": end - timedelta(days=1),
        "amount": version.amount,
        "currency": version.currency,
    }


@transaction.atomic
def preview(context, client_id, data):
    client = lock_client(context, client_id)
    return calculate(context, client, data)[1]


@transaction.atomic
def enroll(context, client_id, data):
    client = lock_client(context, client_id)
    signed = {**data, "client_id": str(client.id)}
    existing = replay(Membership.objects.filter(workspace=context.workspace), signed)
    if existing:
        return existing
    version, result = calculate(context, client, data)
    if (
        data["expected_version"] != result["version"]
        or data["expected_start"] != result["start_date"]
        or data["expected_end"] != result["end_date"]
    ):
        raise ValidationError(
            {"preview": "Las condiciones cambiaron. Vuelve a previsualizar."}
        )
    membership = Membership.objects.create(
        workspace=context.workspace,
        client=client,
        plan_version=version,
        start_date=result["start_date"],
        end_date=result["end_date"],
        request_id=data["request_id"],
        fingerprint=fingerprint(signed),
    )
    receivables.create_charge(
        context, client, membership.id, version.amount, version.currency, version.name
    )
    audit(
        context,
        "gym.membership.created",
        membership,
        ["plan_version", "start_date", "end_date"],
    )
    return membership


def membership_data(context, membership):
    version = membership.plan_version
    now = today(context.workspace)
    end = (
        min(membership.end_date, membership.cancelled_on)
        if membership.cancelled_on
        else membership.end_date
    )
    freezes = list(membership.freezes.order_by("start_date"))
    state = "FUTURE" if now < membership.start_date else "ACTIVE"
    if now >= end:
        state = "CANCELLED" if membership.cancelled_on else "EXPIRED"
    elif any(f.start_date <= now < f.end_date for f in freezes):
        state = "FROZEN"
    if not membership.client.is_active:
        state = "CLIENT_INACTIVE"
    return {
        "id": str(membership.id),
        "name": version.name,
        "version": version.version,
        "amount": format(version.amount, ".2f"),
        "currency": version.currency,
        "start_date": membership.start_date,
        "end_date": membership.end_date,
        "last_day": end - timedelta(days=1) if end > membership.start_date else None,
        "cancelled_on": membership.cancelled_on,
        "status": state,
        "remaining_days": max(
            0,
            (end - max(now, membership.start_date)).days
            - sum(
                max(0, (min(f.end_date, end) - max(f.start_date, now)).days)
                for f in freezes
            ),
        ),
        "freezes": [
            {"start_date": f.start_date, "end_date": f.end_date} for f in freezes
        ],
        "changes": list(
            membership.changes.order_by("created_at", "id").values(
                "kind", "reason", "before", "after", "created_at"
            )
        ),
    }
