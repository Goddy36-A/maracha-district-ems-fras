from django import forms
from django.core.exceptions import ValidationError

from .models import Employee


class EmployeeForm(forms.ModelForm):
    """
    Full HR-facing form. Fields like employment_status, department, and
    position are intentionally included here (HR/Admin only) but excluded
    entirely from the separate self-service form employees use for their
    own profile (see EmployeeSelfServiceForm) — enforcing the "employees
    cannot edit their own employment status/department" rule at the form
    layer, in addition to the view-level permission check.
    """

    class Meta:
        model = Employee
        fields = [
            "employee_id", "first_name", "middle_name", "last_name",
            "gender", "date_of_birth", "email", "phone", "address",
            "department", "position", "employment_type", "employment_status",
            "date_joined_org", "supervisor", "profile_photo",
            "emergency_contact_name", "emergency_contact_phone",
        ]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "date_joined_org": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "address": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if "class" not in field.widget.attrs:
                field.widget.attrs["class"] = "form-control"
        # Prevent an employee from being set as their own supervisor
        if self.instance and self.instance.pk:
            self.fields["supervisor"].queryset = Employee.objects.exclude(pk=self.instance.pk)

    def clean(self):
        cleaned = super().clean()
        supervisor = cleaned.get("supervisor")
        if supervisor and self.instance and supervisor.pk == self.instance.pk:
            raise ValidationError("An employee cannot supervise themselves.")
        return cleaned


class EmployeeSelfServiceForm(forms.ModelForm):
    """
    Restricted form for employees editing their own profile. Deliberately
    omits employee_id, department, position, employment_status,
    employment_type, and supervisor per spec Section 27.
    """

    class Meta:
        model = Employee
        fields = ["phone", "address", "emergency_contact_name", "emergency_contact_phone", "profile_photo"]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 2, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if "class" not in field.widget.attrs:
                field.widget.attrs["class"] = "form-control"


class EmployeeSearchForm(forms.Form):
    q = forms.CharField(required=False, label="Search", widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "Name or Employee ID"}))
    department = forms.CharField(required=False, widget=forms.HiddenInput())
    employment_status = forms.CharField(required=False, widget=forms.HiddenInput())
