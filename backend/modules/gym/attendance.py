from zoneinfo import ZoneInfo
from datetime import timedelta
from django.db import transaction
from django.db.models import F, Max, Min, Q
from django.db.models.functions import Coalesce, Least
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from modules.shared.api import find
from modules.shared.operations import lock_client, replay, fingerprint, audit
from modules.workspaces.policies import require_business
from .models import Membership, Attendance, AttendanceVoid


def service_state(context, client, day):
    if not client.is_active:
        return "CLIENT_INACTIVE", None
    periods = list(
        Membership.objects.filter(workspace=context.workspace, client=client)
        .prefetch_related("freezes")
        .order_by("start_date", "id")
    )
    past = False
    future = False
    for member in periods:
        end = (
            min(member.end_date, member.cancelled_on)
            if member.cancelled_on
            else member.end_date
        )
        if end <= member.start_date:
            continue
        if member.start_date <= day < end:
            frozen = any(f.start_date <= day < f.end_date for f in member.freezes.all())
            return ("FROZEN" if frozen else "ACTIVE"), member
        past |= end <= day
        future |= member.start_date > day
    return ("EXPIRED" if past else "FUTURE" if future else "NO_MEMBERSHIP"), None


def count_today(context, client, day):
    return Attendance.objects.filter(
        workspace=context.workspace,
        client=client,
        local_date=day,
        void_record__isnull=True,
    ).count()


@transaction.atomic
def attendance_preview(context, client_id):
    client = lock_client(context, client_id)
    day = timezone.now().astimezone(ZoneInfo(context.workspace.timezone)).date()
    status, member = service_state(context, client, day)
    dates = (
        Membership.objects.filter(workspace=context.workspace, client=client)
        .annotate(effective_end=Least("end_date", Coalesce("cancelled_on", "end_date")))
        .filter(start_date__lt=F("effective_end"))
        .aggregate(
            previous_end=Max("effective_end", filter=Q(effective_end__lte=day)),
            next_start=Min("start_date", filter=Q(start_date__gt=day)),
        )
    )
    end = (
        min(member.end_date, member.cancelled_on or member.end_date) if member else None
    )
    return {
        "client_id": client.id,
        "full_name": client.full_name,
        "status": status,
        "membership_id": member.id if member else None,
        "last_day": end - timedelta(days=1) if end else None,
        "previous_last_day": dates["previous_end"] - timedelta(days=1)
        if dates["previous_end"]
        else None,
        "next_start": dates["next_start"],
        "local_date": day,
        "today_count": count_today(context, client, day),
        "timezone": context.workspace.timezone,
    }


@transaction.atomic
def record_attendance(context, client_id, data):
    client = lock_client(context, client_id)
    signature = {**data, "client_id": str(client.id)}
    old = replay(Attendance.objects.filter(workspace=context.workspace), signature)
    if old:
        return old
    instant = timezone.now()
    day = instant.astimezone(ZoneInfo(context.workspace.timezone)).date()
    status, member = service_state(context, client, day)
    if (
        day != data["expected_date"]
        or count_today(context, client, day) != data["expected_count"]
    ):
        raise ValidationError(
            {
                "preview": "La fecha o las visitas cambiaron. Vuelve a revisar la entrada."
            }
        )
    if status in {"CLIENT_INACTIVE", "FROZEN"}:
        raise ValidationError(
            {"client": "Ficha inactiva o membresía congelada: entrada no habilitada."}
        )
    if data["expected_count"] > 0 and not data["confirm_repeat"]:
        raise ValidationError(
            {"confirm_repeat": "Confirma expresamente otra visita hoy."}
        )
    exception = data["exception"]
    if exception:
        require_business(
            context.actor, context.workspace.id, "gym.attendance", owner=True
        )
        if status == "ACTIVE" or not data["reason"].strip():
            raise ValidationError(
                {"reason": "La excepción exige falta de servicio vigente y un motivo."}
            )
    elif status != "ACTIVE":
        raise ValidationError(
            {
                "exception": "No hay servicio vigente. Se requiere excepción del propietario."
            }
        )
    elif data["reason"]:
        raise ValidationError(
            {"reason": "Una entrada ordinaria no necesita motivo de excepción."}
        )
    entry = Attendance.objects.create(
        workspace=context.workspace,
        client=client,
        actor=context.actor,
        membership=member,
        created_at=instant,
        local_date=day,
        timezone=context.workspace.timezone,
        decision="EXCEPTION" if exception else "NORMAL",
        service_status=status,
        reason=data["reason"],
        request_id=data["request_id"],
        fingerprint=fingerprint(signature),
    )
    audit(
        context,
        "gym.attendance.created",
        entry,
        ["client", "membership", "local_date", "decision", "reason"],
    )
    return entry


@transaction.atomic
def void_attendance(context, attendance_id, data):
    entry = find(Attendance.objects.filter(workspace=context.workspace), attendance_id)
    lock_client(context, entry.client_id)
    signature = {**data, "attendance_id": str(entry.id)}
    old = replay(AttendanceVoid.objects.filter(workspace=context.workspace), signature)
    if old:
        return entry
    if AttendanceVoid.objects.filter(
        attendance=entry, workspace=context.workspace
    ).exists():
        raise ValidationError({"attendance": "La entrada ya fue anulada."})
    AttendanceVoid.objects.create(
        workspace=context.workspace,
        attendance=entry,
        actor=context.actor,
        reason=data["reason"],
        request_id=data["request_id"],
        fingerprint=fingerprint(signature),
    )
    audit(context, "gym.attendance.voided", entry, ["reason"])
    return entry


def attendance_data(entry):
    void = getattr(entry, "void_record", None)
    return {
        "id": entry.id,
        "client_id": entry.client_id,
        "full_name": entry.client.full_name,
        "actor": entry.actor.username,
        "created_at": entry.created_at,
        "local_date": entry.local_date,
        "timezone": entry.timezone,
        "decision": entry.decision,
        "service_status": entry.service_status,
        "reason": entry.reason,
        "voided": void is not None,
        "void_reason": void.reason if void else None,
        "void_actor": void.actor.username if void else None,
        "voided_at": void.created_at if void else None,
    }
