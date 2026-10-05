from django.db import transaction
from rest_framework.exceptions import ValidationError
from modules.audit.services import record_event
from modules.shared.api import find
from .models import Plan, PlanVersion

PLAN_FIELDS = [
    "name",
    "amount",
    "currency",
    "unit",
    "quantity",
    "is_active",
    "is_promotion",
    "available_from",
    "available_until",
]


def current(plan):
    return PlanVersion.objects.get(
        plan=plan, workspace_id=plan.workspace_id, version=plan.version
    )


def plan_data(plan):
    version = current(plan)
    return {
        "id": plan.id,
        "version": plan.version,
        **{field: getattr(version, field) for field in PLAN_FIELDS},
    }


def validate_plan(data):
    if data["unit"] == "MONTHS" and data["quantity"] > 120:
        raise ValidationError({"quantity": "Máximo 120 meses."})
    if (
        data.get("available_from")
        and data.get("available_until")
        and data["available_from"] > data["available_until"]
    ):
        raise ValidationError(
            {"available_until": "La fecha final debe ser posterior al inicio."}
        )


@transaction.atomic
def create_plan(context, data):
    validate_plan(data)
    plan = Plan.objects.create(workspace=context.workspace)
    PlanVersion.objects.create(
        workspace=context.workspace, plan=plan, version=1, **data
    )
    record_event(
        workspace=context.workspace,
        actor=context.actor,
        action="gym.plan.created",
        object_id=plan.id,
        changed_fields=list(data),
    )
    return plan


@transaction.atomic
def revise_plan(context, identifier, data):
    plan = find(
        Plan.objects.select_for_update().filter(workspace=context.workspace), identifier
    )
    if data.get("expected_version") != plan.version:
        raise ValidationError(
            {"expected_version": "El plan cambió. Recarga y revisa sus condiciones."}
        )
    values = {
        key: value for key, value in plan_data(plan).items() if key in PLAN_FIELDS
    }
    values.update({key: value for key, value in data.items() if key in PLAN_FIELDS})
    validate_plan(values)
    plan.version += 1
    plan.save(update_fields=["version"])
    PlanVersion.objects.create(
        workspace=context.workspace, plan=plan, version=plan.version, **values
    )
    record_event(
        workspace=context.workspace,
        actor=context.actor,
        action="gym.plan.revised",
        object_id=plan.id,
        changed_fields=list(data),
    )
    return plan
