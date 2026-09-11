from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from apps.audit.utils import log_action
from apps.core.permissions import Roles, can_view_performance, has_role, role_required
from apps.notifications.utils import notify

from .forms import PerformanceScoreForm, SelfAssessmentForm, SupervisorAssessmentForm
from .models import PerformanceCriterion, PerformanceEvaluation, PerformanceScore
from .services import calculate_final_score, finalize_evaluation


@login_required
def my_evaluations(request):
    employee = getattr(request.user, "employee_profile", None)
    if not employee:
        raise PermissionDenied("No employee profile is linked to this account.")
    evaluations = PerformanceEvaluation.objects.filter(employee=employee).select_related("cycle")
    return render(request, "performance/my_evaluations.html", {"evaluations": evaluations})


@login_required
def evaluation_detail(request, pk):
    evaluation = get_object_or_404(PerformanceEvaluation.objects.select_related("employee", "cycle"), pk=pk)

    # Server-side privacy enforcement — spec Section 26.
    if not can_view_performance(request.user, evaluation.employee):
        raise PermissionDenied("You are not authorized to view this performance evaluation.")

    scores = evaluation.scores.select_related("criterion")
    is_owner = (lambda p: p is not None and p.pk == evaluation.employee_id)(getattr(request.user, "employee_profile", None))
    is_supervisor_or_hr = has_role(request.user, Roles.ADMIN, Roles.HR, Roles.DEPARTMENT_HEAD)

    return render(request, "performance/evaluation_detail.html", {
        "evaluation": evaluation,
        "scores": scores,
        "can_self_assess": is_owner and evaluation.stage == "OPEN",
        "can_supervisor_assess": is_supervisor_or_hr and evaluation.stage == "SELF_ASSESSED",
        "can_finalize": is_supervisor_or_hr and evaluation.stage == "SUPERVISOR_ASSESSED",
        "can_acknowledge": is_owner and evaluation.stage == "FINALIZED",
    })


@login_required
def submit_self_assessment(request, pk):
    evaluation = get_object_or_404(PerformanceEvaluation, pk=pk)
    is_owner = (lambda p: p is not None and p.pk == evaluation.employee_id)(getattr(request.user, "employee_profile", None))
    if not is_owner:
        raise PermissionDenied("You may only complete your own self-assessment.")
    if evaluation.stage != "OPEN":
        messages.error(request, "This evaluation is no longer open for self-assessment.")
        return redirect("performance:detail", pk=pk)

    if request.method == "POST":
        form = SelfAssessmentForm(request.POST, instance=evaluation)
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.stage = "SELF_ASSESSED"
            evaluation.save()
            messages.success(request, "Self-assessment submitted.")
            return redirect("performance:detail", pk=pk)
    else:
        form = SelfAssessmentForm(instance=evaluation)

    return render(request, "performance/self_assessment_form.html", {"form": form, "evaluation": evaluation})


@login_required
@role_required(Roles.ADMIN, Roles.HR, Roles.DEPARTMENT_HEAD)
def submit_supervisor_assessment(request, pk):
    evaluation = get_object_or_404(PerformanceEvaluation, pk=pk)
    if not can_view_performance(request.user, evaluation.employee):
        raise PermissionDenied("You are not authorized to evaluate this employee.")
    if evaluation.stage != "SELF_ASSESSED":
        messages.error(request, "This evaluation is not ready for supervisor assessment.")
        return redirect("performance:detail", pk=pk)

    criteria = evaluation.cycle.criteria.all()
    if request.method == "POST":
        comment_form = SupervisorAssessmentForm(request.POST, instance=evaluation)
        valid = comment_form.is_valid()
        score_errors = []
        scores_to_save = []
        for criterion in criteria:
            raw = request.POST.get(f"score_{criterion.id}")
            try:
                score_val = int(raw)
            except (TypeError, ValueError):
                score_errors.append(criterion.name)
                continue
            scores_to_save.append((criterion, score_val))

        if valid and not score_errors:
            evaluation = comment_form.save(commit=False)
            evaluation.stage = "SUPERVISOR_ASSESSED"
            evaluation.evaluator = request.user
            evaluation.save()
            for criterion, score_val in scores_to_save:
                PerformanceScore.objects.update_or_create(
                    evaluation=evaluation, criterion=criterion, defaults={"score": score_val},
                )
            messages.success(request, "Supervisor assessment submitted.")
            return redirect("performance:detail", pk=pk)
        else:
            messages.error(request, "Please provide a valid score for every criterion.")
    else:
        comment_form = SupervisorAssessmentForm(instance=evaluation)

    return render(request, "performance/supervisor_assessment_form.html", {
        "comment_form": comment_form, "evaluation": evaluation, "criteria": criteria,
    })


@login_required
@role_required(Roles.ADMIN, Roles.HR, Roles.DEPARTMENT_HEAD)
def finalize(request, pk):
    evaluation = get_object_or_404(PerformanceEvaluation, pk=pk)
    if not can_view_performance(request.user, evaluation.employee):
        raise PermissionDenied("You are not authorized to finalize this evaluation.")
    if request.method == "POST":
        try:
            finalize_evaluation(evaluation)
        except ValueError as exc:
            messages.error(request, str(exc))
        else:
            log_action(
                actor=request.user, action="PERFORMANCE_FINALIZED",
                object_type="PerformanceEvaluation", object_id=evaluation.pk, request=request,
            )
            notify(recipient=evaluation.employee.user, message="Your performance evaluation has been finalized.")
            messages.success(request, "Evaluation finalized.")
    return redirect("performance:detail", pk=pk)


@login_required
def acknowledge(request, pk):
    evaluation = get_object_or_404(PerformanceEvaluation, pk=pk)
    is_owner = (lambda p: p is not None and p.pk == evaluation.employee_id)(getattr(request.user, "employee_profile", None))
    if not is_owner:
        raise PermissionDenied("You may only acknowledge your own evaluation.")
    if request.method == "POST" and evaluation.stage == "FINALIZED":
        from django.utils import timezone
        evaluation.stage = "ACKNOWLEDGED"
        evaluation.employee_acknowledged_at = timezone.now()
        evaluation.save(update_fields=["stage", "employee_acknowledged_at"])
        messages.success(request, "Evaluation acknowledged.")
    return redirect("performance:detail", pk=pk)
