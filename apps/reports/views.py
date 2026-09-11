import csv

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.http import HttpResponse
from django.shortcuts import render

from apps.attendance.models import Attendance
from apps.audit.utils import log_action
from apps.core.permissions import Roles, has_role, role_required
from apps.departments.models import Department
from apps.employees.models import Employee
from apps.leave_management.models import LeaveRequest
from apps.performance.models import PerformanceEvaluation


@login_required
@role_required(Roles.ADMIN, Roles.HR, Roles.MANAGEMENT)
def report_hub(request):
    return render(request, "reports/report_hub.html")


@login_required
@role_required(Roles.ADMIN, Roles.HR, Roles.MANAGEMENT)
def employees_by_department(request):
    data = (
        Department.objects.filter(is_active=True)
        .annotate(employee_count=Count("employees"))
        .order_by("-employee_count")
    )
    log_action(actor=request.user, action="REPORT_GENERATED", object_type="Report",
               object_id="employees_by_department", request=request)
    return render(request, "reports/employees_by_department.html", {"data": data})


@login_required
@role_required(Roles.ADMIN, Roles.HR, Roles.MANAGEMENT)
def employees_by_status(request):
    data = Employee.objects.values("employment_status").annotate(count=Count("id")).order_by("-count")
    log_action(actor=request.user, action="REPORT_GENERATED", object_type="Report",
               object_id="employees_by_status", request=request)
    return render(request, "reports/employees_by_status.html", {"data": data})


@login_required
@role_required(Roles.ADMIN, Roles.HR, Roles.MANAGEMENT)
def leave_utilization(request):
    data = (
        LeaveRequest.objects.filter(status="APPROVED")
        .values("leave_type__name")
        .annotate(total_days=Count("id"))
        .order_by("-total_days")
    )
    log_action(actor=request.user, action="REPORT_GENERATED", object_type="Report",
               object_id="leave_utilization", request=request)
    return render(request, "reports/leave_utilization.html", {"data": data})


@login_required
@role_required(Roles.ADMIN, Roles.HR, Roles.MANAGEMENT)
def performance_review_completion(request):
    total = PerformanceEvaluation.objects.count()
    completed = PerformanceEvaluation.objects.filter(stage__in=["FINALIZED", "ACKNOWLEDGED"]).count()
    rate = round((completed / total) * 100, 2) if total else None
    avg_score = PerformanceEvaluation.objects.filter(final_score__isnull=False).aggregate(avg=Avg("final_score"))["avg"]

    log_action(actor=request.user, action="REPORT_GENERATED", object_type="Report",
               object_id="performance_review_completion", request=request)
    return render(request, "reports/performance_review_completion.html", {
        "total": total, "completed": completed, "rate": rate, "avg_score": avg_score,
    })


@login_required
@role_required(Roles.ADMIN, Roles.HR)
def employee_list_export_csv(request):
    """CSV export respects the same role restriction as the on-screen report."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="miu_employees.csv"'
    writer = csv.writer(response)
    writer.writerow(["Employee ID", "Full Name", "Department", "Position", "Status", "Date Joined"])
    for emp in Employee.objects.select_related("department", "position"):
        writer.writerow([
            emp.employee_id, emp.full_name,
            emp.department.name if emp.department else "",
            emp.position.title if emp.position else "",
            emp.get_employment_status_display(), emp.date_joined_org,
        ])
    log_action(actor=request.user, action="REPORT_GENERATED", object_type="Report",
               object_id="employee_list_csv", request=request)
    return response
