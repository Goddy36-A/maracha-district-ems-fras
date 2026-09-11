from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class EffectivenessIndicator(TimeStampedModel):
    """
    Stores a single measured value for a named indicator at a point in
    time, tagged as BASELINE or POST_IMPLEMENTATION. Nothing here is
    auto-populated with invented numbers — values are entered by an
    authorized administrator/researcher, or computed from real
    application data (e.g. attendance rate) and clearly sourced.
    """
    PERIOD_CHOICES = [
        ("BASELINE", "Baseline (Pre-Implementation)"),
        ("POST_IMPLEMENTATION", "Post-Implementation"),
    ]

    DIMENSION_CHOICES = [
        ("EFFICIENCY", "Efficiency"),
        ("ACCURACY", "Accuracy"),
        ("ACCESSIBILITY", "Accessibility"),
        ("USABILITY", "Usability / Satisfaction"),
        ("HR_EFFECTIVENESS", "HR Effectiveness"),
        ("ATTENDANCE", "Attendance"),
        ("PERFORMANCE_MGMT", "Performance Management"),
        ("REPORTING", "Reporting"),
    ]

    dimension = models.CharField(max_length=25, choices=DIMENSION_CHOICES)
    indicator_name = models.CharField(max_length=150)
    period = models.CharField(max_length=25, choices=PERIOD_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=30, help_text="e.g. 'days', '%', 'count'")
    measured_on = models.DateField()
    source_note = models.CharField(
        max_length=255,
        help_text="Where this number came from (e.g. 'HR manual log, n=42' or 'system-calculated from Attendance model'). Required for academic honesty — never leave blank with a fabricated figure.",
    )
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "effectiveness_indicator"
        ordering = ["dimension", "indicator_name", "period"]

    def __str__(self):
        return f"{self.indicator_name} ({self.period}): {self.value}{self.unit}"


class SatisfactionResponse(TimeStampedModel):
    """
    One respondent's answers to the configurable Likert questionnaire
    (spec Section 56). Questions are stored as a JSON mapping so the
    question set itself remains configurable rather than hard-coded
    into the schema.
    """
    respondent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    answers = models.JSONField(
        help_text='e.g. {"ease_of_use": 4, "usefulness": 5, "reliability": 4, "overall_satisfaction": 5}'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "satisfaction_response"

    def __str__(self):
        return f"Response #{self.pk} — {self.submitted_at:%Y-%m-%d}"

    @property
    def mean_score(self):
        values = [v for v in self.answers.values() if isinstance(v, (int, float))]
        return round(sum(values) / len(values), 2) if values else None
