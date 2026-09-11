"""
Leave workflow: PENDING -> DEPT_APPROVED -> APPROVED / REJECTED, or
CANCELLED at any point before a final decision. Only authorized users may
transition a request (enforced by the calling view, not here — this
module enforces the *state machine*, not who is allowed to call it).
"""
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import LeaveBalance, LeaveRequest


def submit_leave_request(employee, leave_type, start_date, end_date, reason):
    request_obj = LeaveRequest(
        employee=employee, leave_type=leave_type,
        start_date=start_date, end_date=end_date, reason=reason,
        status="PENDING",
    )
    request_obj.full_clean()
    request_obj.save()

    balance, _ = LeaveBalance.objects.get_or_create(
        employee=employee, leave_type=leave_type, year=start_date.year,
        defaults={"annual_entitlement": leave_type.default_annual_days},
    )
    balance.pending += request_obj.number_of_days
    balance.save(update_fields=["pending"])

    return request_obj


def department_approve(leave_request, approver):
    if leave_request.status != "PENDING":
        raise ValidationError("Only pending requests can receive department approval.")
    leave_request.status = "DEPT_APPROVED" if leave_request.leave_type.requires_hr_review else "APPROVED"
    leave_request.reviewed_by = approver
    leave_request.reviewed_at = timezone.now()
    leave_request.save(update_fields=["status", "reviewed_by", "reviewed_at"])
    if leave_request.status == "APPROVED":
        _finalize_balance(leave_request)
    return leave_request


def hr_review(leave_request, reviewer, approve: bool, comment: str = ""):
    if leave_request.status != "DEPT_APPROVED":
        raise ValidationError("HR can only review requests that have department approval.")
    leave_request.status = "APPROVED" if approve else "REJECTED"
    leave_request.reviewed_by = reviewer
    leave_request.reviewed_at = timezone.now()
    leave_request.review_comment = comment
    leave_request.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_comment"])
    if approve:
        _finalize_balance(leave_request)
    else:
        _release_pending_balance(leave_request)
    return leave_request


def reject(leave_request, reviewer, comment: str = ""):
    if leave_request.status not in ("PENDING", "DEPT_APPROVED"):
        raise ValidationError("Only pending or department-approved requests can be rejected.")
    leave_request.status = "REJECTED"
    leave_request.reviewed_by = reviewer
    leave_request.reviewed_at = timezone.now()
    leave_request.review_comment = comment
    leave_request.save(update_fields=["status", "reviewed_by", "reviewed_at", "review_comment"])
    _release_pending_balance(leave_request)
    return leave_request


def cancel(leave_request):
    if leave_request.status in ("APPROVED", "REJECTED", "CANCELLED"):
        raise ValidationError("This request can no longer be cancelled.")
    leave_request.status = "CANCELLED"
    leave_request.save(update_fields=["status"])
    _release_pending_balance(leave_request)
    return leave_request


def _finalize_balance(leave_request):
    try:
        balance = LeaveBalance.objects.get(
            employee=leave_request.employee, leave_type=leave_request.leave_type,
            year=leave_request.start_date.year,
        )
    except LeaveBalance.DoesNotExist:
        return
    balance.pending = max(balance.pending - leave_request.number_of_days, 0)
    balance.used += leave_request.number_of_days
    balance.save(update_fields=["pending", "used"])


def _release_pending_balance(leave_request):
    try:
        balance = LeaveBalance.objects.get(
            employee=leave_request.employee, leave_type=leave_request.leave_type,
            year=leave_request.start_date.year,
        )
    except LeaveBalance.DoesNotExist:
        return
    balance.pending = max(balance.pending - leave_request.number_of_days, 0)
    balance.save(update_fields=["pending"])
