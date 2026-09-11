"""
Centralized Role-Based Access Control (RBAC) helpers.

Design rule (see project spec, "Authorization Rule"): authorization is
NEVER enforced only by hiding UI elements. Every view/endpoint that
touches employee, attendance, leave, performance, or document data must
call one of these helpers (or the equivalent DRF permission class) to
verify access on the server side.
"""
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


class Roles:
    ADMIN = "ADMIN"
    HR = "HR"
    DEPARTMENT_HEAD = "DEPARTMENT_HEAD"
    EMPLOYEE = "EMPLOYEE"
    MANAGEMENT = "MANAGEMENT"

    CHOICES = [
        (ADMIN, "System Administrator"),
        (HR, "Human Resource Administrator"),
        (DEPARTMENT_HEAD, "Department Head"),
        (EMPLOYEE, "Employee"),
        (MANAGEMENT, "Management"),
    ]


def has_role(user, *roles):
    """True if the (authenticated) user's role is one of `roles`."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return getattr(user, "role", None) in roles


def role_required(*roles):
    """
    View decorator: restricts a function-based view to the given roles.
    Superusers always pass. Unauthorized access raises 403 (PermissionDenied)
    rather than silently redirecting, so failed authorization is explicit
    and auditable.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.info(request, "Please log in to continue.")
                return redirect("accounts:login")
            if not has_role(request.user, *roles):
                raise PermissionDenied("You do not have permission to access this resource.")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def can_manage_employee(user, employee):
    """
    Server-side rule for whether `user` may view/edit `employee`'s record.
    - ADMIN / HR: full access.
    - DEPARTMENT_HEAD: only employees within their own department.
    - EMPLOYEE: only their own record (view only — enforced separately for edits).
    - MANAGEMENT: read-only aggregate access only; not individual-record edit access.
    """
    if user.is_superuser or has_role(user, Roles.ADMIN, Roles.HR):
        return True
    if has_role(user, Roles.DEPARTMENT_HEAD):
        head_employee = getattr(user, "employee_profile", None)
        return bool(
            head_employee
            and employee.department_id
            and employee.department_id == head_employee.department_id
        )
    if has_role(user, Roles.EMPLOYEE):
        return (lambda p: p is not None and p.pk == employee.id)(getattr(user, "employee_profile", None))
    return False


def can_view_performance(user, employee):
    """
    Performance data is sensitive (see spec Section 26): employees see
    only their own; department heads only their supervisees; HR/Admin
    broader; Management only aggregated, never here.
    """
    if user.is_superuser or has_role(user, Roles.ADMIN, Roles.HR):
        return True
    if has_role(user, Roles.DEPARTMENT_HEAD):
        head_employee = getattr(user, "employee_profile", None)
        return bool(
            head_employee
            and employee.department_id == head_employee.department_id
        )
    if has_role(user, Roles.EMPLOYEE):
        return (lambda p: p is not None and p.pk == employee.id)(getattr(user, "employee_profile", None))
    return False
