"""
Face Recognition — Models
Stores face descriptors (128-float vectors produced by face-api.js / FaceNet)
per employee. Matching is done server-side using Euclidean distance so no ML
library is required at runtime — only plain Python arithmetic.
"""
import json
import math
from django.conf import settings
from django.db import models
from apps.core.models import TimeStampedModel


MATCH_THRESHOLD = getattr(settings, "FACE_MATCH_THRESHOLD", 0.55)


class FaceProfile(TimeStampedModel):
    """One registered face profile per employee."""
    employee = models.OneToOneField(
        "employees.Employee",
        on_delete=models.CASCADE,
        related_name="face_profile",
    )
    # face-api.js returns a Float32Array(128); we store it as a JSON list
    descriptor = models.JSONField(
        help_text="128-dimensional face embedding produced by FaceNet via face-api.js"
    )
    sample_count = models.PositiveSmallIntegerField(
        default=1,
        help_text="Number of samples averaged into this descriptor",
    )
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="face_registrations",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "face_profile"

    def __str__(self):
        return f"FaceProfile({self.employee.employee_id})"

    @staticmethod
    def euclidean(a, b):
        """Euclidean distance between two equal-length lists of floats."""
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

    @classmethod
    def find_match(cls, descriptor):
        """
        Compare *descriptor* (list[float]) against all active profiles.
        Returns (FaceProfile, distance) for the closest match below
        MATCH_THRESHOLD, or (None, None) if no match.
        """
        best, best_dist = None, float("inf")
        for profile in cls.objects.filter(is_active=True).select_related("employee"):
            dist = cls.euclidean(descriptor, profile.descriptor)
            if dist < best_dist:
                best_dist = dist
                best = profile
        if best and best_dist <= MATCH_THRESHOLD:
            return best, round(best_dist, 4)
        return None, None


class FaceScanLog(TimeStampedModel):
    """Audit trail for every scan attempt — matched or not."""
    RESULT_CHOICES = [
        ("MATCHED",    "Matched — attendance marked"),
        ("NO_MATCH",   "No match found"),
        ("DUPLICATE",  "Already checked in today"),
        ("ERROR",      "Processing error"),
    ]
    employee = models.ForeignKey(
        "employees.Employee",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="face_scan_logs",
    )
    result   = models.CharField(max_length=20, choices=RESULT_CHOICES)
    distance = models.FloatField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    note     = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table  = "face_scan_log"
        ordering  = ["-created_at"]

    def __str__(self):
        emp = self.employee.employee_id if self.employee else "unknown"
        return f"Scan {self.result} — {emp} @ {self.created_at:%Y-%m-%d %H:%M}"
