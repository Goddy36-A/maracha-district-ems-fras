from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel, SoftDeleteModel


class Department(TimeStampedModel, SoftDeleteModel):
    """
    NOTE: No real MIU department names are hard-coded anywhere in this
    app. Departments are created by an Administrator/HR user at runtime,
    or loaded from the clearly-labeled sample fixture in
    apps/departments/fixtures/sample_departments.json for demo purposes.
    """
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    head = models.ForeignKey(
        "employees.Employee", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="headed_department",
    )

    class Meta:
        db_table = "departments_department"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Position(TimeStampedModel, SoftDeleteModel):
    EMPLOYMENT_CATEGORY_CHOICES = [
        ("FULL_TIME", "Full-Time"),
        ("PART_TIME", "Part-Time"),
        ("CONTRACT", "Contract"),
        ("TEMPORARY", "Temporary"),
        ("OTHER", "Other"),
    ]

    title = models.CharField(max_length=150)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="positions")
    job_description = models.TextField(blank=True)
    employment_category = models.CharField(max_length=20, choices=EMPLOYMENT_CATEGORY_CHOICES, default="FULL_TIME")

    class Meta:
        db_table = "departments_position"
        ordering = ["department__name", "title"]
        unique_together = ("title", "department")

    def __str__(self):
        return f"{self.title} — {self.department.name}"
