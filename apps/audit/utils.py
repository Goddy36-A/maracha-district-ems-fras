"""
Single entry point for writing audit records so every module logs
consistently and nothing bypasses the immutability rules in AuditLog.
"""
from .models import AuditLog


def log_action(*, actor, action, object_type="", object_id="", reason="", metadata=None, request=None):
    ip = None
    if request is not None:
        ip = request.META.get("REMOTE_ADDR")

    AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        object_type=object_type,
        object_id=str(object_id) if object_id != "" else "",
        reason=reason,
        metadata=metadata or {},
        ip_address=ip,
    )
