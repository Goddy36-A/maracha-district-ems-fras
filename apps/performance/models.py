from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel


class PerformanceCycle(TimeStampedModel):
    """
    A review period (e.g. "2026 Mid-Year Review"). Criteria and weights
    are configurable per spec Section 25 — no scale is assumed to match
    MIU's actual policy until confirmed.
    """
    name = models.CharField(max_length=150)
    start_date = models.DateField()
    end_date = models.DateField()
    is_open = models.BooleanField(default=True)

    class Meta:
        db_table = "performance_cycle"
        ordering = ["-start_date"]

    def __str__(self):
        return self.name

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")


class PerformanceCriterion(TimeStampedModel):
    """
    Example criteria only (Quality of Work, Productivity, Teamwork, ...).
    Administrators define their own set; nothing here is hard-coded into
    the workflow logic.
    """
    cycle = models.ForeignKey(PerformanceCycle, on_delete=models.CASCADE, related_name="criteria")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    weight = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.0,
        help_text="Relative weight used in the weighted final score. Weights across a cycle should sum sensibly (validated at cycle level, not enforced to exactly 100 here).",
    )

    class Meta:
        db_table = "performance_criterion"
        unique_together = ("cycle", "name")

    def __str__(self):
        return f"{self.name} ({self.cycle})"


class PerformanceEvaluation(TimeStampedModel):
    """
    One evaluation instance per (employee, cycle). Workflow:
    OPEN -> SELF_ASSESSED -> SUPERVISOR_ASSESSED -> FINALIZED -> ACKNOWLEDGED
    Finalized evaluations cannot be edited (enforced in save()).
    """
    STAGE_CHOICES = [
        ("OPEN", "Open"),
        ("SELF_ASSESSED", "Self-Assessment Submitted"),
        ("SUPERVISOR_ASSESSED", "Supervisor Assessment Submitted"),
        ("FINALIZED", "Finalized"),
        ("ACKNOWLEDGED", "Acknowledged by Employee"),
    ]

    cycle = models.ForeignKey(PerformanceCycle, on_delete=models.CASCADE, related_name="evaluations")
    employee = models.ForeignKey("employees.Employee", on_delete=models.CASCADE, related_name="performance_evaluations")
    evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="evaluations_conducted",
    )
    stage = models.CharField(max_length=25, choices=STAGE_CHOICES, default="OPEN")
    self_assessment_comment = models.TextField(blank=True)
    supervisor_comment = models.TextField(blank=True)
    final_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    employee_acknowledged_at = models.DateTimeField(null=True, blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "performance_evaluation"
        unique_together = ("cycle", "employee")
        indexes = [models.Index(fields=["stage"])]

    def __str__(self):
        return f"{self.employee.employee_id} — {self.cycle}"

    def save(self, *args, **kwargs):
        if self.pk:
            original = PerformanceEvaluation.objects.filter(pk=self.pk).first()
            if original and original.stage == "FINALIZED" and self.stage == "FINALIZED":
                # Allow acknowledgement transition only, block silent edits to finalized content.
                immutable_fields_changed = (
                    original.self_assessment_comment != self.self_assessment_comment
                    or original.supervisor_comment != self.supervisor_comment
                    or original.final_score != self.final_score
                )
                if immutable_fields_changed:
                    raise ValidationError("Finalized evaluations cannot be modified. Use a correction record instead.")
        super().save(*args, **kwargs)


class PerformanceScore(TimeStampedModel):
    evaluation = models.ForeignKey(PerformanceEvaluation, on_delete=models.CASCADE, related_name="scores")
    criterion = models.ForeignKey(PerformanceCriterion, on_delete=models.PROTECT, related_name="scores")
    score = models.PositiveSmallIntegerField(help_text="Raw score on the configured scale (e.g. 1-5).")
    comment = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "performance_score"
        unique_together = ("evaluation", "criterion")

    def __str__(self):
        return f"{self.evaluation} — {self.criterion.name}: {self.score}"
