from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    Immutable audit trail. Records are created only (no update/delete
    path is exposed anywhere in the application) so history cannot be
    silently altered. Never stores passwords, tokens, or full document
    contents — only identifying metadata.
    """

    ACTION_CHOICES = [
        ("USER_LOGIN", "User Login"),
        ("USER_LOGOUT", "User Logout"),
        ("EMPLOYEE_CREATED", "Employee Created"),
        ("EMPLOYEE_UPDATED", "Employee Updated"),
        ("EMPLOYEE_DEACTIVATED", "Employee Deactivated"),
        ("LEAVE_SUBMITTED", "Leave Submitted"),
        ("LEAVE_APPROVED", "Leave Approved"),
        ("LEAVE_REJECTED", "Leave Rejected"),
        ("ATTENDANCE_CREATED", "Attendance Created"),
        ("ATTENDANCE_UPDATED", "Attendance Updated"),
        ("PERFORMANCE_CREATED", "Performance Record Created"),
        ("PERFORMANCE_FINALIZED", "Performance Finalized"),
        ("DOCUMENT_UPLOADED", "Document Uploaded"),
        ("DOCUMENT_DOWNLOADED", "Document Downloaded"),
        ("REPORT_GENERATED", "Report Generated"),
        ("ROLE_CHANGED", "Role Changed"),
        ("PERMISSION_DENIED", "Permission Denied"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="audit_logs",
    )
    action = models.CharField(max_length=40, choices=ACTION_CHOICES)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_log"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["action", "timestamp"]),
            models.Index(fields=["object_type", "object_id"]),
        ]

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} — {self.action} by {self.actor}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("AuditLog records are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AuditLog records cannot be deleted.")
