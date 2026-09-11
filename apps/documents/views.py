from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.audit.utils import log_action
from apps.core.permissions import can_manage_employee, has_role, Roles, role_required

from .forms import EmployeeDocumentForm
from .models import EmployeeDocument


@login_required
@role_required(Roles.ADMIN, Roles.HR)
def document_upload(request):
    if request.method == "POST":
        form = EmployeeDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            log_action(
                actor=request.user, action="DOCUMENT_UPLOADED",
                object_type="EmployeeDocument", object_id=document.pk, request=request,
            )
            messages.success(request, "Document uploaded.")
            return redirect("employees:detail", pk=document.employee_id)
    else:
        form = EmployeeDocumentForm()
    return render(request, "documents/document_form.html", {"form": form})


@login_required
def document_download(request, pk):
    """
    The URL here is intentionally the ONLY way documents are served —
    /media/ is not linked to directly anywhere in templates. Every
    download passes through this authorization check first (spec
    Section 47: documents must never be exposed through predictable
    public URLs without an authorization gate).
    """
    document = get_object_or_404(EmployeeDocument.objects.select_related("employee"), pk=pk)

    authorized = (
        has_role(request.user, Roles.ADMIN, Roles.HR)
        or can_manage_employee(request.user, document.employee)
    )
    if not authorized:
        raise PermissionDenied("You are not authorized to access this document.")

    log_action(
        actor=request.user, action="DOCUMENT_DOWNLOADED",
        object_type="EmployeeDocument", object_id=document.pk, request=request,
    )
    return FileResponse(document.file.open("rb"), as_attachment=True, filename=document.file.name.split("/")[-1])


@login_required
def my_documents(request):
    employee = getattr(request.user, "employee_profile", None)
    if not employee:
        raise PermissionDenied("No employee profile is linked to this account.")
    documents = EmployeeDocument.objects.filter(employee=employee)
    return render(request, "documents/my_documents.html", {"documents": documents})
