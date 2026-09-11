from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel


class LeaveType(TimeStampedModel):
    """
    Leave categories are configurable, not hard-coded legal entitlements
    (spec Section 20: "Do not hard-code legal entitlements without
    verifying the applicable policy/law"). default_annual_days is a
    configurable placeholder administrators must confirm against actual
    MIU policy before relying on it.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    default_annual_days = models.PositiveIntegerField(
        default=0,
        help_text="Placeholder entitlement in days/year — verify against actual institutional policy.",
    )
    requires_hr_review = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "leave_type"
        ordering = ["name"]

    def __str__(self):
        return self.name


class LeaveRequest(TimeStampedModel):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("DEPT_APPROVED", "Department Approved"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("CANCELLED", "Cancelled"),
    ]

    employee = models.ForeignKey("employees.Employee", on_delete=models.CASCADE, related_name="leave_requests")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT, related_name="requests")
    start_date = models.DateField()
    end_date = models.DateField()
    number_of_days = models.PositiveIntegerField(editable=False)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="leave_reviews",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comment = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "leave_request"
        ordering = ["-submitted_at"]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["start_date", "end_date"])]

    def __str__(self):
        return f"{self.employee.employee_id} — {self.leave_type} ({self.start_date} to {self.end_date})"

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")

    def save(self, *args, **kwargs):
        self.number_of_days = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)


class LeaveBalance(TimeStampedModel):
    """
    Balances are calculated/updated server-side only — employees have no
    write path to this model anywhere in the app (spec Section 22).
    """
    employee = models.ForeignKey("employees.Employee", on_delete=models.CASCADE, related_name="leave_balances")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name="balances")
    year = models.PositiveIntegerField()
    annual_entitlement = models.PositiveIntegerField(default=0)
    used = models.PositiveIntegerField(default=0)
    pending = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "leave_balance"
        unique_together = ("employee", "leave_type", "year")

    @property
    def remaining(self):
        return max(self.annual_entitlement - self.used - self.pending, 0)

    def __str__(self):
        return f"{self.employee.employee_id} — {self.leave_type} — {self.year}"
