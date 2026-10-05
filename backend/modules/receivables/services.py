from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from rest_framework.exceptions import ValidationError
from modules.shared.api import find
from modules.shared.operations import lock_client, fingerprint, replay, audit
from .models import Charge, Payment, Allocation, Refund, RefundAllocation

ZERO = Decimal("0.00")


def total(query):
    return query.aggregate(value=Sum("amount"))["value"] or ZERO


def balance(charge):
    return (
        charge.amount
        - total(charge.allocations.all())
        + total(RefundAllocation.objects.filter(allocation__charge=charge))
    )


def create_charge(context, client, source, amount, currency, label):
    charge = Charge.objects.create(
        workspace=context.workspace,
        client=client,
        source=source,
        amount=amount,
        currency=currency,
        label=label,
    )
    audit(
        context, "receivables.charge.created", charge, ["amount", "currency", "source"]
    )
    return charge


def unique_allocations(items):
    if len({item["charge_id"] for item in items}) != len(items):
        raise ValidationError({"allocations": "No repitas un cargo."})


@transaction.atomic
def record_payment(context, client_id, data):
    client = lock_client(context, client_id)
    signature = {**data, "client_id": str(client.id)}
    old = replay(Payment.objects.filter(workspace=context.workspace), signature)
    if old:
        return old
    unique_allocations(data["allocations"])
    if sum(item["amount"] for item in data["allocations"]) != data["amount"]:
        raise ValidationError(
            {"amount": "El importe debe coincidir con las aplicaciones."}
        )
    charges = []
    for item in data["allocations"]:
        charge = find(
            Charge.objects.filter(workspace=context.workspace, client=client),
            item["charge_id"],
        )
        if charge.currency != data["currency"] or item["amount"] > balance(charge):
            raise ValidationError(
                {"allocations": "Moneda diferente o importe superior al saldo."}
            )
        charges.append((charge, item["amount"]))
    payment = Payment.objects.create(
        workspace=context.workspace,
        client=client,
        amount=data["amount"],
        currency=data["currency"],
        method=data["method"],
        request_id=data["request_id"],
        fingerprint=fingerprint(signature),
    )
    for charge, amount in charges:
        Allocation.objects.create(
            workspace=context.workspace, payment=payment, charge=charge, amount=amount
        )
    audit(
        context,
        "receivables.payment.created",
        payment,
        ["amount", "currency", "method", "allocations"],
    )
    return payment


@transaction.atomic
def refund_payment(context, client_id, payment_id, data):
    client = lock_client(context, client_id)
    payment = find(
        Payment.objects.filter(workspace=context.workspace, client=client), payment_id
    )
    signature = {**data, "client_id": str(client.id), "payment_id": str(payment.id)}
    old = replay(Refund.objects.filter(workspace=context.workspace), signature)
    if old:
        return old
    unique_allocations(data["allocations"])
    lines = []
    for item in data["allocations"]:
        allocation = payment.allocations.filter(
            workspace=context.workspace, charge_id=item["charge_id"]
        ).first()
        if allocation is None or item["amount"] > allocation.amount - total(
            allocation.refunds.all()
        ):
            raise ValidationError(
                {"allocations": "Importe superior al disponible para devolver."}
            )
        lines.append((allocation, item["amount"]))
    refund = Refund.objects.create(
        workspace=context.workspace,
        payment=payment,
        reason=data["reason"],
        amount=sum(amount for _, amount in lines),
        request_id=data["request_id"],
        fingerprint=fingerprint(signature),
    )
    for allocation, amount in lines:
        RefundAllocation.objects.create(
            workspace=context.workspace,
            refund=refund,
            allocation=allocation,
            amount=amount,
        )
    audit(
        context,
        "receivables.refund.created",
        refund,
        ["amount", "payment", "allocations", "reason"],
    )
    return refund


def payment_data(payment):
    return {
        "id": payment.id,
        "amount": format(payment.amount, ".2f"),
        "currency": payment.currency,
        "method": payment.method,
        "created_at": payment.created_at,
        "allocations": [
            {
                "charge_id": a.charge_id,
                "amount": format(a.amount, ".2f"),
                "refundable": format(a.amount - total(a.refunds.all()), ".2f"),
            }
            for a in payment.allocations.all()
        ],
        "refunds": [
            {
                "id": r.id,
                "amount": format(r.amount, ".2f"),
                "reason": r.reason,
                "created_at": r.created_at,
            }
            for r in payment.refunds.order_by("created_at", "id")
        ],
    }


def charge_data(charge):
    return {
        "id": charge.id,
        "source": charge.source,
        "label": charge.label,
        "amount": format(charge.amount, ".2f"),
        "balance": format(balance(charge), ".2f"),
        "currency": charge.currency,
        "created_at": charge.created_at,
    }
