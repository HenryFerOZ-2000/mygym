import uuid
from django.conf import settings
from django.db import models


class Workspace(models.Model):
    class Kind(models.TextChoices):
        GYM = "GYM", "Gym"
        COACH = "COACH", "Coach"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.GYM)
    timezone = models.CharField(max_length=64, default="America/Guayaquil")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name", "id"]


class WorkspaceAccess(models.Model):
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        RECEPTION = "RECEPTION", "Reception"
        COACH = "COACH", "Coach"

    workspace = models.ForeignKey(Workspace, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    role = models.CharField(max_length=16, choices=Role.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "user"], name="unique_workspace_access"
            )
        ]


class WorkspaceCapability(models.Model):
    workspace = models.ForeignKey(
        Workspace, on_delete=models.PROTECT, related_name="capabilities"
    )
    code = models.CharField(max_length=64)
    enabled = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "code"], name="unique_workspace_capability"
            )
        ]
