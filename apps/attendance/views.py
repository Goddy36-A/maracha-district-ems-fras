import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from apps.audit.utils import log_action
from apps.core.permissions import Roles, can_manage_employee, has_role, role_required
from apps.employees.models import Employee

from .forms import AttendanceFilterForm, AttendanceForm
from .models import Attendance
from .services import attendance_rate


@login_required
@role_required(Roles.ADMIN, Roles.HR, Roles.DEPARTMENT_HEAD)
def attendance_list(request):
    qs = Attendance.objects.select_related("employee", "employee__department")

    if has_role(request.user, Roles.DEPARTMENT_HEAD) and not has_role(request.user, Roles.ADMIN, Roles.HR):
        head_employee = getattr(request.user, "employee_profile", None)
        qs = qs.filter(employee__department=head_employee.department) if head_employee else qs.none()

    form = AttendanceFilterForm(request.GET or None)
    if form.is_valid():
        if form.cleaned_data.get("start_date"):
            qs = qs.filter(date__gte=form.cleaned_data["start_date"])
        if form.cleaned_data.get("end_date"):
            qs = qs.filter(date__lte=form.cleaned_data["end_date"])

    paginator = Paginator(qs, 30)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "attendance/attendance_list.html", {"page_obj": page_obj, "form": form})


@login_required
@role_required(Roles.ADMIN, Roles.HR, Roles.DEPARTMENT_HEAD)
def attendance_create(request):
    if request.method == "POST":
        form = AttendanceForm(request.POST)
        if form.is_valid():
            employee = form.cleaned_data["employee"]
            if has_role(request.user, Roles.DEPARTMENT_HEAD) and not has_role(request.user, Roles.ADMIN, Roles.HR):
                if not can_manage_employee(request.user, employee):
                    raise PermissionDenied("You may only record attendance for your own department.")
            try:
                attendance = form.save(commit=False)
                attendance.recorded_by = request.user
                attendance.save()
            except IntegrityError:
                messages.error(request, "An attendance record for this employee and date already exists.")
            else:
                log_action(
                    actor=request.user, action="ATTENDANCE_CREATED",
                    object_type="Attendance", object_id=attendance.pk, request=request,
                )
                messages.success(request, "Attendance recorded.")
                return redirect("attendance:list")
    else:
        form = AttendanceForm(initial={"date": datetime.date.today()})

    return render(request, "attendance/attendance_form.html", {"form": form})


@login_required
def my_attendance(request):
    employee = getattr(request.user, "employee_profile", None)
    if not employee:
        raise PermissionDenied("No employee profile is linked to this account.")

    records = Attendance.objects.filter(employee=employee).order_by("-date")[:60]

    today = datetime.date.today()
    month_start = today.replace(day=1)
    summary = attendance_rate(employee, month_start, today)

    return render(request, "attendance/my_attendance.html", {"records": records, "summary": summary})
