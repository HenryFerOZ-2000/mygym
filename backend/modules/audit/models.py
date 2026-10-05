from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    workspace = models.ForeignKey("workspaces.Workspace", on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=32)
    object_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)
    changed_fields = models.JSONField(default=list)

    class Meta:
        indexes = [
            models.Index(
                fields=["workspace", "created_at"], name="audit_workspace_date"
            )
        ]
