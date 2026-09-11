from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.audit.utils import log_action
from apps.core.permissions import Roles, can_manage_employee, has_role, role_required

from .forms import EmployeeForm, EmployeeSearchForm, EmployeeSelfServiceForm
from .models import Employee


@login_required
@role_required(Roles.ADMIN, Roles.HR, Roles.DEPARTMENT_HEAD, Roles.MANAGEMENT)
def employee_list(request):
    """
    HR/Admin see all employees. Department heads see only their own
    department. Management sees a read-only, aggregate-friendly list
    (no confidential fields rendered — enforced in the template).
    """
    qs = Employee.objects.select_related("department", "position").all()

    if has_role(request.user, Roles.DEPARTMENT_HEAD) and not has_role(request.user, Roles.ADMIN, Roles.HR):
        head_employee = getattr(request.user, "employee_profile", None)
        qs = qs.filter(department=head_employee.department) if head_employee else qs.none()

    form = EmployeeSearchForm(request.GET or None)
    if form.is_valid():
        q = form.cleaned_data.get("q")
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(employee_id__icontains=q)
            )
        dept = form.cleaned_data.get("department")
        if dept:
            qs = qs.filter(department_id=dept)
        status = form.cleaned_data.get("employment_status")
        if status:
            qs = qs.filter(employment_status=status)

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "employees/employee_list.html", {
        "page_obj": page_obj,
        "form": form,
        "can_edit": has_role(request.user, Roles.ADMIN, Roles.HR),
    })


@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee.objects.select_related("department", "position", "supervisor"), pk=pk)

    # Server-side authorization — never rely on hiding the link in the UI.
    if not can_manage_employee(request.user, employee) and not has_role(request.user, Roles.MANAGEMENT):
        raise PermissionDenied("You are not authorized to view this employee record.")

    return render(request, "employees/employee_detail.html", {
        "employee": employee,
        "can_edit": can_manage_employee(request.user, employee) and has_role(request.user, Roles.ADMIN, Roles.HR),
    })


@login_required
@role_required(Roles.ADMIN, Roles.HR)
def employee_create(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save()
            log_action(
                actor=request.user, action="EMPLOYEE_CREATED",
                object_type="Employee", object_id=employee.pk, request=request,
            )
            messages.success(request, f"Employee {employee.full_name} created.")
            return redirect("employees:detail", pk=employee.pk)
    else:
        form = EmployeeForm()

    return render(request, "employees/employee_form.html", {"form": form, "mode": "create"})


@login_required
def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    is_self = (lambda p: p is not None and p.pk == employee.pk)(getattr(request.user, "employee_profile", None))
    is_hr_or_admin = has_role(request.user, Roles.ADMIN, Roles.HR)

    if not (is_hr_or_admin or is_self):
        raise PermissionDenied("You are not authorized to edit this employee record.")

    FormClass = EmployeeForm if is_hr_or_admin else EmployeeSelfServiceForm

    if request.method == "POST":
        form = FormClass(request.POST, request.FILES, instance=employee)
        if form.is_valid():
            form.save()
            log_action(
                actor=request.user, action="EMPLOYEE_UPDATED",
                object_type="Employee", object_id=employee.pk, request=request,
                metadata={"self_service": is_self and not is_hr_or_admin},
            )
            messages.success(request, "Employee record updated.")
            return redirect("employees:detail", pk=employee.pk)
    else:
        form = FormClass(instance=employee)

    return render(request, "employees/employee_form.html", {"form": form, "mode": "edit", "employee": employee})


@login_required
@role_required(Roles.ADMIN, Roles.HR)
def employee_deactivate(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        employee.employment_status = "INACTIVE"
        employee.save(update_fields=["employment_status"])
        log_action(
            actor=request.user, action="EMPLOYEE_DEACTIVATED",
            object_type="Employee", object_id=employee.pk, request=request,
        )
        messages.success(request, f"{employee.full_name} has been deactivated.")
        return redirect("employees:detail", pk=employee.pk)
    return render(request, "employees/employee_confirm_deactivate.html", {"employee": employee})
