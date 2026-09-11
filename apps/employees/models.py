from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from apps.core.models import TimeStampedModel

phone_validator = RegexValidator(
    regex=r"^\+?[0-9\s\-()]{7,20}$",
    message="Enter a valid phone number.",
)


def employee_photo_path(instance, filename):
    return f"employee_photos/{instance.employee_id}/{filename}"


class Employee(TimeStampedModel):
    """
    Central employee profile. Sensitive/optional fields (date of birth,
    gender, emergency contact) are deliberately nullable — collect them
    only where institutionally required, per the "do not collect sensitive
    personal information unnecessarily" rule in the spec.
    """

    EMPLOYMENT_STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("ON_LEAVE", "On Leave"),
        ("SUSPENDED", "Suspended"),
        ("RESIGNED", "Resigned"),
        ("RETIRED", "Retired"),
        ("TERMINATED", "Terminated"),
        ("INACTIVE", "Inactive"),
    ]

    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
        ("O", "Other"),
        ("N", "Prefer not to say"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="employee_profile",
        null=True, blank=True,
        help_text="Linked login account, if this employee has portal access.",
    )

    employee_id = models.CharField(max_length=20, unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)

    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, validators=[phone_validator], blank=True)
    address = models.TextField(blank=True)

    department = models.ForeignKey(
        "departments.Department", on_delete=models.PROTECT, related_name="employees",
        null=True, blank=True,
    )
    position = models.ForeignKey(
        "departments.Position", on_delete=models.PROTECT, related_name="employees",
        null=True, blank=True,
    )
    employment_type = models.CharField(
        max_length=20,
        choices=[
            ("FULL_TIME", "Full-Time"), ("PART_TIME", "Part-Time"),
            ("CONTRACT", "Contract"), ("TEMPORARY", "Temporary"), ("OTHER", "Other"),
        ],
        default="FULL_TIME",
    )
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, default="ACTIVE")
    date_joined_org = models.DateField(help_text="Date the employee joined Maracha DLG (distinct from portal account creation).")

    supervisor = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="supervisees",
    )

    profile_photo = models.ImageField(upload_to=employee_photo_path, null=True, blank=True)

    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, validators=[phone_validator], blank=True)

    class Meta:
        db_table = "employees_employee"
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["employee_id"]),
            models.Index(fields=["email"]),
            models.Index(fields=["employment_status"]),
            models.Index(fields=["department"]),
        ]

    def __str__(self):
        return f"{self.employee_id} — {self.full_name}"

    @property
    def full_name(self):
        parts = [self.first_name, self.middle_name, self.last_name]
        return " ".join(p for p in parts if p)

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.supervisor_id and self.supervisor_id == self.id:
            raise ValidationError("An employee cannot supervise themselves.")
