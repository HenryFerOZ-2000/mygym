from datetime import timedelta
from django.db import transaction
from rest_framework.exceptions import ValidationError
from modules.shared.api import find
from .dates import today
from .models import Membership, MembershipChange, Freeze
from modules.shared.operations import lock_client, fingerprint, replay, audit


def snapshot(member):
    return {
        "start_date": str(member.start_date),
        "end_date": str(member.end_date),
        "cancelled_on": str(member.cancelled_on) if member.cancelled_on else None,
    }


def save_change(context, member, kind, data, before, signature):
    member.save(update_fields=["start_date", "end_date", "cancelled_on"])
    MembershipChange.objects.create(
        workspace=context.workspace,
        membership=member,
        kind=kind,
        reason=data["reason"],
        before=before,
        after=snapshot(member),
        request_id=data["request_id"],
        fingerprint=fingerprint(signature),
    )
    audit(
        context,
        "gym.membership." + kind.lower(),
        member,
        ["start_date", "end_date", "cancelled_on"],
    )


@transaction.atomic
def change_membership(context, client_id, membership_id, kind, data):
    client = lock_client(context, client_id)
    member = find(
        Membership.objects.filter(workspace=context.workspace, client=client),
        membership_id,
    )
    signature = {
        **data,
        "kind": kind,
        "membership_id": str(member.id),
        "client_id": str(client.id),
    }
    previous = replay(
        MembershipChange.objects.filter(workspace=context.workspace),
        signature,
    )
    if previous:
        return member
    if member.cancelled_on:
        raise ValidationError(
            {"membership": "Esta membresía ya tiene una cancelación registrada."}
        )
    before = snapshot(member)
    now = today(context.workspace)
    if kind == "CANCEL":
        effective = data["effective_date"]
        if effective < now or not member.start_date <= effective < member.end_date:
            raise ValidationError(
                {
                    "effective_date": "Debe estar dentro del período y no ser retroactiva."
                }
            )
        member.cancelled_on = effective
    elif kind == "CORRECT":
        start, end = data["start_date"], data["end_date"]
        if end <= start or member.freezes.exists():
            raise ValidationError(
                {"dates": "Rango inválido o membresía con congelaciones registradas."}
            )
        for other in Membership.objects.filter(
            workspace=context.workspace, client=client
        ).exclude(pk=member.id):
            other_end = (
                min(other.end_date, other.cancelled_on)
                if other.cancelled_on
                else other.end_date
            )
            if (
                start < other_end
                and end > other.start_date
                and other_end > other.start_date
            ):
                raise ValidationError(
                    {"dates": "La corrección se superpone con otro período."}
                )
        member.start_date, member.end_date = start, end
    else:
        start, end = data["start_date"], data["end_date"]
        if (
            start < now
            or start < member.start_date
            or end > member.end_date
            or end <= start
        ):
            raise ValidationError(
                {"dates": "La congelación debe ser futura y estar dentro del período."}
            )
        if member.freezes.filter(start_date__lt=end, end_date__gt=start).exists():
            raise ValidationError({"dates": "La congelación se superpone con otra."})
        future = list(
            Membership.objects.filter(
                workspace=context.workspace,
                client=client,
                start_date__gte=member.end_date,
            )
            .exclude(pk=member.id)
            .order_by("start_date")
        )
        if any(item.freezes.exists() or item.cancelled_on for item in future):
            raise ValidationError(
                {
                    "dates": "Hay períodos posteriores con congelación o cancelación; revisa su programación antes de extender."
                }
            )
        shift = timedelta(days=(end - start).days)
        try:
            new_end = member.end_date + shift
            shifted = [
                (item, item.start_date + shift, item.end_date + shift)
                for item in future
            ]
        except OverflowError:
            raise ValidationError(
                {"dates": "Fecha fuera del rango admitido."}
            ) from None
        Freeze.objects.create(
            workspace=context.workspace,
            membership=member,
            start_date=start,
            end_date=end,
        )
        member.end_date = new_end
        for item, new_start, new_finish in shifted:
            old = snapshot(item)
            item.start_date, item.end_date = new_start, new_finish
            save_change(context, item, "SHIFT", data, old, signature)
    save_change(context, member, kind, data, before, signature)
    return member
