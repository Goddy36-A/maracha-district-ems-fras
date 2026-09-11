from django.core.exceptions import PermissionDenied

from .utils import log_action


class AuditLogMiddleware:
    """
    Catches PermissionDenied exceptions raised by role_required / view-level
    authorization checks and records them, so unauthorized-access attempts
    (e.g. an employee hitting /employees/25/edit/) are always traceable —
    independent of whether the view itself remembers to log it.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDenied):
            log_action(
                actor=getattr(request, "user", None),
                action="PERMISSION_DENIED",
                object_type="HTTPRequest",
                object_id=request.path,
                reason=str(exception) or "Permission denied",
                metadata={"method": request.method},
                request=request,
            )
        return None
