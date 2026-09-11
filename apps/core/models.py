"""
Core abstract base models shared across the MIU-EMS project.
"""
from django.db import models


class TimeStampedModel(models.Model):
    """Adds created_at / updated_at to any model that inherits it."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Marks a record inactive instead of physically deleting it.
    Used for entities (e.g. Department, Position) where historical
    integrity must be preserved even after deactivation.
    """
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True
