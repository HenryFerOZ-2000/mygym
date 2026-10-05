import uuid
from django.db import models


class Record(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey("workspaces.Workspace", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Charge(Record):
    client = models.ForeignKey("clients.ClientRecord", on_delete=models.PROTECT)
    source = models.UUIDField()
    label = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "source"], name="charge_source_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gte=0), name="charge_amount_valid"
            ),
        ]


class Payment(Record):
    client = models.ForeignKey("clients.ClientRecord", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    method = models.CharField(
        max_length=8, choices=[("CASH", "Efectivo"), ("TRANSFER", "Transferencia")]
    )
    request_id = models.UUIDField()
    fingerprint = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "request_id"], name="payment_request_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gt=0), name="payment_amount_positive"
            ),
        ]


class Allocation(Record):
    payment = models.ForeignKey(
        Payment, on_delete=models.PROTECT, related_name="allocations"
    )
    charge = models.ForeignKey(
        Charge, on_delete=models.PROTECT, related_name="allocations"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["payment", "charge"], name="allocation_payment_charge_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gt=0), name="allocation_positive"
            ),
        ]


class Refund(Record):
    payment = models.ForeignKey(
        Payment, on_delete=models.PROTECT, related_name="refunds"
    )
    reason = models.CharField(max_length=300)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    request_id = models.UUIDField()
    fingerprint = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "request_id"], name="refund_request_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gt=0), name="refund_positive"
            ),
        ]


class RefundAllocation(Record):
    refund = models.ForeignKey(
        Refund, on_delete=models.PROTECT, related_name="allocations"
    )
    allocation = models.ForeignKey(
        Allocation, on_delete=models.PROTECT, related_name="refunds"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["refund", "allocation"], name="refund_allocation_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gt=0), name="refund_allocation_positive"
            ),
        ]
