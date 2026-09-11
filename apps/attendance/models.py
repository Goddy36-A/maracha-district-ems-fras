from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Attendance(TimeStampedModel):
    STATUS_CHOICES = [
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
        ("LATE", "Late"),
        ("ON_LEAVE", "On Leave"),
        ("EXCUSED", "Excused"),
        ("REMOTE", "Remote/Other"),
    ]

    employee = models.ForeignKey("employees.Employee", on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField()
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PRESENT")
    remarks = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="attendance_recorded",
    )

    class Meta:
        db_table = "attendance_record"
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(fields=["employee", "date"], name="unique_attendance_per_employee_per_day"),
        ]
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.employee.employee_id} — {self.date} — {self.status}"
