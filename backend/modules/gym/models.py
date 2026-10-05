import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class TenantRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey("workspaces.Workspace", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Plan(TenantRecord):
    version = models.PositiveIntegerField(default=1)


class PlanVersion(TenantRecord):
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="versions")
    version = models.PositiveIntegerField()
    name = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    unit = models.CharField(
        max_length=6, choices=[("DAYS", "Días"), ("MONTHS", "Meses")]
    )
    quantity = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    is_promotion = models.BooleanField(default=False)
    available_from = models.DateField(null=True)
    available_until = models.DateField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "version"], name="plan_version_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gte=0), name="plan_amount_nonnegative"
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1), name="plan_quantity_positive"
            ),
        ]


class Membership(TenantRecord):
    client = models.ForeignKey("clients.ClientRecord", on_delete=models.PROTECT)
    plan_version = models.ForeignKey(PlanVersion, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    cancelled_on = models.DateField(null=True)
    request_id = models.UUIDField()
    fingerprint = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "request_id"], name="membership_request_unique"
            ),
            models.CheckConstraint(
                condition=models.Q(end_date__gt=models.F("start_date")),
                name="membership_dates_valid",
            ),
        ]
        indexes = [models.Index(fields=["workspace", "client", "start_date"])]


class MembershipChange(TenantRecord):
    membership = models.ForeignKey(
        Membership, on_delete=models.PROTECT, related_name="changes"
    )
    kind = models.CharField(max_length=16)
    reason = models.CharField(max_length=300)
    before = models.JSONField()
    after = models.JSONField()
    request_id = models.UUIDField()
    fingerprint = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "request_id", "membership"],
                name="membership_change_request_unique",
            )
        ]


class Freeze(TenantRecord):
    membership = models.ForeignKey(
        Membership, on_delete=models.PROTECT, related_name="freezes"
    )
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__gt=models.F("start_date")),
                name="freeze_dates_valid",
            )
        ]


class Attendance(TenantRecord):
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    client = models.ForeignKey("clients.ClientRecord", on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    membership = models.ForeignKey(Membership, null=True, on_delete=models.PROTECT)
    local_date = models.DateField()
    timezone = models.CharField(max_length=64)
    decision = models.CharField(max_length=12)
    service_status = models.CharField(max_length=24)
    reason = models.CharField(max_length=300, blank=True)
    request_id = models.UUIDField()
    fingerprint = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "request_id"], name="attendance_request_unique"
            )
        ]
        indexes = [models.Index(fields=["workspace", "local_date", "client"])]


class AttendanceVoid(TenantRecord):
    attendance = models.OneToOneField(
        Attendance, related_name="void_record", on_delete=models.PROTECT
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reason = models.CharField(max_length=300)
    request_id = models.UUIDField()
    fingerprint = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "request_id"],
                name="attendance_void_request_unique",
            )
        ]
