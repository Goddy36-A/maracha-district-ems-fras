from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from apps.audit.utils import log_action
from apps.core.permissions import Roles, has_role, role_required
from apps.notifications.utils import notify

from . import services
from .forms import LeaveRequestForm, LeaveReviewForm
from .models import LeaveRequest


@login_required
def my_leave(request):
    employee = getattr(request.user, "employee_profile", None)
    if not employee:
        raise PermissionDenied("No employee profile is linked to this account.")

    if request.method == "POST":
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            try:
                leave_request = services.submit_leave_request(
                    employee=employee,
                    leave_type=form.cleaned_data["leave_type"],
                    start_date=form.cleaned_data["start_date"],
                    end_date=form.cleaned_data["end_date"],
                    reason=form.cleaned_data["reason"],
                )
            except ValidationError as exc:
                messages.error(request, "; ".join(exc.messages))
            else:
                log_action(
                    actor=request.user, action="LEAVE_SUBMITTED",
                    object_type="LeaveRequest", object_id=leave_request.pk, request=request,
                )
                if employee.department and employee.department.head:
                    notify(
                        recipient=employee.department.head.user,
                        message=f"{employee.full_name} submitted a leave request pending your approval.",
                    )
                messages.success(request, "Leave request submitted.")
                return redirect("leave:mine")
    else:
        form = LeaveRequestForm()

    requests_qs = LeaveRequest.objects.filter(employee=employee).select_related("leave_type")
    balances = employee.leave_balances.select_related("leave_type").all()

    return render(request, "leave_management/my_leave.html", {
        "form": form, "requests": requests_qs, "balances": balances,
    })


@login_required
def cancel_leave(request, pk):
    employee = getattr(request.user, "employee_profile", None)
    leave_request = get_object_or_404(LeaveRequest, pk=pk)
    if leave_request.employee_id != getattr(employee, "id", None):
        raise PermissionDenied("You may only cancel your own leave requests.")
    try:
        services.cancel(leave_request)
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    else:
        messages.success(request, "Leave request cancelled.")
    return redirect("leave:mine")


@login_required
@role_required(Roles.DEPARTMENT_HEAD, Roles.ADMIN, Roles.HR)
def department_approvals(request):
    employee = getattr(request.user, "employee_profile", None)
    qs = LeaveRequest.objects.filter(status="PENDING").select_related("employee", "leave_type")
    if has_role(request.user, Roles.DEPARTMENT_HEAD) and not has_role(request.user, Roles.ADMIN, Roles.HR):
        qs = qs.filter(employee__department=employee.department) if employee else qs.none()

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "leave_management/department_approvals.html", {"page_obj": page_obj})


@login_required
@role_required(Roles.DEPARTMENT_HEAD, Roles.ADMIN, Roles.HR)
def department_approve_action(request, pk):
    leave_request = get_object_or_404(LeaveRequest, pk=pk)
    head_employee = getattr(request.user, "employee_profile", None)

    if has_role(request.user, Roles.DEPARTMENT_HEAD) and not has_role(request.user, Roles.ADMIN, Roles.HR):
        if not head_employee or leave_request.employee.department_id != head_employee.department_id:
            raise PermissionDenied("You may only approve leave for your own department.")

    try:
        services.department_approve(leave_request, approver=request.user)
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    else:
        log_action(
            actor=request.user, action="LEAVE_APPROVED",
            object_type="LeaveRequest", object_id=leave_request.pk, request=request,
            metadata={"stage": "department"},
        )
        notify(recipient=leave_request.employee.user, message="Your leave request received department approval.")
        messages.success(request, "Leave request approved at department level.")
    return redirect("leave:department_approvals")


@login_required
@role_required(Roles.HR, Roles.ADMIN)
def hr_review_queue(request):
    qs = LeaveRequest.objects.filter(status="DEPT_APPROVED").select_related("employee", "leave_type")
    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "leave_management/hr_review_queue.html", {"page_obj": page_obj, "form": LeaveReviewForm()})


@login_required
@role_required(Roles.HR, Roles.ADMIN)
def hr_review_action(request, pk, decision):
    leave_request = get_object_or_404(LeaveRequest, pk=pk)
    form = LeaveReviewForm(request.POST or None)
    comment = form.data.get("comment", "") if form.is_bound else ""

    try:
        if decision == "approve":
            services.hr_review(leave_request, reviewer=request.user, approve=True, comment=comment)
            action, message = "LEAVE_APPROVED", "Your leave request has been approved."
        else:
            services.hr_review(leave_request, reviewer=request.user, approve=False, comment=comment)
            action, message = "LEAVE_REJECTED", "Your leave request has been rejected."
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    else:
        log_action(
            actor=request.user, action=action, object_type="LeaveRequest",
            object_id=leave_request.pk, request=request, metadata={"stage": "hr"},
        )
        notify(recipient=leave_request.employee.user, message=message)
        messages.success(request, f"Request {decision}d.")
    return redirect("leave:hr_review_queue")
