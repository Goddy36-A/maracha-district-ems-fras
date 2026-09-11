"""
Face Recognition — Views

Three surfaces:
  /face/kiosk/        — public kiosk terminal (no login) for daily check-in
  /face/register/<id> — register / update a face for one employee (HR/Admin)
  /face/profiles/     — list all employees + face registration status (HR/Admin)

Two JSON API endpoints (called by JavaScript, no HTML response):
  POST /face/api/register/  — stores a face descriptor for an employee
  POST /face/api/verify/    — matches a descriptor, marks attendance, returns result
"""
import json
import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.attendance.models import Attendance
from apps.audit.utils import log_action
from apps.core.permissions import Roles, role_required
from apps.employees.models import Employee

from .models import FaceProfile, FaceScanLog


# ── KIOSK (public — no login required) ───────────────────────────────────────
def kiosk(request):
    """
    Full-screen camera page.  Face-api.js runs entirely in the browser,
    sends the 128-float descriptor to /face/api/verify/ via fetch(), and
    displays the result without a page reload.
    """
    return render(request, "face_recognition/kiosk.html")


# ── PROFILES LIST ─────────────────────────────────────────────────────────────
@login_required
@role_required(Roles.ADMIN, Roles.HR)
def profiles_list(request):
    employees = Employee.objects.filter(
        employment_status="ACTIVE"
    ).select_related("department", "face_profile").order_by("last_name", "first_name")

    return render(request, "face_recognition/profiles.html", {
        "employees": employees,
        "registered_count": sum(1 for e in employees if hasattr(e, "face_profile") and e.face_profile.is_active),
        "total_count": employees.count(),
    })


# ── REGISTER FACE ─────────────────────────────────────────────────────────────
@login_required
@role_required(Roles.ADMIN, Roles.HR)
def register_face(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    existing = getattr(employee, "face_profile", None)
    return render(request, "face_recognition/register.html", {
        "employee": employee,
        "existing": existing,
    })


# ── API: REGISTER DESCRIPTOR ──────────────────────────────────────────────────
@login_required
@role_required(Roles.ADMIN, Roles.HR)
@require_POST
def api_register(request):
    try:
        body       = json.loads(request.body)
        emp_id     = body.get("employee_id")
        descriptor = body.get("descriptor")   # list of 128 floats
        samples    = int(body.get("sample_count", 1))

        if not emp_id or not descriptor or len(descriptor) != 128:
            return JsonResponse({"ok": False, "error": "Invalid payload — need employee_id and 128-float descriptor"}, status=400)

        employee = get_object_or_404(Employee, pk=emp_id)

        profile, created = FaceProfile.objects.update_or_create(
            employee=employee,
            defaults={
                "descriptor":    descriptor,
                "sample_count":  samples,
                "registered_by": request.user,
                "is_active":     True,
            },
        )

        log_action(
            actor=request.user,
            action="FACE_REGISTERED" if created else "FACE_UPDATED",
            object_type="FaceProfile",
            object_id=profile.pk,
            request=request,
            notes=f"Samples: {samples}",
        )

        return JsonResponse({
            "ok": True,
            "created": created,
            "employee_id": employee.employee_id,
            "employee_name": employee.full_name,
        })

    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


# ── API: VERIFY + MARK ATTENDANCE ─────────────────────────────────────────────
@csrf_exempt          # kiosk is a public terminal — CSRF token not available
@require_POST
def api_verify(request):
    ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
    try:
        body       = json.loads(request.body)
        descriptor = body.get("descriptor")

        if not descriptor or len(descriptor) != 128:
            return JsonResponse({"ok": False, "result": "ERROR", "message": "Invalid descriptor"}, status=400)

        profile, distance = FaceProfile.find_match(descriptor)

        if profile is None:
            FaceScanLog.objects.create(result="NO_MATCH", ip_address=ip)
            return JsonResponse({"ok": False, "result": "NO_MATCH", "message": "Face not recognised. Please see the front desk."})

        employee = profile.employee
        today    = datetime.date.today()
        now      = datetime.datetime.now().time()

        # Check for duplicate check-in today
        existing = Attendance.objects.filter(employee=employee, date=today).first()
        if existing:
            if existing.check_out_time is None:
                # Mark check-out
                existing.check_out_time = now
                existing.save(update_fields=["check_out_time"])
                FaceScanLog.objects.create(employee=employee, result="MATCHED", distance=distance, ip_address=ip, note="check-out")
                return JsonResponse({
                    "ok": True, "result": "CHECKOUT",
                    "employee_id": employee.employee_id,
                    "employee_name": employee.full_name,
                    "department": str(employee.department) if employee.department else "",
                    "check_out_time": now.strftime("%H:%M"),
                    "distance": distance,
                    "message": f"Good bye, {employee.first_name}! Check-out recorded at {now.strftime('%H:%M')}.",
                })
            else:
                FaceScanLog.objects.create(employee=employee, result="DUPLICATE", distance=distance, ip_address=ip)
                return JsonResponse({
                    "ok": False, "result": "DUPLICATE",
                    "employee_name": employee.full_name,
                    "message": f"{employee.first_name} has already checked in and out today.",
                })

        # Determine status based on shift (if assigned)
        status = "PRESENT"
        shift  = getattr(employee, "shift", None)
        if shift and hasattr(shift, "start_time"):
            grace  = datetime.timedelta(minutes=getattr(shift, "grace_minutes", 15))
            latest = (datetime.datetime.combine(today, shift.start_time) + grace).time()
            if now > latest:
                status = "LATE"

        attendance = Attendance.objects.create(
            employee=employee,
            date=today,
            check_in_time=now,
            status=status,
        )

        FaceScanLog.objects.create(employee=employee, result="MATCHED", distance=distance, ip_address=ip, note="check-in")

        return JsonResponse({
            "ok": True, "result": "MATCHED",
            "employee_id":   employee.employee_id,
            "employee_name": employee.full_name,
            "department":    str(employee.department) if employee.department else "",
            "status":        status,
            "check_in_time": now.strftime("%H:%M"),
            "distance":      distance,
            "message":       f"Welcome, {employee.first_name}! Check-in recorded at {now.strftime('%H:%M')} — {status}.",
        })

    except Exception as e:
        FaceScanLog.objects.create(result="ERROR", ip_address=ip, note=str(e)[:200])
        return JsonResponse({"ok": False, "result": "ERROR", "message": "Server error. Please try again."}, status=500)


# ── SCAN LOGS (HR/Admin) ──────────────────────────────────────────────────────
@login_required
@role_required(Roles.ADMIN, Roles.HR)
def scan_logs(request):
    from django.core.paginator import Paginator
    logs = FaceScanLog.objects.select_related("employee", "employee__department").order_by("-created_at")
    paginator = Paginator(logs, 40)
    page_obj  = paginator.get_page(request.GET.get("page"))
    return render(request, "face_recognition/scan_logs.html", {"page_obj": page_obj})


# ── DELETE / DEACTIVATE FACE ──────────────────────────────────────────────────
@login_required
@role_required(Roles.ADMIN, Roles.HR)
def delete_face(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    profile  = get_object_or_404(FaceProfile, employee=employee)
    if request.method == "POST":
        profile.is_active = False
        profile.save(update_fields=["is_active"])
        log_action(actor=request.user, action="FACE_DEACTIVATED", object_type="FaceProfile", object_id=profile.pk, request=request)
        messages.success(request, f"Face profile for {employee.full_name} has been deactivated.")
        return redirect("face:profiles")
    return render(request, "face_recognition/confirm_delete.html", {"employee": employee})
