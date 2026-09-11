import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.shortcuts import redirect, render

from apps.attendance.models import Attendance
from apps.attendance.services import attendance_rate
from apps.core.permissions import Roles, has_role, role_required
from apps.departments.models import Department
from apps.employees.models import Employee
from apps.leave_management.models import LeaveRequest
from apps.notifications.models import Notification
from apps.performance.models import PerformanceEvaluation

from django.contrib import messages

from .forms import SatisfactionSurveyForm
from .models import EffectivenessIndicator, SatisfactionResponse


@login_required
def home(request):
    """Routes each role to its own dashboard (spec Sections 28-30)."""
    user = request.user
    if user.is_superuser or has_role(user, Roles.ADMIN, Roles.HR):
        return hr_dashboard(request)
    if has_role(user, Roles.MANAGEMENT):
        return management_dashboard(request)
    if has_role(user, Roles.DEPARTMENT_HEAD):
        return department_head_dashboard(request)
    return employee_dashboard(request)


@login_required
@role_required(Roles.ADMIN, Roles.HR)
def hr_dashboard(request):
    today = datetime.date.today()
    context = {
        "total_employees": Employee.objects.count(),
        "active_employees": Employee.objects.filter(employment_status="ACTIVE").count(),
        "on_leave": Employee.objects.filter(employment_status="ON_LEAVE").count(),
        "department_count": Department.objects.filter(is_active=True).count(),
        "pending_leave": LeaveRequest.objects.filter(status__in=["PENDING", "DEPT_APPROVED"]).count(),
        "present_today": Attendance.objects.filter(date=today, status="PRESENT").count(),
        "review_completion": _review_completion_rate(),
    }
    return render(request, "dashboard/hr_dashboard.html", context)


@login_required
@role_required(Roles.MANAGEMENT)
def management_dashboard(request):
    context = {
        "workforce_size": Employee.objects.count(),
        "by_department": Department.objects.filter(is_active=True).annotate(count=Count("employees")),
        "status_distribution": Employee.objects.values("employment_status").annotate(count=Count("id")),
        "avg_performance_score": PerformanceEvaluation.objects.filter(final_score__isnull=False).aggregate(avg=Avg("final_score"))["avg"],
        "review_completion": _review_completion_rate(),
        "leave_pending": LeaveRequest.objects.filter(status__in=["PENDING", "DEPT_APPROVED"]).count(),
    }
    return render(request, "dashboard/management_dashboard.html", context)


@login_required
@role_required(Roles.DEPARTMENT_HEAD)
def department_head_dashboard(request):
    employee = getattr(request.user, "employee_profile", None)
    department = employee.department if employee else None
    context = {"department": department}
    if department:
        context.update({
            "team_size": department.employees.count(),
            "pending_leave": LeaveRequest.objects.filter(
                employee__department=department, status="PENDING",
            ).count(),
        })
    return render(request, "dashboard/department_head_dashboard.html", context)


@login_required
def employee_dashboard(request):
    employee = getattr(request.user, "employee_profile", None)
    context = {"employee": employee}
    if employee:
        today = datetime.date.today()
        todays_attendance = Attendance.objects.filter(employee=employee, date=today).first()
        month_start = today.replace(day=1)
        context.update({
            "todays_attendance": todays_attendance,
            "leave_balances": employee.leave_balances.select_related("leave_type"),
            "pending_leave_count": employee.leave_requests.filter(status__in=["PENDING", "DEPT_APPROVED"]).count(),
            "latest_notification": Notification.objects.filter(recipient=request.user).first(),
            "attendance_summary": attendance_rate(employee, month_start, today),
            "latest_evaluation": employee.performance_evaluations.order_by("-created_at").first(),
        })
    return render(request, "dashboard/employee_dashboard.html", context)


def _review_completion_rate():
    total = PerformanceEvaluation.objects.count()
    if not total:
        return None
    completed = PerformanceEvaluation.objects.filter(stage__in=["FINALIZED", "ACKNOWLEDGED"]).count()
    return round((completed / total) * 100, 2)


@login_required
@role_required(Roles.ADMIN, Roles.HR)
def effectiveness_dashboard(request):
    """
    Spec Sections 33-34: compares BASELINE vs POST_IMPLEMENTATION
    indicators only where both exist. Never fabricates a comparison —
    missing data is shown as "Not yet collected" rather than omitted
    silently or filled in.
    """
    indicators = EffectivenessIndicator.objects.all().order_by("dimension", "indicator_name")

    grouped = {}
    for ind in indicators:
        grouped.setdefault(ind.indicator_name, {"dimension": ind.dimension, "baseline": None, "post": None})
        if ind.period == "BASELINE":
            grouped[ind.indicator_name]["baseline"] = ind
        else:
            grouped[ind.indicator_name]["post"] = ind

    comparisons = []
    for name, data in grouped.items():
        baseline, post = data["baseline"], data["post"]
        improvement_pct = None
        if baseline and post and baseline.value:
            improvement_pct = round(((baseline.value - post.value) / baseline.value) * 100, 2)
        comparisons.append({
            "name": name, "dimension": data["dimension"],
            "baseline": baseline, "post": post, "improvement_pct": improvement_pct,
        })

    satisfaction_responses = SatisfactionResponse.objects.all()
    mean_scores = [r.mean_score for r in satisfaction_responses if r.mean_score is not None]
    overall_satisfaction_mean = round(sum(mean_scores) / len(mean_scores), 2) if mean_scores else None

    return render(request, "dashboard/effectiveness_dashboard.html", {
        "comparisons": comparisons,
        "response_count": satisfaction_responses.count(),
        "overall_satisfaction_mean": overall_satisfaction_mean,
    })


@login_required
def satisfaction_survey(request):
    """Any authenticated user may voluntarily submit the questionnaire."""
    if request.method == "POST":
        form = SatisfactionSurveyForm(request.POST)
        if form.is_valid():
            SatisfactionResponse.objects.create(
                respondent=request.user, answers=form.as_answers_dict(),
            )
            messages.success(request, "Thank you — your feedback has been recorded.")
            return redirect("dashboard:home")
    else:
        form = SatisfactionSurveyForm()
    return render(request, "dashboard/satisfaction_survey.html", {"form": form})
