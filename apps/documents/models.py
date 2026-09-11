import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.db import models

from apps.core.models import TimeStampedModel

private_document_storage = FileSystemStorage(location=str(settings.PRIVATE_MEDIA_ROOT))


def document_upload_path(instance, filename):
    """
    Random UUID filename so documents are never exposed through
    predictable/guessable URLs, even if MEDIA storage were misconfigured.
    """
    ext = os.path.splitext(filename)[1]
    return f"employee_documents/{instance.employee_id}/{uuid.uuid4().hex}{ext}"


def validate_document_file(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in settings.ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError(f"Unsupported file type: {ext}")
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if value.size > max_bytes:
        raise ValidationError(f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB limit.")


class EmployeeDocument(TimeStampedModel):
    CATEGORY_CHOICES = [
        ("EMPLOYMENT", "Employment Document"),
        ("IDENTIFICATION", "Identification Document"),
        ("CERTIFICATE", "Certificate"),
        ("CONTRACT", "Contract"),
        ("PERFORMANCE", "Performance Document"),
        ("OTHER", "Other HR Document"),
    ]

    employee = models.ForeignKey("employees.Employee", on_delete=models.CASCADE, related_name="documents")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="OTHER")
    title = models.CharField(max_length=150)
    file = models.FileField(
        upload_to=document_upload_path, validators=[validate_document_file],
        storage=private_document_storage,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="documents_uploaded",
    )

    class Meta:
        db_table = "employee_document"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} — {self.employee.employee_id}"
